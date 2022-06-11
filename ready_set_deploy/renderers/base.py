from collections.abc import Iterable, Sequence

from ready_set_deploy.components import Component


class Renderer:
    def to_commands(self, diff: Component) -> Iterable[Sequence[str]]:
        raise NotImplementedError("to_commands")
