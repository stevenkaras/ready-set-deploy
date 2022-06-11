from collections.abc import Iterable, MutableMapping
from typing import Generic, Iterator, Optional, TypeVar, cast, Union
import difflib
from enum import Enum

Primitive = Union[str, list, dict]


class Element:
    """
    Elements are the basic building blocks of system configuration state.
    """


_CF = TypeVar("_CF", bound="FullElement")
_CD = TypeVar("_CD", bound="DiffElement")


class FullElement(Element, Generic[_CD]):
    """
    Full elements represent a desired configuration state.

    Full elements are expected to be mutable, and should allow access to their members through well-known APIs
    """

    def diff(self: _CF, other: _CF) -> _CD:
        """
        Produce a DiffElement that when applied to self would produce other.
        """
        raise NotImplementedError("diff")

    def apply(self: _CF, other: _CD) -> _CF:
        """
        Apply the changes from other to produce a new FullElement.

        Assuming the diff element was produced from this element, this should return the original "other".
        """
        raise NotImplementedError("apply")

    @classmethod
    def zero(cls: type[_CF]) -> _CF:
        """
        Generate a zero-element of the given type
        """
        raise NotImplementedError("zero")

    @classmethod
    def diff_type(cls) -> type[_CD]:
        """
        Return the full type associated with this diff type
        """
        raise NotImplementedError("diff_type")

    def copy(self: _CF) -> _CF:
        """
        Return a deep copy of this element
        """
        raise NotImplementedError("copy")

    def to_primitive(self) -> Primitive:
        """
        Serialize this element into a primitive python value
        """
        raise NotImplementedError("to_primitive")

    @classmethod
    def from_primitive(cls, primitive: Primitive) -> "FullElement":
        """
        Construct this element from a primitive Python value
        """
        if isinstance(primitive, str):
            return Atom._from_primitive(primitive)
        elif isinstance(primitive, list):
            first_element = primitive[0]
            if first_element == "list":
                return List._from_primitive(primitive[1:])
            elif first_element == "set":
                return Set._from_primitive(primitive[1:])
            else:
                raise ValueError(f"Expected either a tagged list or set. Got {first_element}")
        elif isinstance(primitive, dict):
            return Map._from_primitive(primitive)
        else:
            raise TypeError(f"Expected a primitive, got {type(primitive)}")


class DiffElement(Element, Generic[_CF]):
    """
    Diff elements are an efficient representation of the difference between two FullElements.

    Diff elements are expected to be immutable, but allow direct access to their members
    """

    @classmethod
    def full_type(cls) -> type[_CF]:
        """
        Return the diff type associated with this full type
        """
        raise NotImplementedError("full_type")

    def copy(self: _CD) -> _CD:
        """
        Return a deep copy of this element
        """
        raise NotImplementedError("copy")

    def to_primitive(self) -> Primitive:
        """
        Serialize this element into a primitive python value
        """
        raise NotImplementedError("to_primitive")

    @classmethod
    def from_primitive(cls, primitive: Primitive) -> "DiffElement":
        """
        Construct this element from a primitive Python value
        """
        if isinstance(primitive, str):
            return AtomDiff._from_primitive(primitive)
        elif isinstance(primitive, dict):
            type_tag = primitive["diff_type"]
            if type_tag == "set":
                return SetDiff._from_primitive(primitive)
            elif type_tag == "map":
                return MapDiff._from_primitive(primitive)
            else:
                raise ValueError(f"Expected either a tagged set or map. Got {type_tag}")
        elif isinstance(primitive, list):
            return ListDiff._from_primitive(primitive)
        else:
            raise TypeError(f"Expected a primitive, got {type(primitive)}")


_F = TypeVar("_F", bound=FullElement)
_D = TypeVar("_D", bound=DiffElement)


