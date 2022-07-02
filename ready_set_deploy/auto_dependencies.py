from typing import Optional, cast

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom, AtomDiff, Map, MapDiff, Set
from ready_set_deploy.systems import System

CompenentDict = dict[tuple[str, tuple[str, ...]], Component]


def _check_homebrew_for_package(components: CompenentDict, formula_name: str) -> Optional[Component]:
    homebrew = components.get(("packages.homebrew", ()))

    if homebrew is not None:
        simple_formulas = cast(Set[Atom], homebrew.elements["simple_formulas"])
        if Atom(formula_name) in simple_formulas:
            return homebrew
        complex_formulas = cast(Map[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]], homebrew.elements["formulas"])
        if Atom(formula_name) in complex_formulas:
            return homebrew

    return None


def auto_mark_system_dependencies(system: System):
    components = system.components_by_dependency()
    _mark_asdf(components)
    _mark_pipx(components)


def _mark_pipx(components: CompenentDict):
    pipx = components.get(("packages.pipx", ()))
    if pipx is None:
        return
    source = _find_pipx_source(components)
    if source is None:
        return
    pipx.dependencies.append(source.dependency_key)


def _find_pipx_source(components: CompenentDict) -> Optional[Component]:
    homebrew = _check_homebrew_for_package(components, "pipx")
    if homebrew is not None:
        return homebrew


def _mark_asdf(components: CompenentDict):
    asdf = components.get(("packages.asdf", ()))
    if asdf is None:
        return
    source = _find_asdf_source(components)
    if source is None:
        return
    asdf.dependencies.append(source.dependency_key)


def _find_asdf_source(components: CompenentDict) -> Optional[Component]:
    homebrew = _check_homebrew_for_package(components, "asdf")
    if homebrew is not None:
        return homebrew
