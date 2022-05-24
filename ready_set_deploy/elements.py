
from collections.abc import Iterable, Mapping
from typing import Generic, TypeVar


class Element:
    def diff(self, other: "Element") -> "Element":
        raise NotImplementedError("diff")

    def merge(self, other: "Element") -> "Element":
        raise NotImplementedError("merge")


class Atom(Element):
    def __init__(self, value: str) -> None:
        self._value = value

    def diff(self, other: "Atom") -> "Atom":
        return other

    def merge(self, other: "Atom") -> "Atom":
        return Atom(other._value)

    def __hash__(self) -> int:
        return hash(self._value)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Atom):
            return __o._value == self._value
        else:
            raise TypeError("Atoms are only comparable to other atoms")

    def __str__(self) -> str:
        return self._value

    __repr__ = __str__


class Set(Element):
    def __init__(self, atoms: set[Atom]) -> None:
        self._atoms = atoms

    def diff(self, other: "Set") -> "SetDiff":
        return SetDiff(other._atoms - self._atoms, self._atoms - other._atoms)

    def merge(self, other: "SetDiff") -> "Set":
        return Set((self._atoms - other._to_remove) | other._to_add)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Set):
            return __o._atoms == self._atoms
        else:
            raise TypeError("Sets are only comparable to other set")

    def __str__(self) -> str:
        return str(self._atoms)

    __repr__ = __str__


class SetDiff(Element):
    def __init__(self, to_add: set[Atom], to_remove: set[Atom]) -> None:
        self._to_add = to_add
        self._to_remove = to_remove

    def __str__(self) -> str:
        return f"(+{self._to_add} -{self._to_remove})"

    __repr__ = __str__


_V = TypeVar("_V", bound=Element)


class _GenericMap(Element, Generic[_V]):
    def __init__(self, map: Mapping[Atom, _V]) -> None:
        self._map = map

    def diff(self, other: "_GenericMap") -> "_GenericMapDiff[_V]":
        keys_to_remove = set(self._map.keys()) - set(other._map.keys())
        items_to_add = [
            (key, value)
            for key, value in other._map.items()
            if key not in self._map
        ]
        items_to_set = [
            (key, self._map[key].diff(value))
            for key, value in other._map.items()
            if key in self._map and self._map[key] != value
        ]
        return _GenericMapDiff(keys_to_remove, items_to_add, items_to_set)

    def merge(self, other: "_GenericMapDiff[_V]") -> "_GenericMap[_V]":
        new_map = dict(self._map)
        for key in other._keys_to_remove:
            del new_map[key]

        for key, value in other._items_to_set:
            new_map[key] = self._map[key].merge(value)

        for key, value in other._items_to_add:
            new_map[key] = value

        return _GenericMap(new_map)

    def __str__(self) -> str:
        return str(self._map)

    __repr__ = __str__


_V = TypeVar("_V", bound=Element)


class _GenericMapDiff(Element, Generic[_V]):
    def __init__(self, keys_to_remove: Iterable[Atom], items_to_add: Iterable[tuple[Atom, _V]], items_to_set: Iterable[tuple[Atom, _V]]) -> None:
        self._keys_to_remove = keys_to_remove
        self._items_to_set = items_to_set
        self._items_to_add = items_to_add

    def __str__(self) -> str:
        return f"(+{self._items_to_add} ~{self._items_to_set} -{self._keys_to_remove})"

    __repr__ = __str__


class Map(_GenericMap[Atom]): pass
class MapDiff(_GenericMapDiff[Atom]): pass
class MultiMap(_GenericMap[Set]): pass
class MultiMapDiff(_GenericMapDiff[Set]): pass


if __name__ == '__main__':
    atomA = Atom("A")
    atomB = Atom("B")
    print(f"{atomA} {atomB}")  # A B
    diffed = atomA.diff(atomB)
    print(f"{diffed}")  # B
    merged = atomA.merge(diffed)
    print(f"{merged}")  # B

    setA = Set(set([Atom(v) for v in ["a", "both"]]))
    setB = Set(set([Atom(v) for v in ["b", "both"]]))
    print(f"{setA} {setB}")  # {both, a} {both, b}
    diffed = setA.diff(setB)
    print(f"{diffed}")  # (+{b} -{a})
    merged = setA.merge(diffed)
    print(f"{merged}")  # {both, b}

    mapA = Map({Atom(k): Atom(k) for k in ["a", "unchanged", "changed"]})
    mapB = {Atom(k): Atom(k) for k in ["b", "unchanged", "changed"]}
    mapB[Atom("changed")] = Atom("changedB")
    mapB = Map(mapB)
    print(f"{mapA} {mapB}")  # {a: a, unchanged: unchanged, changed: changed} {b: b, unchanged: unchanged, changed: changedB}
    diffed = mapA.diff(mapB)
    print(f"{diffed}")  # (+[(b, b)] ~[(changed, changedB)] -{a})
    merged = mapA.merge(diffed)
    print(f"{merged}")  # {unchanged: unchanged, changed: changedB, b: b}

    mmapA = MultiMap({
        Atom(k): Set(set(Atom(e) for e in v))
        for k, v in {
            "a": ["a"],
            "both": ["both"],
            "changed": ["a", "both"],
        }.items()
    })
    mmapB = MultiMap({
        Atom(k): Set(set(Atom(e) for e in v))
        for k, v in {
            "b": ["b"],
            "both": ["both"],
            "changed": ["b", "both"],
        }.items()
    })
    print(f"{mmapA} {mmapB}")
    diffed = mmapA.diff(mmapB)
    print(f"{diffed}")
    merged = mmapA.merge(diffed)
    print(f"{merged}")
