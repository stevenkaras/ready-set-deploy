from collections.abc import Iterable, MutableMapping
from typing import Generic, Iterator, Optional, TypeVar, cast, Type
import difflib
from enum import Enum


class Element:
    """
    Elements are the basic building blocks of system configuration state.
    """


class FullElement(Element):
    def diff(self, other: "FullElement") -> "DiffElement":
        """
        Produce a DiffElement that when applied to self would produce other.
        """
        raise NotImplementedError("diff")

    def apply(self, other: "DiffElement") -> "FullElement":
        """
        Apply the changes from other to produce a new FullElement.

        Assuming the diff element was produced from this element, this should return the original "other".
        """
        raise NotImplementedError("apply")

    @classmethod
    def zero(cls) -> "FullElement":
        """
        Generate a zero-element of the given type
        """
        raise NotImplementedError("zero")

    @classmethod
    def diff_type(cls) -> Type["DiffElement"]:
        """
        Return the full type associated with this diff type
        """
        raise NotImplementedError("diff_type")

    def copy(self) -> "FullElement":
        """
        Return a deep copy of this element
        """
        raise NotImplementedError("copy")


class DiffElement(Element):
    @classmethod
    def full_type(cls) -> Type[FullElement]:
        """
        Return the diff type associated with this full type
        """
        raise NotImplementedError("full_type")

    def copy(self) -> "DiffElement":
        """
        Return a deep copy of this element
        """
        raise NotImplementedError("copy")


class Atom(FullElement):
    """
    Represents an atomically replaceable element (a string).
    """

    def __init__(self, value: str) -> None:
        self.value = value

    def copy(self) -> FullElement:
        return self.__class__(value=self.value)

    @classmethod
    def zero(cls) -> FullElement:
        return cls(value="")

    @classmethod
    def diff_type(cls) -> Type[DiffElement]:
        return AtomDiff

    def diff(self, other: FullElement) -> DiffElement:
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self)} are only diffable against other {type(self)}. Got {type(other)}")
        diff_type = cast(Type[AtomDiff], self.diff_type())
        return diff_type(value=other.value)

    def apply(self, other: DiffElement) -> FullElement:
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
        return str(self)


class AtomDiff(DiffElement):
    def __init__(self, value: str) -> None:
        self.value = value

    def copy(self):
        return self.__class__(value=self.value)

    @classmethod
    def full_type(cls) -> Type[FullElement]:
        return Atom

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return str(self)


class Set(FullElement):
    """
    A set is an element representing an unordered collection of Atoms
    """

    def __init__(self, atoms: set[Atom]) -> None:
        self._atoms = atoms

    def copy(self):
        return self.__class__(atoms=set(self._atoms))

    @classmethod
    def zero(cls) -> FullElement:
        return cls(atoms=set())

    @classmethod
    def diff_type(cls) -> Type[DiffElement]:
        return SetDiff

    def diff(self, other: FullElement) -> DiffElement:
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self)} are only diffable against other {type(self)}. Got {type(other)}")
        diff_type = cast(Type[SetDiff], self.diff_type())
        return diff_type(to_add=other._atoms - self._atoms, to_remove=self._atoms - other._atoms)

    def apply(self, other: DiffElement) -> FullElement:
        if not isinstance(other, self.diff_type()):
            raise TypeError(f"{type(self)}s can only be applied with SetDiff. Got {type(other)}")
        other = cast(SetDiff, other)
        return self.__class__(atoms=(self._atoms - other.to_remove) | other.to_add)

    def add(self, value: Atom) -> "Set":
        """
        Add the given value to this set
        """
        self._atoms.add(value)
        return self

    def remove(self, value: Atom) -> "Set":
        """
        Remove the given value from this set if present
        """
        self._atoms.discard(value)
        return self

    def __len__(self) -> int:
        return len(self._atoms)

    def __iter__(self) -> Iterator[Atom]:
        return iter(self._atoms)

    def __contains__(self, item) -> bool:
        return item in self._atoms

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Set):
            return __o._atoms == self._atoms
        else:
            raise TypeError("Sets are only comparable to other set")

    def __str__(self) -> str:
        return str(self._atoms)

    def __repr__(self) -> str:
        return str(self)


