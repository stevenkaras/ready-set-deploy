from pathlib import Path

from ready_set_deploy.components import Component
from ready_set_deploy.elements import List


class Gatherer:
    def empty(self) -> Component:
        """
        Returns an empty component in the shape of this provider (that is, with empty elements with the correct names and types)
        """
        raise NotImplementedError("empty")

    def gather_local(self, *, qualifier: tuple[str, ...] = ()) -> Component:
        raise NotImplementedError("gather_local")

    def gather_file(self, path: str) -> List:
        """
        Gather a file into a List with a prefix marker if the file exists

        See the corresponding render_file_diff in the Renderer base class
        """
        fullpath = Path(path).expanduser()
        if not fullpath.exists():
            return List.zero()
        else:
            with open(fullpath, mode="r") as f:
                return List.infer(["e"] + f.readlines())
