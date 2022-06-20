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
        assert applied == elementB, f"Expected: {elementB!r} Actual: {applied!r}"

    def _test_serialization(self, element):
        serialized = element.to_primitive()
        roundtripped = FullElement.from_primitive(serialized)
        assert element == roundtripped, f"Expected: {element!r} Actual: {roundtripped!r}"

    def _test_serialization_diff(self, elementA, elementB):
        diffed = elementA.diff(elementB)
        serialized = diffed.to_primitive()
        roundtripped = cast(MapDiff, DiffElement.from_primitive(serialized))
        assert diffed == roundtripped, f"Expected: {diffed!r} Actual: {roundtripped!r}"

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

        with self.subTest("Atom infer"):
            inferred = FullElement.infer(atomA.value)
            assert inferred == atomA

        with self.subTest("Atom combine"):
            combined = atomA.combine(atomB)
            assert combined == atomB

        with self.subTest("Atom ordering"):
            assert atomA < atomB


class TestSet(ElementTest):
    def test_atom_set(self):
        AtomSet = Set[Atom]
        setA = AtomSet(set([Atom(v) for v in ["a", "both"]]))
        setB = AtomSet(set([Atom(v) for v in ["b", "both"]]))

        self._run_standard_tests("Set[Atom]", setA, setB)

        with self.subTest("Set[Atom] infer"):
            inferred = FullElement.infer(set([a.value for a in setA]))
            assert inferred == setA

        with self.subTest("Set[Atom] combine"):
            combined = setA.combine(setB)
            assert combined == FullElement.infer(set(["a", "both", "b"]))

        with self.subTest("Set[Atom] ordering"):
            assert setA < setB, f"{setA=} {setB=}"
            assert FullElement.infer(set(["a", "b"])) < FullElement.infer(set(["b"]))

    def test_atom_set_set(self):
        AtomSetSet = Set[Set[Atom]]
        AtomSet = Set[Atom]
        setA = AtomSetSet(
            set(
                [
                    AtomSet(set([Atom(v) for v in ["shared"]])),
                    AtomSet(set([Atom(v) for v in ["a"]])),
                    AtomSet(set([Atom(v) for v in ["a", "changed"]])),
                ]
            )
        )
        setB = AtomSetSet(
            set(
                [
                    AtomSet(set([Atom(v) for v in ["shared"]])),
                    AtomSet(set([Atom(v) for v in ["b"]])),
                    AtomSet(set([Atom(v) for v in ["b", "changed"]])),
                ]
            )
        )

        self._run_standard_tests("Set[Set[Atom]]", setA, setB)

    def test_atom_map_set(self):
        AtomMapSet = Set[Map[Atom, AtomDiff]]
        AtomMap = Map[Atom, AtomDiff]
        setA = AtomMapSet(
            set(
                [
                    AtomMap(
                        {
                            Atom(k): Atom(v)
                            for k, v in {
                                "a": "a",
                            }.items()
                        }
                    ),
                    AtomMap(
                        {
                            Atom(k): Atom(v)
                            for k, v in {
                                "shared": "shared",
                            }.items()
                        }
                    ),
                    AtomMap(
                        {
                            Atom(k): Atom(v)
                            for k, v in {
                                "unchanged": "unchanged",
                                "changed": "a",
                            }.items()
                        }
                    ),
                ]
            )
        )
        setB = AtomMapSet(
            set(
                [
                    AtomMap(
                        {
                            Atom(k): Atom(v)
                            for k, v in {
                                "b": "b",
                            }.items()
                        }
                    ),
                    AtomMap(
                        {
                            Atom(k): Atom(v)
                            for k, v in {
                                "shared": "shared",
                            }.items()
                        }
                    ),
                    AtomMap(
                        {
                            Atom(k): Atom(v)
                            for k, v in {
                                "unchanged": "unchanged",
                                "changed": "b",
                            }.items()
                        }
                    ),
                ]
            )
        )

        self._run_standard_tests("Set[Map[Atom]]", setA, setB)