class SetDiff(DiffElement):
    def __init__(self, to_add: set[Atom], to_remove: set[Atom]) -> None:
        self.to_add = to_add
        self.to_remove = to_remove

    def copy(self):
        return self.__class__(to_add=self.to_add, to_remove=self.to_remove)

    @classmethod
    def full_type(cls) -> Type[FullElement]:
        return Set

    def __str__(self) -> str:
        return f"(+{self.to_add} -{self.to_remove})"

    def __repr__(self) -> str:
        return str(self)


_F = TypeVar("_F", bound=FullElement)
_D = TypeVar("_D", bound=DiffElement)


class _GenericMap(FullElement, Generic[_F, _D]):
    def __init__(self, map: MutableMapping[Atom, _F]) -> None:
        self._map = map

    def copy(self):
        return self.__class__(map={
            key: value.copy()
            for key, value in self._map.items()
        })

    @classmethod
    def zero(cls) -> FullElement:
        return cls(map={})

    @classmethod
    def diff_type(cls) -> Type[DiffElement]:
        return _GenericMapDiff

    def diff(self, other: FullElement) -> DiffElement:
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self)} are only diffable against other {type(self)}. Got {type(other)}")
        keys_to_remove = set(self._map.keys()) - set(other._map.keys())
        raw_items_to_add = [(key, value.copy()) for key, value in other._map.items() if key not in self._map]
        items_to_add = cast(list[tuple[Atom, _F]], raw_items_to_add)
        raw_items_to_set = [
            (key, self._map[key].diff(value)) for key, value in other._map.items() if key in self._map and self._map[key] != value
        ]
        items_to_set = cast(list[tuple[Atom, _D]], raw_items_to_set)
        diff_type = cast(Type[_GenericMapDiff[_F, _D]], self.diff_type())
        return diff_type(keys_to_remove=keys_to_remove, items_to_add=items_to_add, items_to_set=items_to_set)

    def apply(self, other: DiffElement) -> FullElement:
        if not isinstance(other, self.diff_type()):
            raise TypeError(f"{type(self)}s can only be applied with {self.diff_type}. Got {type(other)}")
        other = cast(_GenericMapDiff[_F, _D], other)
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

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, type(self)):
            return __o._map == self._map
        else:
            raise TypeError(f"{type(self)} are only comparable to other {type(self)}")

    def __str__(self) -> str:
        return str(self._map)

    def __repr__(self) -> str:
        return str(self)


class _GenericMapDiff(DiffElement, Generic[_F, _D]):
    def __init__(self, keys_to_remove: Iterable[Atom], items_to_add: Iterable[tuple[Atom, _F]], items_to_set: Iterable[tuple[Atom, _D]]) -> None:
        self.keys_to_remove = keys_to_remove
        self.items_to_set = items_to_set
        self.items_to_add = items_to_add

    def copy(self):
        return self.__class__(
            keys_to_remove=self.keys_to_remove,
            items_to_add=self.items_to_add,
            items_to_set=self.items_to_set,
        )

    @classmethod
    def full_type(cls) -> Type[FullElement]:
        return _GenericMap

    def __str__(self) -> str:
        return f"(+{self.items_to_add} ~{self.items_to_set} -{self.keys_to_remove})"

    def __repr__(self) -> str:
        return str(self)


def generate_map_type(name: str, full_type: Type[_F], diff_type: Type[_D]) -> tuple[Type[_GenericMap[_F, _D]], Type[_GenericMapDiff[_F, _D]]]:
    types: list[Type] = []
    full = type(name, (_GenericMap,), {
        "diff_type": classmethod(lambda cls: types[1])
    })
    types.append(full)
    diff = type(f"{name}Diff", (_GenericMapDiff,), {
        "full_type": classmethod(lambda cls: types[0])
    })
    types.append(diff)
    return full, diff


class Map(_GenericMap[Atom, AtomDiff]):
    """
    A map is a mapping of Atoms to Atoms
    """

    @classmethod
    def diff_type(cls) -> Type[DiffElement]:
        return MapDiff


class MapDiff(_GenericMapDiff[Atom, AtomDiff]):
    @classmethod
    def full_type(cls) -> Type[FullElement]:
        return Map


class NestedMap(_GenericMap[Map, MapDiff]):
    """
    A nested map is a mapping of Atoms to maps of atoms to atoms.

    This is useful to model the installation options of packages
    """

    @classmethod
    def diff_type(cls) -> Type[DiffElement]:
        return NestedMapDiff


