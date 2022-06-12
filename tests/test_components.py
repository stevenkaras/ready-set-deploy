import unittest

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom


class TestComponent(unittest.TestCase):
    def test_sanity(self):
        cfoo1 = Component(name="foo", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")})
        cfoo2 = Component(name="foo", dependencies=[], qualifier=(), elements={"foo": Atom("foobaz")})
        diffed = cfoo1.diff(cfoo2)
        applied = cfoo1.apply(diffed)
        assert applied == cfoo2

    def test_combine(self):
        cfoo1 = Component(name="foo", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")})
        cfoo2 = Component(name="foo", dependencies=[], qualifier=(), elements={"foo": Atom("foobaz")})
        combined = cfoo1.combine(cfoo2)
        assert combined == cfoo2

    def test_empty_validity(self):
        empty = Component(name="empty", dependencies=[], qualifier=(), elements={})
        assert empty.is_diff()
        assert empty.is_full()
        assert empty.is_valid()

    def test_zerodiffapply(self):
        cfoo1 = Component(name="foo", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")})
        diffed = cfoo1.zerodiff()
        applied = diffed.zeroapply()
        assert applied == cfoo1

    def test_copy(self):
        cfoo1 = Component(name="foo", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")})
        copied = cfoo1.copy()
        assert copied == cfoo1

    def test_serialize(self):
        componentA = Component(name="foo", dependencies=[], qualifier=(), elements={"foo": Atom("foobar")})
        componentB = Component(name="foo", dependencies=[], qualifier=(), elements={"foo": Atom("foobaz")})
        diffed = componentA.diff(componentB)

        serialized = componentA.to_primitive()
        roundtripped = Component.from_primitive(serialized, is_diff=False)
        assert componentA == roundtripped

        serialized = diffed.to_primitive()
        roundtripped = Component.from_primitive(serialized, is_diff=True)
        assert diffed == roundtripped


if __name__ == "__main__":
    unittest.main()
