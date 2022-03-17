from typing import Optional
from collections.abc import Iterable, Sequence
from ready_set_deploy.model import SubsystemState


class Provider:
    def gather_local(self, *, qualifier: Optional[str] = None, previous_state: Optional[SubsystemState] = None) -> SubsystemState:
        raise NotImplementedError("gather_local")

    def diff(self, actual: SubsystemState, goal: SubsystemState) -> tuple[SubsystemState, SubsystemState]:
        """
        compute the desired and undesired partial states that would change actual to goal
        """
        raise NotImplementedError("diff")

    def combine(self, states: Iterable[SubsystemState]) -> Iterable[SubsystemState]:
        raise NotImplementedError("combine")

    def to_commands(self, desired: Optional[SubsystemState], undesired: Optional[SubsystemState]) -> Iterable[Sequence[str]]:
        raise NotImplementedError("to_commands")

    def is_valid(self, state: SubsystemState) -> Iterable[str]:
        raise NotImplementedError("is_valid")
