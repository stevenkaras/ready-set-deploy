from itertools import chain
from typing import Any
from collections.abc import Iterable
import pathlib

import tomli

from ready_set_deploy.registry import ProviderRegistry


DEFAULT_CONFIG_PATHS: list[str] = [
    "~/.config/rsd/config.toml",
    "./rsd.toml",
]


def load_config(configpaths: list[str] = []) -> dict[str, str]:
    def _load_configfile(path: pathlib.Path):
        with open(path, mode="rb") as f:
            return tomli.load(f)

    default_paths = [
        path
        for path in [
            pathlib.Path(path).expanduser()
            for path in DEFAULT_CONFIG_PATHS
        ]
        if path.exists()
    ]
    user_paths = [
        pathlib.Path(path).expanduser()
        for path in configpaths
    ]

    configs = [
        _load_configfile(path)
        for path in default_paths + user_paths
    ]

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
    for key in chain.from_iterable(flattened):
        values = [flat[key] for flat in flattened if key in flat]
        result[key] = values[-1]

    return result

def load_registry_from_config(configpaths: list[str] = []) -> ProviderRegistry:
    merged_config = load_config(configpaths)

    return ProviderRegistry.from_dict(merged_config)
