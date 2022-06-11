from itertools import chain
from typing import Any
from collections.abc import Iterable
import dataclasses
import os
import pathlib

import tomli

from ready_set_deploy.registry import GathererRegistry, RendererRegistry

DEFAULT_CONFIG_PATHS: list[str] = [
    "~/.config/rsd/config.toml",
    "./rsd.toml",
]
BUILTIN_CONFIG = {
    "gather.packages.homebrew": "ready_set_deploy.gatherers.homebrew.HomebrewGatherer",
    "render.packages.homebrew": "ready_set_deploy.renderers.homebrew.HomebrewRenderer",
}


def load_config(configpaths: list[str] = []) -> dict[str, str]:
    def _load_configfile(path: pathlib.Path):
        with open(path, mode="rb") as f:
            return tomli.load(f)

    default_paths = [path for path in [pathlib.Path(os.path.expandvars(path)).expanduser() for path in DEFAULT_CONFIG_PATHS] if path.exists()]
    user_paths = [pathlib.Path(os.path.expandvars(path)).expanduser() for path in configpaths]

    configs = [_load_configfile(path) for path in default_paths + user_paths]
    configs.insert(0, BUILTIN_CONFIG)

    return _merge_configs(*configs)


def _merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    # flatten the configs first
    def _flatten_dict(d: dict[str, Any], current_path: list[str] = [], delimiter: str = ".") -> Iterable[tuple[str, str]]:
        for key, val in d.items():
            current_path.append(key)
            if isinstance(val, dict):
                yield from _flatten_dict(val, current_path, delimiter)
            else:
                yield delimiter.join(current_path), val
            current_path.pop()

    flattened = [dict(_flatten_dict(config)) for config in configs]
    result = {}
    for key in set(chain.from_iterable(flattened)):
        values = [flat[key] for flat in flattened if key in flat]
        result[key] = values[-1]

    return result


@dataclasses.dataclass
class Config:
    gatherers: GathererRegistry
    renderers: RendererRegistry

    @classmethod
    def load_from_files(cls, configpaths: list[str] = []) -> "Config":
        merged_config = load_config(configpaths)
        gather_config = {k.removeprefix("gather."): v for k, v in merged_config.items() if k.startswith("gather.")}
        render_config = {k.removeprefix("render."): v for k, v in merged_config.items() if k.startswith("render.")}
        return cls(
            gatherers=GathererRegistry.from_dict(gather_config),
            renderers=RendererRegistry.from_dict(render_config),
        )
