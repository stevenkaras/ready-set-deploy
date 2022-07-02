"""
Holistic asdf RSD provider

This provider handles all aspects of the asdf runtime packaging system

https://asdf-vm.com/
"""
from collections.abc import Iterable, Sequence
from typing import cast

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom, ListDiff, MapDiff, Set, SetDiff
from ready_set_deploy.renderers.base import Renderer
from ready_set_deploy.runner import Runner

RuntimeVersionsDiff = MapDiff[Set[Atom], SetDiff[Atom]]


class AsdfRenderer(Renderer):
    NAME = "packages.asdf"

    def to_commands(self, diff: Component, initial: Component) -> Iterable[Sequence[str]]:
        asdf_dir = cast(Atom, diff.elements["asdf_dir"]).value
        yield from self.render_file_diff(f"{asdf_dir}/asdf_updates_disabled", cast(ListDiff, diff.elements["asdf_updates_disabled"]))
        config_file_path = cast(Atom, diff.elements["asdf_config_path"]).value
        yield from self.render_file_diff(config_file_path, cast(ListDiff, diff.elements["asdfrc"]))
        tool_versions_filename = cast(Atom, diff.elements["default_tool_versions_filename"]).value
        yield from self.render_file_diff(f"~/{tool_versions_filename}", cast(ListDiff, diff.elements["global_tool_versions"]))

        versions = cast(RuntimeVersionsDiff, diff.elements["versions"])
        for plugin in sorted(versions.keys_to_remove):
            yield from Runner.to_commands("asdf plugin remove".split(), [plugin.value])
        for plugin, _ in sorted(versions.items_to_add):
            yield from Runner.to_commands("asdf plugin add".split(), [plugin.value])

        for plugin, addversions in sorted(versions.items_to_add):
            for version in sorted(addversions):
                yield from Runner.to_commands(f"asdf install {plugin.value}".split(), [version.value])

        for plugin, versiondiff in sorted(versions.items_to_set):
            for version in sorted(versiondiff.to_add):
                yield from Runner.to_commands(f"asdf install {plugin.value}".split(), [version.value])
            for version in sorted(versiondiff.to_remove):
                yield from Runner.to_commands(f"asdf uninstall {plugin.value}".split(), [version.value])


if __name__ == "__main__":
    from ready_set_deploy.testing import find_and_run_unittests

    find_and_run_unittests(__file__)
