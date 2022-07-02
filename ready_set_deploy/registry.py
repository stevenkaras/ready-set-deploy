import logging
import importlib
from typing import TypeVar, Generic, Union
from collections.abc import Iterable, Sequence
from ready_set_deploy.components import Component
from ready_set_deploy.gatherers.base import Gatherer

from ready_set_deploy.renderers.base import Renderer

log = logging.getLogger(__name__)


_V = TypeVar("_V")


class _Registry(Generic[_V]):
    def __init__(self):
        self._loaded_handlers: dict[str, _V] = {}
        self._unloaded_handlers: dict[str, str] = {}

    @classmethod
    def from_dict(cls, config: dict[str, str]):
        registry = cls()
        for name, handler in config.items():
            registry.deferred_register(name, handler)

        return registry

    def deferred_register(self, name: str, handlerclass: str):
        self._unloaded_handlers[name] = handlerclass

    def register(self, name: str, handler: _V):
        self._loaded_handlers[name] = handler

    def _load_handler(self, handlerclass) -> _V:
        package_name, class_name = handlerclass.rsplit(".", maxsplit=1)
        module = importlib.import_module(package_name)
        handler_class = getattr(module, class_name)
        handler = handler_class()
        return handler

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

    def __repr__(self):
        return str(self)


class GathererRegistry(_Registry[Gatherer]):
    def empty(self, name: str) -> Component:
        return self.get(name).empty()

    def gather_local(self, name: str, *, qualifier: tuple[str, ...] = ()) -> Iterable[Component]:
        return self.get(name).gather_local(qualifier=qualifier)


class RendererRegistry(_Registry[Renderer]):
    def to_commands(self, name: str, diff: Component) -> Iterable[Sequence[str]]:
        return self.get(name).to_commands(diff)
