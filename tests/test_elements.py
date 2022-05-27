import unittest
from typing import cast

from ready_set_deploy.elements import Atom, Set, SetDiff, Map, MultiMap, List


class TestAtom(unittest.TestCase):
    def test_sanity(self):
        atomA = Atom("A")
        atomB = Atom("B")
        assert f"{atomA} {atomB}" == "A B"
        diffed = atomA.diff(atomB)
        assert f"{diffed}" == "B"
        applied = atomA.apply(diffed)
        assert f"{applied}" == "B"
        raw = Atom("back\\slash\nnew line")
        encoded = raw.encode()
        decoded = Atom.decode(encoded)
        assert encoded == "back\\\\slash\\nnew line"
        assert raw == decoded


class TestSet(unittest.TestCase):
    def test_sanity(self):
        setA = Set(set([Atom(v) for v in ["a", "both"]]))
        setB = Set(set([Atom(v) for v in ["b", "both"]]))
        diffed = cast(SetDiff, setA.diff(setB))
        assert diffed.to_add == set([Atom("b")])
        assert diffed.to_remove == set([Atom("a")])
        applied = setA.apply(diffed)
        assert applied == setB


class TestMap(unittest.TestCase):
    def test_sanity(self):
        mapA = Map({Atom(k): Atom(k) for k in ["a", "unchanged", "changed"]})
        mapBdict = {Atom(k): Atom(k) for k in ["b", "unchanged", "changed"]}
        mapBdict[Atom("changed")] = Atom("changedB")
        mapB = Map(mapBdict)
        diffed = mapA.diff(mapB)
        applied = mapA.apply(diffed)
        assert applied == mapB


class TestMultiMap(unittest.TestCase):
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


class TestList(unittest.TestCase):
    def test_sanity(self):
        listA = List([Atom(v) for v in "a b c d e f g h j k l m n o p".split()])
        listB = List([Atom(v) for v in "a b d e f g h i j k l m q o p".split()])
        diffed = listA.diff(listB)
        applied = listA.apply(diffed)
        assert applied == listB, f"{applied=} {listB=}"


if __name__ == "__main__":
    unittest.main()
