"""
Holistic homebrew RSD provider

This provider handles all aspects of the homebrew packaging system
"""

from collections.abc import Iterable, Sequence
from typing import Optional

from ready_set_deploy.model import SubsystemState
from ready_set_deploy.runner import Runner
from ready_set_deploy.providers.base import Provider
from ready_set_deploy.providers.generic import GenericProviderMixin

_Elements = tuple[set, set, set]


class HomebrewProvider(GenericProviderMixin[_Elements], Provider):
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

    def diff_left_only(self, left: _Elements, right: _Elements) -> _Elements:
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

    def to_commands(self, desired: Optional[SubsystemState], undesired: Optional[SubsystemState]) -> Iterable[Sequence[str]]:
        desired_elements = [[], [], []] if desired is None else desired.elements
        desired_taps, desired_formulas, desired_casks = self.convert_elements(desired_elements)
        yield from Runner.to_commands("brew tap".split(), desired_taps)
        yield from Runner.to_commands("brew install".split(), desired_formulas)
        yield from Runner.to_commands("brew install --cask".split(), desired_casks)

        undesired_elements = [[], [], []] if undesired is None else undesired.elements
        undesired_taps, undesired_formulas, undesired_casks = self.convert_elements(undesired_elements)
        yield from Runner.to_commands("brew untap".split(), undesired_taps)
        yield from Runner.to_commands("brew uninstall".split(), undesired_formulas)
        yield from Runner.to_commands("brew uninstall --cask".split(), undesired_casks)
