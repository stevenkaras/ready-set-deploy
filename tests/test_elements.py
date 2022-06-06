import unittest
from typing import cast

from ready_set_deploy.elements import Atom, AtomDiff, DiffElement, FullElement, Set, SetDiff, Map, MultiMap, List, MapDiff, generate_map_type


class TestAtom(unittest.TestCase):
    def test_copy(self):
        atom = Atom("foo")
        copied = atom.copy()
        assert copied == atom

    def test_sanity(self):
        atomA = Atom("A")
        atomB = Atom("B")
        assert f"{atomA} {atomB}" == "A B"
        diffed = atomA.diff(atomB)
        assert f"{diffed}" == "B"
        applied = atomA.apply(diffed)
        assert f"{applied}" == "B"

    def test_serialization(self):
        atomA = Atom("foo")
        atomB = Atom("foo")
        diffed = atomA.diff(atomB)

        serialized = atomA.to_primitive()
        roundtripped = FullElement.from_primitive(serialized)
        assert atomA == roundtripped

        serialized = diffed.to_primitive()
        roundtripped = DiffElement.from_primitive(serialized)
        assert diffed == roundtripped


class TestSet(unittest.TestCase):
    def test_copy(self):
        setA = Set(set([Atom(v) for v in ["a", "both"]]))
        copied = setA.copy()
        assert copied == setA

    def test_sanity(self):
        setA = Set(set([Atom(v) for v in ["a", "both"]]))
        setB = Set(set([Atom(v) for v in ["b", "both"]]))
        diffed = cast(SetDiff, setA.diff(setB))
        assert diffed.to_add == set([AtomDiff("b")])
        assert diffed.to_remove == set([AtomDiff("a")])
        applied = setA.apply(diffed)
        assert applied == setB

    def test_serialization(self):
        setA = Set(set([Atom(v) for v in ["a", "both"]]))
        setB = Set(set([Atom(v) for v in ["b", "both"]]))
        diffed = cast(SetDiff, setA.diff(setB))

        serialized = setA.to_primitive()
        roundtripped = FullElement.from_primitive(serialized)
        assert setA == roundtripped

        serialized = diffed.to_primitive()
        roundtripped = DiffElement.from_primitive(serialized)
        assert diffed == roundtripped


class TestMap(unittest.TestCase):
    def test_copy(self):
        mapA = Map({Atom(k): Atom(k) for k in ["a", "unchanged", "changed"]})
        copied = mapA.copy()
        assert copied == mapA

    def test_sanity(self):
        mapA = Map({Atom(k): Atom(k) for k in ["a", "unchanged", "changed"]})
        mapBdict = {Atom(k): Atom(k) for k in ["b", "unchanged", "changed"]}
        mapBdict[Atom("changed")] = Atom("changedB")
        mapB = Map(mapBdict)
        diffed = mapA.diff(mapB)
        applied = mapA.apply(diffed)
        assert applied == mapB

    def test_serialization(self):
        mapA = Map({Atom(k): Atom(k) for k in ["a", "unchanged", "changed"]})
        mapBdict = {Atom(k): Atom(k) for k in ["b", "unchanged", "changed"]}
        mapBdict[Atom("changed")] = Atom("changedB")
        mapB = Map(mapBdict)
        diffed = cast(MapDiff, mapA.diff(mapB))

        serialized = mapA.to_primitive()
        roundtripped = FullElement.from_primitive(serialized)
        assert mapA == roundtripped

        serialized = diffed.to_primitive()
        roundtripped = cast(MapDiff, DiffElement.from_primitive(serialized))
        assert diffed == roundtripped


class TestMultiMap(unittest.TestCase):
    def test_copy(self):
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
        copied = mmapA.copy()
        assert copied == mmapA

    def test_sanity(self):
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
        diffed = mmapA.diff(mmapB)
        applied = mmapA.apply(diffed)
        assert applied == mmapB


class TestComplexMap(unittest.TestCase):
    def test_map_of_maps(self):
        NestedMap, _ = generate_map_type("NestedMap", Map, MapDiff)

        optsA = NestedMap(
            {
                Atom("a"): Map(
                    {
                        Atom("name"): Atom("a"),
                    }
                ),
                Atom("unchanged"): Map(
                    {
                        Atom("name"): Atom("unchanged"),
                    }
                ),
                Atom("changed"): Map(
                    {
                        Atom("name"): Atom("changed"),
                    }
                ),
                Atom("nested"): Map(
                    {
                        Atom("name"): Atom("nested"),
                        Atom("prefix"): Atom("a"),
                    }
                ),
            }
        )
        optsB = NestedMap(
            {
                Atom("b"): Map(
                    {
                        Atom("name"): Atom("b"),
                    }
                ),
                Atom("unchanged"): Map(
                    {
                        Atom("name"): Atom("unchanged"),
                    }
                ),
                Atom("changed"): Map(
                    {
                        Atom("name"): Atom("changedB"),
                    }
                ),
                Atom("nested"): Map(
                    {
                        Atom("name"): Atom("nested"),
                        Atom("prefix"): Atom("b"),
                    }
                ),
            }
        )

        diffed = optsA.diff(optsB)
        applied = optsA.apply(diffed)
        assert applied == optsB


class TestList(unittest.TestCase):
    def test_copy(self):
        listA = List([Atom(v) for v in "a b c d e f g h j k l m n o p".split()])
        copied = listA.copy()
        assert copied == listA

    def test_sanity(self):
        listA = List([Atom(v) for v in "a b c d e f g h j k l m n o p".split()])
        listB = List([Atom(v) for v in "a b d e f g h i j k l m q o p".split()])
        diffed = listA.diff(listB)
        applied = listA.apply(diffed)
        assert applied == listB, f"{applied=} {listB=}"

    def test_serialization(self):
        listA = List([Atom(v) for v in "a b c d e f g h j k l m n o p".split()])
        listB = List([Atom(v) for v in "a b d e f g h i j k l m q o p".split()])
        diffed = listA.diff(listB)

        serialized = listA.to_primitive()
        roundtripped = FullElement.from_primitive(serialized)
        assert listA == roundtripped

        serialized = diffed.to_primitive()
        roundtripped = DiffElement.from_primitive(serialized)
        assert diffed == roundtripped


if __name__ == "__main__":
    unittest.main()