class TestMap(ElementTest):
    def test_atom_map(self):
        AtomMap = Map[Atom, AtomDiff]
        mapA = AtomMap({Atom(k): Atom(k) for k in ["a", "unchanged", "changed"]})
        mapBdict = {Atom(k): Atom(k) for k in ["b", "unchanged", "changed"]}
        mapBdict[Atom("changed")] = Atom("changedB")
        mapB = AtomMap(mapBdict)

        self._run_standard_tests("Map[Atom]", mapA, mapB)

        with self.subTest("Map[Atom] infer"):
            inferred = FullElement.infer({k.value: v.value for k, v in mapA.items()})
            assert inferred == mapA

        with self.subTest("Map[Atom] combine"):
            combined = mapA.combine(mapB)
            expected = FullElement.infer({k: k for k in "a unchanged b".split()} | {"changed": "changedB"})
            assert combined == expected

        with self.subTest("Map[Atom] ordering"):
            assert mapA < mapB

    def test_atom_set_map(self):
        AtomSetMap = Map[Set[Atom], SetDiff[Atom]]
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

        with self.subTest("Map[Set[Atom]] infer"):
            inferred = FullElement.infer({k.value: set(a.value for a in v) for k, v in mapA.items()})
            assert inferred == mapA

        with self.subTest("Map[Set[Atom]] combine"):
            combined = mapA.combine(mapB)
            expected = FullElement.infer({k: set([k]) for k in "a b both".split()} | {"changed": set("a b both".split())})
            assert combined == expected

    def test_atom_map_map(self):
        NestedMap = Map[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]]

        mapA = NestedMap(
            {
                Atom("a"): Map(
                    {
                        Atom("a"): Atom("a"),
                    }
                ),
                Atom("unchanged"): Map(
                    {
                        Atom("unchanged"): Atom("unchanged"),
                    }
                ),
                Atom("changed"): Map(
                    {
                        Atom("changed"): Atom("changed"),
                    }
                ),
                Atom("nested"): Map(
                    {
                        Atom("a"): Atom("a"),
                        Atom("both"): Atom("both"),
                        Atom("changed"): Atom("changed"),
                    }
                ),
            }
        )
        mapB = NestedMap(
            {
                Atom("b"): Map(
                    {
                        Atom("b"): Atom("b"),
                    }
                ),
                Atom("unchanged"): Map(
                    {
                        Atom("unchanged"): Atom("unchanged"),
                    }
                ),
                Atom("changed"): Map(
                    {
                        Atom("changed"): Atom("changedB"),
                    }
                ),
                Atom("nested"): Map(
                    {
                        Atom("b"): Atom("b"),
                        Atom("both"): Atom("both"),
                        Atom("changed"): Atom("changedB"),
                    }
                ),
            }
        )

        self._run_standard_tests("Map[Map[Atom]]", mapA, mapB)

        with self.subTest("Map[Map[Atom]] infer"):
            inferred = FullElement.infer({k.value: {sk.value: sv.value for sk, sv in v.items()} for k, v in mapA.items()})
            assert inferred == mapA

        with self.subTest("Map[Map[Atom]] combine"):
            combined = mapA.combine(mapB)
            expected = FullElement.infer(
                {k: {k: k} for k in "a b unchanged".split()}
                | {"changed": {"changed": "changedB"}, "nested": {k: k for k in "a b both".split()} | {"changed": "changedB"}}
            )
            assert combined == expected


class TestList(ElementTest):
    def test_list(self):
        listA = List([Atom(v) for v in "a b removed d e f g h j k l m achanged o p".split()])
        listB = List([Atom(v) for v in "a b d e f g h inserted j k l m bchanged o p".split()])

        self._run_standard_tests("List", listA, listB)

        with self.subTest("List infer"):
            inferred = FullElement.infer([a.value for a in listA])
            assert inferred == listA

        with self.subTest("List combine"):
            combined = listA.combine(listB)
            expected = FullElement.infer(list("a b removed d e f g h inserted j k l m bchanged achanged o p".split()))
            assert combined == expected

        with self.subTest("Map[Atom] ordering"):
            assert FullElement.infer("a b c".split()) < FullElement.infer("a b d".split())
            assert FullElement.infer("a b".split()) < FullElement.infer("a b d".split())
            assert FullElement.infer("a b".split()) < FullElement.infer("b c".split())


if __name__ == "__main__":
    unittest.main()
