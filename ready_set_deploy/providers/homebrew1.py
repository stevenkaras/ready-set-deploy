"""
This is a partially done homebrew provider that only considers formulas
"""

from collections.abc import Iterable, Sequence
from typing import Optional

from ready_set_deploy.model import SubsystemState
from ready_set_deploy.providers.base import Provider, Runner
from ready_set_deploy.providers.multiversion_packages import MultiversionPackageManagerMixin


class HomebrewPackagesProvider(MultiversionPackageManagerMixin, Provider):
    STATE_TYPE = "packages.homebrew.formulas"

    def gather_local(self, previous_state: Optional[SubsystemState] = None) -> SubsystemState:
        packages = self.gather_requested_packages()
        versions = self.gather_versions(packages)
        return SubsystemState(
            name=self.STATE_TYPE,
            elements=list(versions.items()),
        )

    def gather_requested_packages(self) -> list[str]:
        command = "brew leaves --installed-on-request".split()
        return [package for package in Runner.lines(command)]

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
