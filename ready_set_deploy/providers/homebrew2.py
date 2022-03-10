"""
Holistic homebrew RSD provider

This provider handles all aspects of the homebrew packaging system
"""

from collections.abc import Iterable, Sequence
from typing import Optional

from ready_set_deploy.model import SubsystemState
from ready_set_deploy.providers.base import Provider, Runner
from ready_set_deploy.providers.generic import GenericProviderMixin

_Elements = tuple[set, set, set]


class HomebrewPackagesProvider(Provider, GenericProviderMixin[_Elements]):
    STATE_TYPE = "packages.homebrew"

    @property
    def TAPS_STATE_TYPE(self):
        return f"{self.STATE_TYPE}.taps"

    @property
    def FORMULAS_STATE_TYPE(self):
        return f"{self.STATE_TYPE}.formulas"

    @property
    def CASKS_STATE_TYPE(self):
        return f"{self.STATE_TYPE}.casks"

    def gather_local(self, previous_state: Optional[SubsystemState] = None) -> SubsystemState:
        command = "brew tap".split()
        info = Runner.lines(command)
        taps = list(info)

        command = "brew info --json=v2 --installed".split()
        info = Runner.json(command)

        casks = [self._parse_cask(cask_info) for cask_info in info["casks"]]
        formulas = [self._parse_formula(formula_info) for formula_info in info["formulae"]]

        return SubsystemState(
            name=self.STATE_TYPE,
            elements=[
                taps,
                casks,
                formulas,
            ],
        )

    def _parse_cask(self, cask_info):
        return {
            "name": cask_info["full_token"],
        }

    def _parse_formula(self, formula_info):
        return {
            "name": formula_info["full_name"],
        }

    def convert_elements(self, elements: list) -> _Elements:
        raw_taps, raw_formulas, raw_casks = elements
        taps = set(raw_taps)
        formulas = set(formula["name"] for formula in raw_formulas)
        casks = set(cask["name"] for cask in raw_casks)
        return taps, formulas, casks

    def convert_elements_back(self, elements: _Elements) -> list:
        taps, formulas, casks = elements
        return [
            list(taps),
            [{"name": formula} for formula in formulas],
            [{"name": cask} for cask in casks],
        ]

    def diff_packages_leftside(self, left: _Elements, right: _Elements) -> _Elements:
        left_taps, left_formulas, left_casks = left
        right_taps, right_formulas, right_casks = right

        taps = left_taps - right_taps
        formulas = left_formulas - right_formulas
        casks = left_casks - right_casks

        return taps, formulas, casks

    def add_elements(self, left: _Elements, partial: _Elements) -> _Elements:
        left_taps, left_formulas, left_casks = left
        partial_taps, partial_formulas, partial_casks = partial

        taps = left_taps | partial_taps
        formulas = left_formulas | partial_formulas
        casks = left_casks | partial_casks

        return taps, formulas, casks

    def remove_elements(self, left: _Elements, partial: _Elements) -> _Elements:
        left_taps, left_formulas, left_casks = left
        partial_taps, partial_formulas, partial_casks = partial

        taps = left_taps - partial_taps
        formulas = left_formulas - partial_formulas
        casks = left_casks - partial_casks

        return taps, formulas, casks

    def apply_partial_to_full(self, left: SubsystemState, partial: SubsystemState) -> SubsystemState:
        assert left.is_desired
        assert partial.is_partial

        left_packages = self.convert_elements(left.elements)
        partial_packages = self.convert_elements(partial.elements)

        if partial.is_desired:
            combined = self.add_elements(left_packages, partial_packages)
        else:
            combined = self.remove_elements(left_packages, partial_packages)

        return SubsystemState(
            name=self.STATE_TYPE,
            elements=self.convert_elements_back(combined),
        )

    def to_commands(self, state: SubsystemState) -> Iterable[Sequence[str]]:
        taps, formulas, casks = self.convert_elements(state.elements)
        yield from Runner.to_commands("brew tap".split(), taps)
        yield from Runner.to_commands("brew install".split(), formulas)
        yield from Runner.to_commands("brew install --cask".split(), casks)


def main():
    import logging

    logging.basicConfig(level=logging.DEBUG)
    provider = HomebrewPackagesProvider()
    print(provider.gather_local())


if __name__ == "__main__":
    main()
