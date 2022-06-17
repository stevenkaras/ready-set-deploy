import dataclasses
from typing import Iterator

from ready_set_deploy.components import Component
from ready_set_deploy.elements import AtomDiff


@dataclasses.dataclass
class System:
    components: list[Component] = dataclasses.field(default_factory=list)

    def to_primitive(self) -> dict:
        return {
            "components": [component.to_primitive() for component in sorted(self.components)],
            "version": "2",
            "is_diff": self.is_diff(),
        }

    @classmethod
    def from_primitive(cls, primitive: dict) -> "System":
        return cls(components=[Component.from_primitive(component, is_diff=primitive["is_diff"]) for component in primitive["components"]])

    def components_by_dependency(self):
        return {component.dependency_key: component for component in self.components}

    def is_diff(self) -> bool:
        return all(component.is_diff() for component in self.components)

    def is_full(self) -> bool:
        return all(component.is_full() for component in self.components)

    def is_valid(self) -> bool:
        components = self.components_by_dependency()
        return (
            all(component.is_valid() for component in self.components)
            and ((self.is_diff() ^ self.is_full()) or not self.components)
            and all(dependency in components for component in self.components for dependency in component.dependencies)
        )

    def __iter__(self) -> Iterator[Component]:
        components = self.components_by_dependency()
        while components:
            unblocked = [component for component in components.values() if all(dependency not in components for dependency in component.dependencies)]
            if not unblocked:
                raise ValueError("Circular dependency in system - invalid state")
            for component in sorted(unblocked):
                yield component
                components.pop(component.dependency_key)

    def _validate_compatible(self, other: "System") -> None:
        if not self.is_valid():
            raise ValueError("Incompatible systems - invalid systems")
        if not other.is_valid():
            raise ValueError("Incompatible systems - invalid systems")

    def diff(self, other: "System") -> "System":
        self._validate_compatible(other)
        if not self.is_full() or not other.is_full():
            raise ValueError(f"Cannot diff diff-systems")

        self_components = self.components_by_dependency()
        other_components = other.components_by_dependency()

        components_to_add = {
            component_key: component.zerodiff()
            for component_key in other_components.keys() - self_components.keys()
            for component in (other_components[component_key],)
        }
        # use a well known component to indicate it should be removed (and add a single diff element to indicate it's a diff component)
        components_to_remove = {
            component_key: Component(name="component.remove", dependencies=[], qualifier=(component.name, *component.qualifier), elements={"_": AtomDiff("")})
            for component_key in self_components.keys() - other_components.keys()
            for component in (self_components[component_key],)
        }
        components_to_apply = {
            component_key: self_components[component_key].diff(other_components[component_key])
            for component_key in other_components.keys() & self_components.keys()
            if self_components[component_key] != other_components[component_key]
        }

        new_components: list[Component] = []
        new_components += components_to_add.values()
        new_components += components_to_remove.values()
        new_components += components_to_apply.values()

        return System(components=new_components)

    def apply(self, other: "System") -> "System":
        self._validate_compatible(other)
        if not self.is_full() or not other.is_diff():
            raise ValueError(f"Cannot only apply diff components to full components")

        self_components = self.components_by_dependency()
        other_components = other.components_by_dependency()

        components_to_remove = set(
            [(component.qualifier[0], component.qualifier[1:]) for _, component in other_components.items() if component.name == "component.remove"]
        )
        new_components = {}
        for key, component in self_components.items():
            if key in components_to_remove:
                continue

            other_component = other_components.get(key)
            if other_component is None:
                new_components[key] = component.copy()
                continue

            new_components[key] = component.apply(other_component)

        for key, component in other_components.items():
            if key in new_components:
                continue
            if component.name == "component.remove":
                continue

            new_components[key] = component.zeroapply()

        return System(components=list(new_components.values()))

    def combine(self, other: "System") -> "System":
        self._validate_compatible(other)
        if not self.is_full() or not other.is_full():
            raise ValueError(f"Cannot combine diff-systems")

        self_components = self.components_by_dependency()
        other_components = other.components_by_dependency()

        new_components = {}
        for key, component in self_components.items():
            other_component = other_components.get(key)
            if other_component is None:
                new_components[key] = component.copy()
            else:
                new_components[key] = component.combine(other_component)

        for key, component in other_components.items():
            if key in new_components:
                continue

            new_components[key] = component.copy()

        return System(components=list(new_components.values()))

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, System):
            raise NotImplementedError(f"Cannot only compare {type(self)} to other {type(self)}, not {type(__o)}")

        return sorted(self.components) == sorted(__o.components)

    def __str__(self):
        return f"System(components={self.components})>"

    def __repr__(self):
        return str(self)


if __name__ == "__main__":
    from ready_set_deploy.testing import find_and_run_unittests

    find_and_run_unittests(__file__)
