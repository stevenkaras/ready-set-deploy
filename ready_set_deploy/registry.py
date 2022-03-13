import logging
import importlib
from typing import Any, Optional, TypeVar, Generic, Union
from collections.abc import Iterable, Sequence

from ready_set_deploy.model import SubsystemState
from ready_set_deploy.providers.base import Provider

log = logging.getLogger(__name__)


_V = TypeVar("_V")


class _Registry(Generic[_V]):
    def __init__(self):
        self._loaded_handlers: dict[str, _V] = {}
        self._unloaded_handlers: dict[str, str] = {}

    @classmethod
    def from_dict(cls, config: dict[str, Any]):
        def _flatten_dict(d: dict[str, Any], current_path: list[str] = [], delimiter: str = ".") -> Iterable[tuple[str, str]]:
            for key, val in d.items():
                current_path.append(key)
                if isinstance(val, dict):
                    yield from _flatten_dict(val, current_path, delimiter)
                else:
                    yield delimiter.join(current_path), val
                current_path.pop()
            return d.items()

        registry = cls()
        for name, handler in _flatten_dict(config):
            registry.deferred_register(name, handler)

        return registry

    def deferred_register(self, name: str, handlerclass: str):
        self._unloaded_handlers[name] = handlerclass

    def _load_handler(self, handlerclass) -> _V:
        package_name, class_name = handlerclass.rsplit(".", maxsplit=1)
        module = importlib.import_module(package_name)
        handler_class = getattr(module, class_name)
        handler = handler_class()
        return handler

    def register(self, name: str, handler: _V):
        self._loaded_handlers[name] = handler

    def all(self) -> Iterable[str]:
        return list(self._loaded_handlers.keys()) + list(self._unloaded_handlers.keys())

    def get(self, name: str) -> _V:
        handler = self._loaded_handlers.get(name)
        if handler is None:
            handlerclass = self._unloaded_handlers.pop(name)
            handler = self._load_handler(handlerclass)
            self._loaded_handlers[name] = handler
        return handler

    def __str__(self):
        handlers: dict[str, Union[str, _V]] = {name: handler for name, handler in self._loaded_handlers.items()}
        for name, handlerclass in self._unloaded_handlers.items():
            handlers[name] = f"U-{handlerclass}"

        return f"<{self.__class__.__name__} handlers={handlers}>"


class ProviderRegistry(_Registry[Provider]):
    def gather_local(self, name: str, previous_state: Optional[SubsystemState] = None) -> SubsystemState:
        return self.get(name).gather_local(previous_state)

    def diff(self, name: str, left: SubsystemState, right: SubsystemState) -> tuple[SubsystemState, SubsystemState]:
        return self.get(name).diff(left, right)

    def apply_partial_to_full(self, name: str, full: SubsystemState, partial: SubsystemState) -> SubsystemState:
        return self.get(name).apply_partial_to_full(full, partial)

    def combine(self, name: str, states: Iterable[SubsystemState]) -> Iterable[SubsystemState]:
        return self.get(name).combine(states)

    def to_commands(self, name: str, desired: Optional[SubsystemState], undesired: Optional[SubsystemState]) -> Iterable[Sequence[str]]:
        return self.get(name).to_commands(desired, undesired)

    def is_valid(self, name: str, state: SubsystemState) -> Iterable[str]:
        return self.get(name).is_valid(state)
