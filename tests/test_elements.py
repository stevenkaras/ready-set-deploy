import unittest
from typing import cast

from ready_set_deploy.elements import Atom, AtomDiff, DiffElement, FullElement, Set, SetDiff, Map, MapDiff, List


class ElementTest(unittest.TestCase):
    def _test_copy(self, element):
        copied = element.copy()
        assert copied == element

    def _test_diff_apply(self, elementA, elementB):
        diffed = elementA.diff(elementB)
        applied = elementA.apply(diffed)
        assert applied == elementB

    def _test_serialization(self, element):
        serialized = element.to_primitive()
        roundtripped = FullElement.from_primitive(serialized)
        assert element == roundtripped

    def _test_serialization_diff(self, elementA, elementB):
        diffed = elementA.diff(elementB)
        serialized = diffed.to_primitive()
        roundtripped = cast(MapDiff, DiffElement.from_primitive(serialized))
        assert diffed == roundtripped

    def _run_standard_tests(self, subtype, elementA, elementB):
        with self.subTest(f"{subtype} copy"):
            self._test_copy(elementA)

        with self.subTest(f"{subtype} diff apply"):
            self._test_diff_apply(elementA, elementB)

        with self.subTest(f"{subtype} serialization"):
            self._test_serialization(elementA)

        with self.subTest(f"{subtype} serialization diff"):
            self._test_serialization_diff(elementA, elementB)


class TestAtom(ElementTest):
    def _build_atoms(self):
        atomA = Atom("A")
        atomB = Atom("B")

        return atomA, atomB

    def test_atoms(self):
        atomA, atomB = self._build_atoms()
        self._run_standard_tests("Atom", atomA, atomB)


class TestSet(ElementTest):
    def test_atom_set(self):
        AtomSet = Set[Atom, AtomDiff]
        setA = AtomSet(set([Atom(v) for v in ["a", "both"]]))
        setB = AtomSet(set([Atom(v) for v in ["b", "both"]]))

        self._run_standard_tests("Set[Atom]", setA, setB)

    def test_atom_set_set(self):
        AtomSetSet = Set[Set[Atom, AtomDiff], SetDiff[Atom, AtomDiff]]
        AtomSet = Set[Atom, AtomDiff]
        setA = AtomSetSet(set([
            AtomSet(set([
                Atom(v) for v in ["shared"]
            ])),
            AtomSet(set([
                Atom(v) for v in ["a"]
            ])),
            AtomSet(set([
                Atom(v) for v in ["a", "changed"]
            ])),
        ]))
        setB = AtomSetSet(set([
            AtomSet(set([
                Atom(v) for v in ["shared"]
            ])),
            AtomSet(set([
                Atom(v) for v in ["b"]
            ])),
            AtomSet(set([
                Atom(v) for v in ["b", "changed"]
            ])),
        ]))

        self._run_standard_tests("Set[Set[Atom]]", setA, setB)

    def test_atom_map_set(self):
        AtomMapSet = Set[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]]
        AtomMap = Map[Atom, AtomDiff]
        setA = AtomMapSet(set([
            AtomMap({
                Atom(k): Atom(v)
                for k, v in {
                    "a": "a",
                }.items()
            }),
            AtomMap({
                Atom(k): Atom(v)
                for k, v in {
                    "shared": "shared",
                }.items()
            }),
            AtomMap({
                Atom(k): Atom(v)
                for k, v in {
                    "unchanged": "unchanged",
                    "changed": "a",
                }.items()
            }),
        ]))
        setB = AtomMapSet(set([
            AtomMap({
                Atom(k): Atom(v)
                for k, v in {
                    "b": "b",
                }.items()
            }),
            AtomMap({
                Atom(k): Atom(v)
                for k, v in {
                    "shared": "shared",
                }.items()
            }),
            AtomMap({
                Atom(k): Atom(v)
                for k, v in {
                    "unchanged": "unchanged",
                    "changed": "b",
                }.items()
            }),
        ]))

        self._run_standard_tests("Set[Map[Atom]]", setA, setB)


class TestMap(ElementTest):
    def test_atom_map(self):
        AtomMap = Map[Atom, AtomDiff]
        mapA = AtomMap({Atom(k): Atom(k) for k in ["a", "unchanged", "changed"]})
        mapBdict = {Atom(k): Atom(k) for k in ["b", "unchanged", "changed"]}
        mapBdict[Atom("changed")] = Atom("changedB")
        mapB = AtomMap(mapBdict)

        self._run_standard_tests("Map[Atom]", mapA, mapB)

    def test_atom_set_map(self):
        AtomSetMap = Map[Set[Atom, AtomDiff], SetDiff[Atom, AtomDiff]]
        mapA = AtomSetMap(
            {
                Atom(k): Set(set(Atom(e) for e in v))
                for k, v in {
                    "a": ["a"],
                    "both": ["both"],
                    "changed": ["a", "both"],
                }.items()
            }
        )
        mapB = AtomSetMap(
            {
                Atom(k): Set(set(Atom(e) for e in v))
                for k, v in {
                    "b": ["b"],
                    "both": ["both"],
                    "changed": ["b", "both"],
                }.items()
            }
        )

        self._run_standard_tests("Map[Set[Atom]]", mapA, mapB)

    def test_atom_map_map(self):
        NestedMap = Map[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]]

        mapA = NestedMap(
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
        mapB = NestedMap(
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

        self._run_standard_tests("Map[Map[Atom]]", mapA, mapB)


class TestList(ElementTest):
    def test_list(self):
        listA = List([Atom(v) for v in "a b c d e f g h j k l m n o p".split()])
        listB = List([Atom(v) for v in "a b d e f g h i j k l m q o p".split()])

        self._run_standard_tests("List", listA, listB)


if __name__ == "__main__":
    unittest.main()
