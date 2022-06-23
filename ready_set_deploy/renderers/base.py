import json
import shlex
from collections.abc import Iterable, Sequence

from ready_set_deploy.components import Component
from ready_set_deploy.elements import Atom, List, ListDiff, ListDiffOpcode
from ready_set_deploy.runner import Runner


class Renderer:
    def to_commands(self, diff: Component) -> Iterable[Sequence[str]]:
        raise NotImplementedError("to_commands")

    def render_file_diff(self, filepath: str, spec: ListDiff) -> Iterable[Sequence[str]]:
        """
        Render the commands for a file diff produced by gather_file in the Gatherer base class
        """
        if not spec.diff:
            return

        raw_op, idx, lhs, rhs = spec.diff[0]
        op = ListDiffOpcode(raw_op)
        if idx == 0 and op == ListDiffOpcode.DELETE and lhs == "e":
            yield from Runner.to_commands(["rm", f"\"{filepath}\""])
            return

        if idx == 0 and op == ListDiffOpcode.INSERT and rhs == "e":
            yield from Runner.to_commands(["touch", f"\"{filepath}\""])

        if len(spec.diff) == 1:
            return

        # the first element ("e") is an existence marker, but it's not part of the file content, so we need to modify the diff manually
        new_spec = []
        for op, idx, lhs, rhs in spec.diff:
            if idx == 0:
                continue
            new_spec.append((op, idx - 1, lhs, rhs))
        fixed = ListDiff(diff=new_spec)

        json_diff = json.dumps(fixed.to_primitive())
        yield from Runner.to_commands(["rsd-patch", f"\"{filepath}\"", f"{json_diff}"])
