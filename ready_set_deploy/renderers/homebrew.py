"""
Holistic homebrew RSD provider

This provider handles all aspects of the homebrew packaging system
"""

from collections.abc import Iterable, Sequence
from typing import cast

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom, AtomDiff, Map, MapDiff, SetDiff

from ready_set_deploy.renderers.base import Renderer
from ready_set_deploy.runner import Runner


AtomSetDiff = SetDiff[Atom]
PackageOptionsMapDiff = MapDiff[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]]


class HomebrewRenderer(Renderer):
    NAME = "packages.homebrew"

    def to_commands(self, diff: Component) -> Iterable[Sequence[str]]:
        taps = cast(AtomSetDiff, diff.elements["taps"])
        yield from Runner.to_commands("brew tap".split(), sorted([a.value for a in taps.to_add]))
        yield from Runner.to_commands("brew untap".split(), sorted([a.value for a in taps.to_remove]))

        formulas = cast(PackageOptionsMapDiff, diff.elements["formulas"])
        if formulas:
            print(formulas)
            raise NotImplementedError("no support for package options yet")
        simple_formulas = cast(AtomSetDiff, diff.elements["simple_formulas"])
        yield from Runner.to_commands("brew install".split(), sorted([a.value for a in simple_formulas.to_add]))
        yield from Runner.to_commands("brew uninstall".split(), sorted([k.value for k in simple_formulas.to_remove]))

        casks = cast(PackageOptionsMapDiff, diff.elements["casks"])
        if casks:
            raise NotImplementedError("no support for package options yet")
        simple_casks = cast(AtomSetDiff, diff.elements["simple_casks"])
        yield from Runner.to_commands("brew install --cask".split(), sorted([a.value for a in simple_casks.to_add]))
        yield from Runner.to_commands("brew uninstall --cask".split(), sorted([k.value for k in simple_casks.to_remove]))
