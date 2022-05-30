import dataclasses
from typing import Generic, cast, TypeVar

from ready_set_deploy.elements import DiffElement, FullElement


_E = TypeVar("_E", DiffElement, FullElement)


@dataclasses.dataclass
class Component(Generic[_E]):
    name: str
    dependencies: list[tuple[str, list[str]]] = dataclasses.field(default_factory=list)
    qualifier: list[str] = dataclasses.field(default_factory=list)
    elements: dict[str, _E] = dataclasses.field(default_factory=dict)

    @property
    def dependency_key(self):
        return (self.name, self.qualifier)

    def is_partial(self) -> bool:
        return all(isinstance(element, DiffElement) for element in self.elements.values())

    def is_full(self) -> bool:
        return all(isinstance(element, FullElement) for element in self.elements.values())

    def is_valid(self) -> bool:
        return self.is_partial() ^ self.is_full() or not self.elements

    def _validate_compatible(self, other: "Component") -> None:
        if not self.is_valid():
            raise ValueError("Incompatible components - invalid components")
        if not other.is_valid():
            raise ValueError("Incompatible components - invalid components")
        if self.name != other.name:
            raise ValueError(f"Incompatible component {self.name} with {other.name}")
        if self.qualifier != other.qualifier:
            raise ValueError(f"Incompatible component {self.name} with different qualifiers")
        if self.dependencies != other.dependencies:
            raise ValueError("Incompatible components - mismatched dependencies")
        if self.elements.keys() != other.elements.keys():
            raise ValueError("Incompatible components - mismatched elements")

    def diff(self, other: "Component") -> "Component":
        self._validate_compatible(other)
        if not self.is_full() or not other.is_full():
            raise ValueError(f"Cannot diff partial elements")

        self_elements = cast(dict[str, FullElement], self.elements)
        other_elements = cast(dict[str, FullElement], other.elements)
        new_elements = {key: self_elements[key].diff(other_elements[key]) for key in self_elements.keys()}

        return Component(
            name=self.name,
            dependencies=self.dependencies,
            qualifier=self.qualifier,
            elements=new_elements,
        )

    def zerodiff(self) -> "Component":
        return Component(
            name=self.name,
            dependencies=self.dependencies,
            qualifier=self.qualifier,
            elements={name: element.zero().diff(element) for name, element in cast(dict[str, FullElement], self.elements).items()},
        )

    def apply(self, other: "Component") -> "Component":
        self._validate_compatible(other)
        if not self.is_full() or not other.is_partial():
            raise ValueError(f"Cannot only apply partial components to full components")

        self_elements = cast(dict[str, FullElement], self.elements)
        other_elements = cast(dict[str, DiffElement], other.elements)
        new_elements = {key: self_elements[key].apply(other_elements[key]) for key in self_elements.keys()}

        return Component(
            name=self.name,
            dependencies=self.dependencies,
            qualifier=self.qualifier,
            elements=new_elements,
        )

    def zeroapply(self) -> "Component":
        return Component(
            name=self.name,
            dependencies=self.dependencies,
            qualifier=self.qualifier,
            elements={name: element.full_type().zero().apply(element) for name, element in cast(dict[str, DiffElement], self.elements).items()},
        )

    def copy(self) -> "Component":
        return Component(
            name=self.name,
            dependencies=self.dependencies,
            qualifier=self.qualifier,
            elements={name: element.copy() for name, element in self.elements.items()},
        )

    def __str__(self):
        qualifier = "" if not self.qualifier else f" {{{self.qualifier}}}"
        return f"<Component.{self.name}{qualifier} e={self.elements}>"

    def __repr__(self):
        return str(self)


if __name__ == "__main__":
    from ready_set_deploy.elements import Atom

    empty = Component(name="empty", dependencies=[], qualifier=[], elements={})
    assert empty.is_partial()
    assert empty.is_full()
    assert empty.is_valid()

    cfoo1 = Component(name="foo", dependencies=[], qualifier=[], elements={"foo": Atom("foobar")})
    cfoo2 = Component(name="foo", dependencies=[], qualifier=[], elements={"foo": Atom("foobaz")})
    diffed = cfoo1.diff(cfoo2)
    applied = cfoo1.apply(diffed)
    assert applied == cfoo2

    cfoo1 = Component(name="foo", dependencies=[], qualifier=[], elements={"foo": Atom("foobar")})
    diffed = cfoo1.zerodiff()
    applied = diffed.zeroapply()
    assert applied == cfoo1
