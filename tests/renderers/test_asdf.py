import unittest
import shlex

from ready_set_deploy.components import Component
from ready_set_deploy.renderers.asdf import AsdfRenderer


class TestAsdfRenderer(unittest.TestCase):
    def _build_components(self):
        asdf = Component.from_primitive(
            {
                "name": "packages.asdf",
                "dependencies": [],
                "qualifier": [],
                "elements": {
                    "asdf_config_path": "~/.asdfrc",
                    "asdf_dir": "~/bin/.asdf",
                    "asdf_updates_disabled": ["list"],
                    "asdfrc": ["list", "e", "legacy_version_file = yes"],
                    "default_tool_versions_filename": ".tool_versions",
                    "global_tool_versions": ["list", "e", "python 3.9.6\\n"],
                    "versions": {
                        "nodejs": ["set", "14.16.1", "16.1.0"],
                        "python": ["set", "3.9.6"],
                        "ruby": ["set", "2.4.8", "3.0.2"],
                        "terraform": ["set", "1.0.3"],
                    },
                },
            },
            is_diff=False,
        )
        asdf2 = Component.from_primitive(
            {
                "name": "packages.asdf",
                "dependencies": [],
                "qualifier": [],
                "elements": {
                    "asdf_config_path": "~/.asdfrc",
                    "asdf_dir": "~/bin/.asdf",
                    "asdf_updates_disabled": ["list", "e"],
                    "asdfrc": ["list"],
                    "default_tool_versions_filename": ".tool_versions",
                    "global_tool_versions": ["list", "e", "python 3.9.6\\n", "ruby 3.0.2\\n"],
                    "versions": {
                        "nodejs": ["set", "14.16.1", "16.1.0"],
                        "ruby": ["set", "2.4.9", "3.0.1", "3.0.2"],
                        "terraform": ["set", "1.0.4"],
                    },
                },
            },
            is_diff=False,
        )

        return asdf, asdf2

    def test_simple_case(self):
        asdf, asdf2 = self._build_components()
        diff = asdf.diff(asdf2)
        cs = AsdfRenderer().to_commands(diff, asdf)
        expected_commands = [
            ["touch", '"~/bin/.asdf/asdf_updates_disabled"'],
            ["rm", '"~/.asdfrc"'],
            ["rsd-patch", '"~/.tool_versions"', '[["=", 0, "python 3.9.6\\\\n", "python 3.9.6\\\\n"], ["+", 1, null, "ruby 3.0.2\\\\n"]]'],
            ["asdf", "plugin", "remove", "python"],
            ["asdf", "install", "ruby", "2.4.9"],
            ["asdf", "install", "ruby", "3.0.1"],
            ["asdf", "uninstall", "ruby", "2.4.8"],
            ["asdf", "install", "terraform", "1.0.4"],
            ["asdf", "uninstall", "terraform", "1.0.3"],
        ]
        for c, ec in zip(cs, expected_commands):
            assert c == ec, f"{c=} {ec=}"


if __name__ == "__main__":
    unittest.main()
