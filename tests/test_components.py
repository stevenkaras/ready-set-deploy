import unittest

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom


class TestComponent(unittest.TestCase):
    def test_sanity(self):
        cfoo1 = Component(name="foo", dependencies=[], qualifier=[], elements={"foo": Atom("foobar")})
        cfoo2 = Component(name="foo", dependencies=[], qualifier=[], elements={"foo": Atom("foobaz")})
        diffed = cfoo1.diff(cfoo2)
        applied = cfoo1.apply(diffed)
        assert applied == cfoo2

    def test_empty_validity(self):
        empty = Component(name="empty", dependencies=[], qualifier=[], elements={})
        assert empty.is_partial()
        assert empty.is_full()
        assert empty.is_valid()

    def test_zerodiffapply(self):
        cfoo1 = Component(name="foo", dependencies=[], qualifier=[], elements={"foo": Atom("foobar")})
        diffed = cfoo1.zerodiff()
        applied = diffed.zeroapply()
        assert applied == cfoo1

    def test_copy(self):
        cfoo1 = Component(name="foo", dependencies=[], qualifier=[], elements={"foo": Atom("foobar")})
        copied = cfoo1.copy()
        assert copied == cfoo1


if __name__ == "__main__":
    unittest.main()
