"""
This is a partially done homebrew provider that only considers formulas
"""

from collections.abc import Iterable, Sequence

from ready_set_deploy.model import SubsystemState
from ready_set_deploy.plugins.base import MultiversionPackageManagerMixin, Provider, Runner

class HomebrewPackagesProvider(MultiversionPackageManagerMixin, Provider):
    STATE_TYPE = "packages.homebrew.formulas"

    def gather_local(self) -> SubsystemState:
        packages = self.gather_requested_packages()
        versions = self.gather_versions(packages)
        return SubsystemState(
            name=self.STATE_TYPE,
            elements=list(versions.items()),
        )

    def gather_requested_packages(self) -> list[str]:
        command = "brew leaves --installed-on-request".split()
        return [
            package
            for package in Runner.lines(command)
        ]

    def gather_versions(self, packages: list[str]) -> dict[str, list[str]]:
        command = "brew list --formulae --versions --".split()
        versions = {}
        for line in Runner.lines(command, packages):
            package, version = line.split(maxsplit=1)
            versions[package] = [version]

        return versions

    def to_commands(self, state: SubsystemState) -> Iterable[Sequence[str]]:
        packages = self._elements_to_multiversions(state.elements)
        command = "brew install".split()
        return Runner.to_commands(command, packages.keys())


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    provider = HomebrewPackagesProvider()
    # state = provider.gather_local()
    # print(provider._elements_to_multiversions(state.elements))

    left = {'leftonly': set(['1']), 'mixed': set(['1', '2']), 'shared': set(['1']), 'changed': set(['1'])}
    right = {'rightonly': set(['1']), 'mixed': set(['2', '3']), 'shared': set(['1']), 'changed': set(['2'])}
    left_state = SubsystemState(name=provider.STATE_TYPE, elements=provider._multiversions_to_elements(left))
    right_state = SubsystemState(name=provider.STATE_TYPE, elements=provider._multiversions_to_elements(right))
    print("Left state:")
    print(left_state)
    print("Right state:")
    print(right_state)

    print()
    to_add, to_remove = provider.diff(left_state, right_state)
    print("left -> right to add:")
    print(provider._diff_multiversion(right, left))  # {'rightonly': {'1'}, 'mixed': {'3'}, 'changed': {'2'}}
    print(to_add)

    print("left -> right to remove:")
    print(provider._diff_multiversion(left, right))  # {'leftonly': {'1'}, 'mixed': {'1'}, 'changed': {'1'}}
    print(to_remove)

    print()
    print("left + (right - left) = right")
    full_state = provider.apply_partial_to_full(provider.apply_partial_to_full(left_state, to_remove), to_add)
    print(right_state)
    print(full_state)


if __name__ == "__main__":
    main()
