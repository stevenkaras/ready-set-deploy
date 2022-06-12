"""
Holistic homebrew RSD provider

This provider handles all aspects of the homebrew packaging system
"""
from ready_set_deploy.components import Component
from ready_set_deploy.elements import AtomDiff, Atom, FullElement, Set, Map, MapDiff

from ready_set_deploy.runner import Runner
from ready_set_deploy.gatherers.base import Gatherer

AtomSet = Set[Atom]
PackageOptions = Map[Atom, AtomDiff]
PackageOptionsMap = Map[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]]


class HomebrewGatherer(Gatherer):
    NAME = "packages.homebrew"

    def empty(self) -> Component:
        return Component(
            name=self.NAME,
            elements={
                "taps": AtomSet.zero(),
                "simple_formulas": AtomSet.zero(),
                "formulas": PackageOptionsMap.zero(),
                "simple_casks": AtomSet.zero(),
                "casks": PackageOptionsMap.zero(),
            },
        )

    def gather_local(self, *, qualifier: tuple[str, ...] = ()) -> Component:
        command = "brew tap".split()
        taps = Runner.lines(command)

        command = "brew info --json=v2 --installed".split()
        info = Runner.json(command)
        casks = [self._parse_cask(cask_info) for cask_info in info["casks"]]
        formulas = [
            self._parse_formula(formula_info)
            for formula_info in info["formulae"]
            if any(install_info["installed_on_request"] for install_info in formula_info["installed"])
        ]
        simple_formulas = [formula for formula in formulas if len(formula) == 1]
        complex_formulas = [formula for formula in formulas if len(formula) > 1]
        simple_casks = [cask for cask in casks if len(cask) == 1]
        complex_casks = [cask for cask in casks if len(cask) > 1]

        return Component(
            name=self.NAME,
            elements={
                "taps": FullElement.infer(set(taps)),
                "simple_formulas": FullElement.infer(set(formula["name"] for formula in simple_formulas)),
                "formulas": FullElement.infer(
                    {formula["name"]: {option: value for option, value in formula if option != "name"} for formula in complex_formulas}
                ),
                "simple_casks": FullElement.infer(set(cask["name"] for cask in simple_casks)),
                "casks": FullElement.infer({cask["name"]: {option: value for option, value in cask if option != "name"} for cask in complex_casks}),
            },
        )

    def _parse_cask(self, cask_info):
        return {
            "name": cask_info["full_token"],
        }

    def _parse_formula(self, formula_info):
        return {
            "name": formula_info["full_name"],
        }