class Atom(FullElement["AtomDiff"]):
    """
    Represents an atomically replaceable element (a string).
    """

    def __init__(self, value: str) -> None:
        self.value = value

    def copy(self) -> "Atom":
        return self.__class__(value=self.value)

    def to_primitive(self) -> Primitive:
        return self.value

    @classmethod
    def _from_primitive(cls, primitive: Primitive) -> "Atom":
        primitive = cast(str, primitive)
        return cls(value=primitive)

    @classmethod
    def zero(cls) -> "Atom":
        return cls(value="")

    @classmethod
    def diff_type(cls) -> type["AtomDiff"]:
        return AtomDiff

    def diff(self, other: "Atom") -> "AtomDiff":
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self)} are only diffable against other {type(self)}. Got {type(other)}")
        diff_type = cast(type[AtomDiff], self.diff_type())
        return diff_type(value=other.value)

    def apply(self, other: DiffElement) -> "Atom":
        if not isinstance(other, self.diff_type()):
            raise TypeError(f"{type(self)}s can only be applied with Atom. Got {type(other)}")
        other = cast(AtomDiff, other)
        return self.__class__(value=other.value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Atom):
            return __o.value == self.value
        else:
            raise TypeError("Atoms are only comparable to other atoms")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.value}")'


class AtomDiff(DiffElement["Atom"]):
    def __init__(self, value: str) -> None:
        self.value = value

    def copy(self) -> "AtomDiff":
        return self.__class__(value=self.value)

    def to_primitive(self) -> Primitive:
        return self.value

    @classmethod
    def _from_primitive(cls, primitive: Primitive) -> "AtomDiff":
        primitive = cast(str, primitive)
        return cls(value=primitive)

    @classmethod
    def full_type(cls) -> type[Atom]:
        return Atom

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, AtomDiff):
            return __o.value == self.value
        else:
            raise TypeError("AtomDiffs are only comparable to other atom diffs")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.value}")'


class Set(FullElement["SetDiff[_F]"], Generic[_F]):
    """
    A set is an element representing an unordered collection of Atoms
    """

    def __init__(self, items: set[_F]) -> None:
        self._items = items

    def copy(self) -> "Set[_F]":
        return self.__class__(items=set(self._items))

    def to_primitive(self) -> Primitive:
        return ["set", *(item.to_primitive() for item in self._items)]

    @classmethod
    def _from_primitive(cls, primitive: Primitive) -> "Set[_F]":
        primitive = cast(list[str], primitive)
        items = set([FullElement.from_primitive(item) for item in primitive])
        return cls(items=cast(set[_F], items))

    @classmethod
    def zero(cls) -> "Set[_F]":
        return cls(items=set())

    @classmethod
    def diff_type(cls) -> type["SetDiff[_F]"]:
        return SetDiff

    def diff(self, other: "Set[_F]") -> "SetDiff[_F]":
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self)} are only diffable against other {type(self)}. Got {type(other)}")
        diff_type = self.diff_type()

        to_add = set(item for item in other._items - self._items)
        to_remove = set(item for item in self._items - other._items)

        return diff_type(to_add=to_add, to_remove=to_remove)

    def apply(self, other: "SetDiff[_F]") -> "Set[_F]":
        if not isinstance(other, self.diff_type()):
            raise TypeError(f"{type(self)}s can only be applied with SetDiff. Got {type(other)}")
        # other = cast(SetDiff, other)

        items = set(self._items)
        items |= other.to_add
        items -= other.to_remove

        return self.__class__(items=items)

    def add(self, value: _F) -> "Set[_F]":
        """
        Add the given value to this set
        """
        self._items.add(value)
        return self

    def remove(self, value: _F) -> "Set[_F]":
        """
        Remove the given value from this set if present
        """
        self._items.discard(value)
        return self

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[_F]:
        return iter(self._items)

    def __contains__(self, item) -> bool:
        return item in self._items

    def __hash__(self) -> int:
        h = 0
        for item in self._items:
            h ^= hash(item)
        return h

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Set):
            return __o._items == self._items
        else:
            raise TypeError("Sets are only comparable to other set")

    def __str__(self) -> str:
        return str(self._items)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._items!r})"


class SetDiff(DiffElement["Set[_F]"], Generic[_F]):
    def __init__(self, to_add: set[_F], to_remove: set[_F]) -> None:
        self.to_add = to_add
        self.to_remove = to_remove

    def copy(self):
        return self.__class__(to_add=self.to_add, to_remove=self.to_remove)

    def to_primitive(self) -> Primitive:
        return {
            "diff_type": "set",
            "to_add": [atom.to_primitive() for atom in self.to_add],
            "to_remove": [atom.to_primitive() for atom in self.to_remove],
        }

    @classmethod
    def _from_primitive(cls, primitive: Primitive) -> "SetDiff":
        primitive = cast(dict[str, list[str]], primitive)
        to_add = cast(set[_F], set(FullElement.from_primitive(atom) for atom in primitive["to_add"]))
        to_remove = cast(set[_F], set(FullElement.from_primitive(atom) for atom in primitive["to_remove"]))
        return cls(to_add=to_add, to_remove=to_remove)

    @classmethod
    def full_type(cls) -> type["Set"]:
        return Set

    def __hash__(self) -> int:
        h = 0
        for item in self.to_add:
            h ^= hash(item)
        for item in self.to_remove:
            h ^= -hash(item)

        return h

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, SetDiff):
            return __o.to_add == self.to_add and __o.to_remove == self.to_remove
        else:
            raise TypeError(f"SetDiffs are only comparable to other set diffs, not {type(__o)}")

    def __str__(self) -> str:
        return f"(+{self.to_add} -{self.to_remove})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(to_add={self.to_add}, to_remove={self.to_remove})"


