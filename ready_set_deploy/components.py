import dataclasses
from typing import cast, Union

from ready_set_deploy.elements import DiffElement, FullElement


Elements = Union[DiffElement, FullElement]


@dataclasses.dataclass
class Component:
    name: str
    dependencies: list[tuple[str, tuple[str, ...]]] = dataclasses.field(default_factory=list)
    qualifier: tuple[str, ...] = dataclasses.field(default_factory=tuple)
    elements: dict[str, Elements] = dataclasses.field(default_factory=dict)

    def to_primitive(self) -> dict:
        return {
            "name": self.name,
            "dependencies": [[name, [segment for segment in qualifier]] for name, qualifier in self.dependencies],
            "qualifier": [*self.qualifier],
            "elements": {name: element.to_primitive() for name, element in self.elements.items()},
        }

    @classmethod
    def from_primitive(cls, primitive: dict, *, is_diff: bool) -> "Component":
        elements: dict[str, Elements]
        if is_diff:
            elements = {name: DiffElement.from_primitive(element) for name, element in primitive["elements"].items()}
        else:
            elements = {name: FullElement.from_primitive(element) for name, element in primitive["elements"].items()}

        return cls(
            name=primitive["name"],
            dependencies=[(name, tuple(qualifier)) for name, qualifier in primitive["dependencies"]],
            qualifier=tuple(primitive["qualifier"]),
            elements=elements,
        )

    @property
    def dependency_key(self) -> tuple[str, tuple[str, ...]]:
        return (self.name, self.qualifier)

    def is_diff(self) -> bool:
        return all(isinstance(element, DiffElement) for element in self.elements.values())

    def is_full(self) -> bool:
        return all(isinstance(element, FullElement) for element in self.elements.values())

    def is_valid(self) -> bool:
        return self.is_diff() ^ self.is_full() or not self.elements

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
            raise ValueError(f"Cannot diff diff-components")

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
        if not self.is_full() or not other.is_diff():
            raise ValueError(f"Cannot only apply diff components to full components")

        self_elements = cast(dict[str, FullElement], self.elements)
        other_elements = cast(dict[str, DiffElement], other.elements)
        new_elements: dict[str, Elements] = {key: self_elements[key].apply(other_elements[key]) for key in self_elements.keys()}

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
    from typing import Iterable
    import pathlib

    def find_test_files(filename: str) -> Iterable[pathlib.Path]:
        file = pathlib.Path(filename)
        pattern = f"test_{file.stem}.py"
        root = file.parent
        while root.parent != root:
            testdirs = [child for child in root.iterdir() if child.is_dir() and child.name in ("test", "tests")]
            for testdir in testdirs:
                yield from testdir.rglob(pattern)

            root = root.parent

    import unittest

    for testfile in find_test_files(__file__):
        tests = unittest.defaultTestLoader.discover(str(testfile.parent), pattern=testfile.name)
        runner = unittest.TextTestRunner()
        results = runner.run(tests)
