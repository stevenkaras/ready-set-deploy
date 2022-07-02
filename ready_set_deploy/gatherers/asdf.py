"""
Holistic asdf RSD provider

This provider handles all aspects of the asdf runtime packaging system

https://asdf-vm.com/
"""
import os
from collections.abc import Iterable

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom, List, Map, Set, SetDiff
from ready_set_deploy.gatherers.base import Gatherer
from ready_set_deploy.runner import Runner

RuntimeVersions = Map[Set[Atom], SetDiff[Atom]]


class AsdfGatherer(Gatherer):
    NAME = "packages.asdf"

    def empty(self) -> Component:
        return Component(
            name=self.NAME,
            elements={
                "versions": RuntimeVersions.zero(),
                "global_tool_versions": List.zero(),
                "asdfrc": List.zero(),
                "asdf_updates_disabled": List.zero(),
                # captured environment variables
                "asdf_dir": Atom.zero(),
                "default_tool_versions_filename": Atom.zero(),
                "asdf_config_path": Atom.zero(),
            },
        )

    def gather_local(self, *, qualifier: tuple[str, ...] = ()) -> Iterable[Component]:
        versions: dict[str, set[str]] = {}
        current_plugin = "INVALID PLUGIN"
        for line in Runner.lines("asdf list".split()):
            if not line.startswith(" "):
                current_plugin = line
                continue

            if line == "  No versions installed":
                versions[current_plugin] = set()
                continue

            versions.setdefault(current_plugin, set()).add(line.strip())

        tool_versions_filename = os.environ.get("ASDF_DEFAULT_TOOL_VERSIONS_FILENAME", ".tool_versions")
        global_versions = self.gather_file(f"~/{tool_versions_filename}")
        asdf_config_path = os.environ.get("ASDF_CONFIG_FILE", "~/.asdfrc")
        asdfrc = self.gather_file(asdf_config_path)
        asdf_dir = os.environ.get("ASDF_DIR", "~/.asdf")
        updates_disabled = self.gather_file(f"{asdf_dir}/asdf_updates_disabled")

        yield Component(
            name=self.NAME,
            elements={
                "versions": RuntimeVersions.infer(versions),
                "global_tool_versions": global_versions,
                "asdfrc": asdfrc,
                "asdf_updates_disabled": updates_disabled,
                "asdf_dir": Atom(asdf_dir),
                "default_tool_versions_filename": Atom(tool_versions_filename),
                "asdf_config_path": Atom(asdf_config_path),
            },
        )