class Map(FullElement["MapDiff"], Generic[_F, _D]):
    def __init__(self, map: MutableMapping[Atom, _F]) -> None:
        self._map = map

    def copy(self) -> "Map":
        return self.__class__(map={key: value.copy() for key, value in self._map.items()})

    def to_primitive(self) -> Primitive:
        return {key.to_primitive(): value.to_primitive() for key, value in self._map.items()}

    @classmethod
    def _from_primitive(cls, primitive: Primitive) -> "Map":
        primitive = cast(dict[Primitive, Primitive], primitive)
        element_map: MutableMapping[Atom, _F] = {}
        for raw_key, raw_value in primitive.items():
            # NOTE: If the input is malformed, we might get an element that is not a _F - this is an error
            element_map[cast(Atom, FullElement.from_primitive(raw_key))] = cast(_F, FullElement.from_primitive(raw_value))

        return cls(map=element_map)

    @classmethod
    def zero(cls) -> "Map":
        return cls(map={})

    @classmethod
    def diff_type(cls) -> type["MapDiff"]:
        return MapDiff

    def diff(self, other: "Map") -> "MapDiff":
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self)} are only diffable against other {type(self)}. Got {type(other)}")
        keys_to_remove = set(self._map.keys()) - set(other._map.keys())
        raw_items_to_add = set((key, value.copy()) for key, value in other._map.items() if key not in self._map)
        items_to_add = cast(set[tuple[Atom, _F]], raw_items_to_add)
        raw_items_to_set = set((key, self._map[key].diff(value)) for key, value in other._map.items() if key in self._map and self._map[key] != value)
        items_to_set = cast(set[tuple[Atom, _D]], raw_items_to_set)
        diff_type = cast(type[MapDiff[_F, _D]], self.diff_type())
        return diff_type(keys_to_remove=keys_to_remove, items_to_add=items_to_add, items_to_set=items_to_set)

    def apply(self, other: "MapDiff") -> "Map":
        if not isinstance(other, self.diff_type()):
            raise TypeError(f"{type(self)}s can only be applied with {self.diff_type}. Got {type(other)}")
        other = cast(MapDiff[_F, _D], other)
        new_map = dict(self._map)
        for key in other.keys_to_remove:
            del new_map[key]

        for key, to_set in other.items_to_set:
            new_map[key] = cast(_F, self._map[key].apply(to_set))

        for key, to_add in other.items_to_add:
            new_map[key] = to_add

        return self.__class__(map=new_map)

    def __getitem__(self, key: Atom) -> _F:
        return self._map[key]

    def __setitem__(self, key: Atom, value: _F) -> None:
        self._map[key] = value

    def __delitem__(self, key: Atom) -> None:
        del self._map[key]

    def __len__(self) -> int:
        return len(self._map)

    def __iter__(self) -> Iterator[Atom]:
        return iter(self._map)

    def __contains__(self, key: Atom) -> bool:
        return key in self._map

    def keys(self) -> Iterable[Atom]:
        return self._map.keys()

    def values(self) -> Iterable[_F]:
        return self._map.values()

    def items(self) -> Iterable[tuple[Atom, _F]]:
        return self._map.items()

    def get(self, key: Atom, default: Optional[_F] = None) -> Optional[_F]:
        return self._map.get(key, default)

    def pop(self, key: Atom, default: Optional[_F] = None) -> Optional[_F]:
        return self._map.pop(key, default)

    def __hash__(self) -> int:
        h = 0
        for key, value in self._map.items():
            h ^= hash((key, hash(value)))
        return h

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Map):
            return __o._map == self._map
        else:
            raise TypeError(f"{type(self)} are only comparable to other {type(self)}")

    def __str__(self) -> str:
        return str(self._map)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._map!r})"


