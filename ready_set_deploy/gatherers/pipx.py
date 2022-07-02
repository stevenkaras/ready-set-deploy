"""
Holistic pipx RSD provider

This provider handles all aspects of the pipx application packaging system
"""
from collections.abc import Iterable

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom, AtomDiff, Map, MapDiff
from ready_set_deploy.gatherers.base import Gatherer
from ready_set_deploy.runner import Runner

InstalledApplications = Map[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]]


class PipxGatherer(Gatherer):
    NAME = "packages.pipx"

    def empty(self) -> Component:
        return Component(
            name=self.NAME,
            elements={
                "applications": InstalledApplications.zero(),
            },
        )

    def gather_application_from_spec(self, venv_spec: dict) -> dict[str, str]:
        metadata = venv_spec["metadata"]
        main_package = metadata["main_package"]
        package_spec = main_package["package_or_url"]
        version = main_package["package_version"]
        pip_args = main_package["pip_args"]
        suffix = main_package["suffix"]
        python_version = metadata["python_version"]
        include_deps = "yes" if main_package["include_dependencies"] else "no"
        return {
            "package_spec": package_spec,
            "version": version,
            "pip_args": pip_args,
            "suffix": suffix,
            "python_version": python_version,
            "include_deps": include_deps,
        }

    def gather_from_spec(self, spec: dict) -> dict[str, dict[str, str]]:
        applications: dict[str, dict[str, str]] = {}

        for venv_name, venv_spec in spec["venvs"].items():
            applications[venv_name] = self.gather_application_from_spec(venv_spec)

        return applications

    def gather_local(self, *, qualifier: tuple[str, ...] = ()) -> Iterable[Component]:
        spec = Runner.json("pipx list --json".split())
        applications = self.gather_from_spec(spec)

        yield Component(
            name=self.NAME,
            elements={
                "applications": InstalledApplications.infer(applications),
            },
        )
