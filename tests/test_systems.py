import unittest

from ready_set_deploy.systems import System
from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom


class TestSystems(unittest.TestCase):
    def _build_systems(self) -> tuple[System, System]:
        systemA = System(
            components=[
                Component(name="a", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
                Component(name="unchanged", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
                Component(name="changed", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
            ]
        )
        systemB = System(
            components=[
                Component(name="unchanged", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
                Component(name="changed", dependencies=[], qualifier=(), elements={"foo": Atom("barbaz")}),
                Component(name="b", dependencies=[], qualifier=(), elements={"foo": Atom("barbaz")}),
            ]
        )
        return systemA, systemB

    def test_sanity(self):
        systemA, systemB = self._build_systems()
        assert systemA.is_valid()
        assert systemB.is_valid()
        diffed = systemA.diff(systemB)
        applied = systemA.apply(diffed)
        assert applied == systemB

    def test_combine(self):
        systemA, systemB = self._build_systems()
        combined = systemA.combine(systemB)
        expected = System(
            components=[
                Component(name="a", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
                Component(name="unchanged", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
                Component(name="changed", dependencies=[], qualifier=(), elements={"foo": Atom("barbaz")}),
                Component(name="b", dependencies=[], qualifier=(), elements={"foo": Atom("barbaz")}),
            ]
        )
        assert combined == expected

    def test_serialize(self):
        systemA, systemB = self._build_systems()
        diffed = systemA.diff(systemB)

        serialized = systemA.to_primitive()
        roundtripped = System.from_primitive(serialized)
        assert systemA == roundtripped

        serialized = diffed.to_primitive()
        roundtripped = System.from_primitive(serialized)
        assert diffed == roundtripped


if __name__ == "__main__":
    unittest.main()
