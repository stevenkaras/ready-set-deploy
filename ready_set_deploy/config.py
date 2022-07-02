import logging.config
from itertools import chain
from typing import Any, Iterator
from collections.abc import Iterable
import dataclasses
import os
import pathlib

import tomli

from ready_set_deploy.registry import GathererRegistry, RendererRegistry

DEFAULT_CONFIG_PATHS: list[str] = [
    "${XDG_CONFIG_HOME}/rsd/config.toml",
    "./rsd.toml",
]
_DEFAULT_VARS = {
    "${XDG_CONFIG_HOME}": "~/.config",
}
BUILTIN_CONFIG = """
gather.packages.homebrew = "ready_set_deploy.gatherers.homebrew.HomebrewGatherer"
render.packages.homebrew = "ready_set_deploy.renderers.homebrew.HomebrewRenderer"
gather.packages.asdf = "ready_set_deploy.gatherers.asdf.AsdfGatherer"
render.packages.asdf = "ready_set_deploy.renderers.asdf.AsdfRenderer"
"""

DEFAULT_LOGGING_CONFIG_PATH: str = "${XDG_CONFIG_HOME}/rsd/logging.toml"
BUILTIN_LOGGING_CONFIG = """
version = 1
disable_existing_loggers = false

[formatters.default]
# python doesn't expose the msec as a strftime placeholder, but it's part of the record as a field
# from: https://stackoverflow.com/questions/6290739/python-logging-use-milliseconds-in-time-format
format = "%(asctime)s.%(msecs)03d:%(levelname)s:%(name)s::%(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"

[handlers.console]
class = "logging.StreamHandler"
level = "INFO"
formatter = "default"
stream = "ext://sys.stdout"

[loggers.root]
level = "INFO"
handlers = ["console"]
"""


def _resolve_config_path(configpaths: list[str]) -> Iterator[pathlib.Path]:
    for configpath in configpaths:
        resolved_path = os.path.expandvars(configpath)
        for var, value in _DEFAULT_VARS.items():
            resolved_path = resolved_path.replace(var, value)
        resolved_path = os.path.expanduser(resolved_path)
        yield pathlib.Path(resolved_path)


def _ensure_configs():
    # populate the default builtin configs
    config_folder = next(_resolve_config_path(["${XDG_CONFIG_HOME}/rsd"]))
    config_folder.mkdir(mode=0o755, parents=True, exist_ok=True)
    logging_config_path = next(_resolve_config_path([DEFAULT_LOGGING_CONFIG_PATH]))
    if not logging_config_path.exists():
        with open(logging_config_path, mode="w") as f:
            f.write(BUILTIN_LOGGING_CONFIG)

    rsd_config = next(_resolve_config_path([DEFAULT_CONFIG_PATHS[0]]))
    if not rsd_config.exists():
        with open(rsd_config, mode="w") as f:
            f.write(BUILTIN_CONFIG)


def _load_configfile(path: pathlib.Path):
    with open(path, mode="rb") as f:
        return tomli.load(f)


def setup_logging():
    _ensure_configs()
    logging_config_path = next(_resolve_config_path([DEFAULT_LOGGING_CONFIG_PATH]))
    logging.config.dictConfig(_load_configfile(logging_config_path))


def _load_config(configpaths: list[str] = []) -> dict[str, str]:
    _ensure_configs()
    default_paths = [path for path in _resolve_config_path(DEFAULT_CONFIG_PATHS) if path.exists()]
    user_paths = [pathlib.Path(os.path.expandvars(path)).expanduser() for path in configpaths]

    configs = [_load_configfile(path) for path in default_paths + user_paths]
    configs.insert(0, tomli.loads(BUILTIN_CONFIG))

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
        merged_config = _load_config(configpaths)
        gather_config = {k.removeprefix("gather."): v for k, v in merged_config.items() if k.startswith("gather.")}
        render_config = {k.removeprefix("render."): v for k, v in merged_config.items() if k.startswith("render.")}
        return cls(
            gatherers=GathererRegistry.from_dict(gather_config),
            renderers=RendererRegistry.from_dict(render_config),
        )