class MapDiff(DiffElement[Map], Generic[_F, _D]):
    def __init__(self, keys_to_remove: set[Atom], items_to_add: set[tuple[Atom, _F]], items_to_set: set[tuple[Atom, _D]]) -> None:
        self.keys_to_remove = keys_to_remove
        self.items_to_set = items_to_set
        self.items_to_add = items_to_add

    def copy(self) -> "MapDiff":
        return self.__class__(
            keys_to_remove=self.keys_to_remove,
            items_to_add=self.items_to_add,
            items_to_set=self.items_to_set,
        )

    def to_primitive(self) -> Primitive:
        return {
            "diff_type": "map",
            "keys_to_remove": list(sorted(cast(str, atom.to_primitive()) for atom in self.keys_to_remove)),
            "items_to_set": list(sorted([key.to_primitive(), value.to_primitive()] for key, value in self.items_to_set)),
            "items_to_add": list(sorted([key.to_primitive(), value.to_primitive()] for key, value in self.items_to_add)),
        }

    @classmethod
    def _from_primitive(cls, primitive: Primitive) -> "MapDiff":
        primitive = cast(dict[str, Primitive], primitive)

        keys_to_remove = set(Atom._from_primitive(atom) for atom in primitive["keys_to_remove"])
        items_to_add = set((Atom._from_primitive(entry[0]), FullElement.from_primitive(entry[1])) for entry in primitive["items_to_add"])
        items_to_set = set((Atom._from_primitive(entry[0]), DiffElement.from_primitive(entry[1])) for entry in primitive["items_to_set"])

        return cls(
            keys_to_remove=cast(set[Atom], keys_to_remove),
            items_to_add=cast(set[tuple[Atom, _F]], items_to_add),
            items_to_set=cast(set[tuple[Atom, _D]], items_to_set),
        )

    @classmethod
    def full_type(cls) -> type["Map"]:
        return Map

    def __hash__(self) -> int:
        h = 0
        for key in self.keys_to_remove:
            h ^= hash(key)
        for item_to_add in self.items_to_add:
            h ^= hash(item_to_add)
        for item_to_set in self.items_to_set:
            h ^= hash(item_to_set)

        return h

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, MapDiff):
            return __o.keys_to_remove == self.keys_to_remove and __o.items_to_set == self.items_to_set and __o.items_to_add == self.items_to_add
        else:
            raise TypeError(f"{type(self)} are only comparable to other {type(self)}")

    def __str__(self) -> str:
        return f"(+{self.items_to_add} ~{self.items_to_set} -{self.keys_to_remove})"

    def __repr__(self) -> str:
        return str(self)


class _DiffOpcode(Enum):
    EQUAL = "="
    REPLACE = "~"
    INSERT = "+"
    DELETE = "-"


