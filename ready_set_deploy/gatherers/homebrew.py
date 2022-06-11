"""
Holistic homebrew RSD provider

This provider handles all aspects of the homebrew packaging system
"""
from typing import cast

from ready_set_deploy.components import Component
from ready_set_deploy.elements import AtomDiff, Atom, Set, Map, MapDiff

from ready_set_deploy.runner import Runner
from ready_set_deploy.gatherers.base import Gatherer

AtomSet = Set[Atom]
PackageOptions = Map[Atom, AtomDiff]
PackageOptionsMap = Map[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]]


class HomebrewGatherer(Gatherer):
    PROVIDER_NAME = "packages.homebrew"

    def empty(self) -> Component:
        return Component(
            name=self.PROVIDER_NAME,
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
        info = Runner.lines(command)
        taps = list(sorted(info))

        command = "brew info --json=v2 --installed".split()
        info = Runner.json(command)
        casks = [self._parse_cask(cask_info) for cask_info in info["casks"]]
        formulas = [
            self._parse_formula(formula_info)
            for formula_info in info["formulae"]
            if any(install_info["installed_on_request"] for install_info in formula_info["installed"])
        ]

        component = self.empty()
        component_taps = cast(AtomSet, component.elements["taps"])
        for tap in taps:
            component_taps.add(Atom(tap))

        component_simple_formulas = cast(AtomSet, component.elements["simple_formulas"])
        for formula in formulas:
            if len(formula) > 1:
                continue

            component_simple_formulas.add(Atom(formula["name"]))

        component_formulas = cast(PackageOptionsMap, component.elements["formulas"])
        for formula in formulas:
            if len(formula) == 1:
                continue

            component_formulas[Atom(formula["name"])] = PackageOptions({Atom(option): Atom(value) for option, value in formula.items() if option != "name"})

        component_simple_casks = cast(AtomSet, component.elements["simple_casks"])
        for cask in casks:
            if len(cask) > 1:
                continue

            component_simple_casks.add(Atom(cask["name"]))

        component_casks = cast(PackageOptionsMap, component.elements["casks"])
        for cask in casks:
            if len(cask) == 1:
                continue

            component_casks[Atom(cask["name"])] = PackageOptions({Atom(option): Atom(value) for option, value in cask.items() if option != "name"})

        return component

    def _parse_cask(self, cask_info):
        return {
            "name": cask_info["full_token"],
        }

    def _parse_formula(self, formula_info):
        return {
            "name": formula_info["full_name"],
        }
