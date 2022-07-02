"""
Holistic asdf RSD provider

This provider handles all aspects of the asdf runtime packaging system

https://asdf-vm.com/
"""
from collections.abc import Iterable, Sequence
from typing import cast
import logging

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom, AtomDiff, Map, MapDiff
from ready_set_deploy.renderers.base import Renderer
from ready_set_deploy.runner import Runner

log = logging.getLogger(__name__)

InstalledApplicationsDiff = MapDiff[Map[Atom, AtomDiff], MapDiff[Atom, AtomDiff]]


class PipxRenderer(Renderer):
    NAME = "packages.pipx"

    def to_commands(self, diff: Component, initial: Component) -> Iterable[Sequence[str]]:
        applications = cast(InstalledApplicationsDiff, diff.elements["applications"])
        for application in applications.keys_to_remove:
            yield from Runner.to_commands("pipx uninstall".split(), [application.value])
        for application, spec in sorted(applications.items_to_add):
            package_spec = spec[Atom("package_spec")].value
            version = spec[Atom("version")].value
            if "=" not in package_spec:
                package_spec = f"{package_spec}=={version}"
            else:
                log.warning("package spec %s may result in version other than %s being installed", package_spec, version)

            options = {
                "--pip-args": spec[Atom("pip_args")],
                "--suffix": spec[Atom("suffix")],
                "--python": spec[Atom("python_version")],
            }
            command = "pipx install".split()
            for option_name, option_value in options.items():
                command += [option_name, option_value]
            command += ["--include-deps"] if spec[Atom("include_deps")].value == "yes" else []

            yield command

        for application, spec in sorted(applications.items_to_set):
            changes = {key.value: value for key, value in spec.items_to_set}
            if "version" not in changes or len(changes) != 1:
                raise NotImplementedError("No support for changing application specs at the moment")
            version = changes["version"].value

            command = "pipx upgrade".split()
            command += ["--pip-args", f"{application.value}=={version}"]
            command += [application.value]

            yield command


if __name__ == "__main__":
    from ready_set_deploy.testing import find_and_run_unittests

    find_and_run_unittests(__file__)
