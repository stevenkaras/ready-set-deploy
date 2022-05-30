import unittest

from ready_set_deploy.systems import System
from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom


class TestSystems(unittest.TestCase):
    def test_sanity(self):

        systemA = System(components=[
            Component(name="a", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
            Component(name="unchanged", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
            Component(name="changed", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
        ])
        assert systemA.is_valid()
        systemB = System(components=[
            Component(name="unchanged", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")}),
            Component(name="changed", dependencies=[], qualifier=(), elements={"foo": Atom("barbaz")}),
            Component(name="b", dependencies=[], qualifier=(), elements={"foo": Atom("barbaz")}),
        ])
        assert systemB.is_valid()
        diffed = systemA.diff(systemB)
        applied = systemA.apply(diffed)
        assert applied == systemB


if __name__ == "__main__":
    unittest.main()