class List(FullElement["ListDiff"]):
    """
    A list is an ordered collection of Atoms
    """

    def __init__(self, atoms: list[Atom]) -> None:
        self._atoms = atoms

    def copy(self) -> "List":
        return self.__class__(atoms=list(self._atoms))

    def to_primitive(self) -> Primitive:
        return ["list", *(atom.to_primitive() for atom in self._atoms)]

    @classmethod
    def _from_primitive(cls, primitive: Primitive) -> "List":
        primitive = cast(list[str], primitive)
        atoms = [FullElement.from_primitive(atom) for atom in primitive]
        return cls(atoms=cast(list[Atom], atoms))

    @classmethod
    def zero(cls) -> "List":
        return cls(atoms=[])

    @classmethod
    def diff_type(cls) -> type["ListDiff"]:
        return ListDiff

    def diff(self, other: "List") -> "ListDiff":
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self)} are only diffable against other {type(self)}. Got {type(other)}")
        matcher = difflib.SequenceMatcher(a=self._atoms, b=other._atoms)
        diff: list[tuple[str, int, str]] = []
        for group in matcher.get_grouped_opcodes(n=1):
            for opcode, self_start, self_end, other_start, other_end in group:
                if opcode == "equal":
                    for idx in range(other_start, other_end):
                        diff.append((_DiffOpcode.EQUAL.value, idx, other._atoms[idx].value))
                elif opcode == "replace":
                    for idx in range(other_start, other_end):
                        diff.append((_DiffOpcode.REPLACE.value, idx, other._atoms[idx].value))
                elif opcode == "insert":
                    for idx in range(other_start, other_end):
                        diff.append((_DiffOpcode.INSERT.value, idx, other._atoms[idx].value))
                elif opcode == "delete":
                    for idx in range(self_start, self_end):
                        diff.append((_DiffOpcode.DELETE.value, other_start, self._atoms[idx].value))
                else:
                    raise ValueError(f"Invalid opcode {opcode}")

        diff_type = cast(type[ListDiff], self.diff_type())
        return diff_type(diff=diff)

    def _apply_opcodes(self, atoms: list[Atom], opcodes: list[tuple[str, int, str]]) -> list[Atom]:
        for raw_opcode, idx, replacement in opcodes:
            atom = Atom(replacement)
            opcode = _DiffOpcode(raw_opcode)
            if opcode == _DiffOpcode.EQUAL:
                actual = atoms[idx]
                if atom is not None and actual != atom:
                    raise ValueError(f"Diffs don't match at offset {idx}. Expected `{atom}` but got `{actual}`")
            elif opcode == _DiffOpcode.REPLACE:
                atoms[idx] = atom
            elif opcode == _DiffOpcode.INSERT:
                atoms.insert(idx, atom)
            elif opcode == _DiffOpcode.DELETE:
                del atoms[idx : idx + 1]
            else:
                raise ValueError(f"Invalid opcode {opcode}")

        return atoms

    def apply(self, other: "ListDiff") -> "List":
        if not isinstance(other, ListDiff):
            raise TypeError(f"{type(self)}s can only be applied with ListDiff. Got {type(other)}")
        new_atoms = self._apply_opcodes(self._atoms, other.diff)
        return self.__class__(atoms=new_atoms)

    def __getitem__(self, idx: int) -> Atom:
        return self._atoms[idx]

    def __setitem__(self, idx: int, value: Atom) -> None:
        self._atoms[idx] = value

    def __delitem__(self, idx: int) -> None:
        del self._atoms[idx]

    def __len__(self) -> int:
        return len(self._atoms)

    def __iter__(self) -> Iterator[Atom]:
        return iter(self._atoms)

    def __contains__(self, value: Atom) -> bool:
        return value in self._atoms

    def append(self, value: Atom) -> None:
        self._atoms.append(value)

    def extend(self, values: Iterable[Atom]) -> None:
        self._atoms.extend(values)

    def __iadd__(self, other: Iterable[Atom]) -> "List":
        self._atoms += other
        return self

    def __hash__(self) -> int:
        return hash(self._atoms)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, List):
            return __o._atoms == self._atoms
        else:
            raise TypeError("Lists are only comparable to other lists")

    def __str__(self) -> str:
        return str(self._atoms)

    def __repr__(self) -> str:
        return str(self)


class ListDiff(DiffElement[List]):
    def __init__(self, diff: list[tuple[str, int, str]]) -> None:
        self.diff = diff

    def to_primitive(self) -> Primitive:
        return [[op, idx, replacement] for op, idx, replacement in self.diff]

    @classmethod
    def _from_primitive(cls, primitive: Primitive) -> "DiffElement":
        primitive = cast(list[list], primitive)

        diffs = [(op, idx, replacement) for op, idx, replacement in primitive]
        return cls(diff=diffs)

    @classmethod
    def full_type(cls) -> type[List]:
        return List

    def __hash__(self) -> int:
        return hash(self.diff)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, ListDiff):
            return __o.diff == self.diff
        else:
            raise TypeError("ListDiffs are only comparable to other list diffs")

    def __str__(self) -> str:
        return str(self.diff)

    def __repr__(self) -> str:
        return str(self)


if __name__ == "__main__":
    from typing import Iterable
    import pathlib

    def find_test_files(filename: str) -> Iterable[pathlib.Path]:
        file = pathlib.Path(filename)
        pattern = f"test_{file.stem}.py"
        root = file.parent
        while root.parent != root:
            testdirs = [child for child in root.iterdir() if child.is_dir() and child.name in ("test", "tests")]
            for testdir in testdirs:
                yield from testdir.rglob(pattern)

            root = root.parent

    import unittest

    for testfile in find_test_files(__file__):
        tests = unittest.defaultTestLoader.discover(str(testfile.parent), pattern=testfile.name)
        runner = unittest.TextTestRunner()
        results = runner.run(tests)