class NestedMapDiff(_GenericMapDiff[Map, MapDiff]):
    @classmethod
    def full_type(cls) -> Type[FullElement]:
        return NestedMap


class MultiMap(_GenericMap[Set, SetDiff]):
    """
    A multimap is a mapping of Atoms to multiple Atoms
    """

    @classmethod
    def diff_type(cls) -> Type[DiffElement]:
        return MultiMapDiff

class MultiMapDiff(_GenericMapDiff[Atom, AtomDiff]):
    @classmethod
    def full_type(cls) -> Type[FullElement]:
        return MultiMap


class _DiffOpcode(Enum):
    EQUAL = "="
    REPLACE = "~"
    INSERT = "+"
    DELETE = "-"


class List(FullElement):
    """
    A list is an ordered collection of Atoms
    """

    def __init__(self, atoms: list[Atom]) -> None:
        self._atoms = atoms

    def copy(self):
        return self.__class__(atoms=list(self._atoms))

    @classmethod
    def zero(cls) -> FullElement:
        return cls(atoms=[])

    @classmethod
    def diff_type(cls) -> Type[DiffElement]:
        return ListDiff

    def diff(self, other: FullElement) -> DiffElement:
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

        diff_type = cast(Type[ListDiff], self.diff_type())
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

    def apply(self, other: DiffElement) -> FullElement:
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

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, List):
            return __o._atoms == self._atoms
        else:
            raise TypeError("Sets are only comparable to other set")

    def __str__(self) -> str:
        return str(self._atoms)

    def __repr__(self) -> str:
        return str(self)


class ListDiff(DiffElement):
    def __init__(self, diff: list[tuple[str, int, str]]) -> None:
        self.diff = diff

    @classmethod
    def full_type(cls) -> Type[FullElement]:
        return List

    def __str__(self) -> str:
        return str(self.diff)

    def __repr__(self) -> str:
        return str(self)


if __name__ == "__main__":
    atomA = Atom("A")
    atomB = Atom("B")
    assert f"{atomA} {atomB}" == "A B"
    diffed = atomA.diff(atomB)
    assert f"{diffed}" == "B"
    applied = atomA.apply(diffed)
    assert f"{applied}" == "B"

    setA = Set(set([Atom(v) for v in ["a", "both"]]))
    setB = Set(set([Atom(v) for v in ["b", "both"]]))
    print(f"{setA} {setB}")  # {both, a} {both, b}
    diffed = setA.diff(setB)
    print(f"{diffed}")  # (+{b} -{a})
    applied = setA.apply(diffed)
    print(f"{applied}")  # {both, b}

    mapA = Map({Atom(k): Atom(k) for k in ["a", "unchanged", "changed"]})
    mapBdict = {Atom(k): Atom(k) for k in ["b", "unchanged", "changed"]}
    mapBdict[Atom("changed")] = Atom("changedB")
    mapB = Map(mapBdict)
    print(f"{mapA} {mapB}")  # {a: a, unchanged: unchanged, changed: changed} {b: b, unchanged: unchanged, changed: changedB}
    diffed = mapA.diff(mapB)
    print(f"{diffed}")  # (+[(b, b)] ~[(changed, changedB)] -{a})
    applied = mapA.apply(diffed)
    print(f"{applied}")  # {unchanged: unchanged, changed: changedB, b: b}

    mmapA = MultiMap(
        {
            Atom(k): Set(set(Atom(e) for e in v))
            for k, v in {
                "a": ["a"],
                "both": ["both"],
                "changed": ["a", "both"],
            }.items()
        }
    )
    mmapB = MultiMap(
        {
            Atom(k): Set(set(Atom(e) for e in v))
            for k, v in {
                "b": ["b"],
                "both": ["both"],
                "changed": ["b", "both"],
            }.items()
        }
    )
    print(f"{mmapA} {mmapB}")
    diffed = mmapA.diff(mmapB)
    print(f"{diffed}")
    applied = mmapA.apply(diffed)
    print(f"{applied}")

    listA = List([Atom(v) for v in "a b c d e f g h j k l m n o p".split()])
    listB = List([Atom(v) for v in "a b d e f g h i j k l m q o p".split()])
    diffed = listA.diff(listB)
    applied = listA.apply(diffed)
    assert applied == listB, f"{applied=} {listB=}"
