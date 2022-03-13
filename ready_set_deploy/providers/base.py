from typing import Optional
from collections.abc import Iterable, Sequence
from ready_set_deploy.model import SubsystemState


class Provider:
    def gather_local(self, previous_state: Optional[SubsystemState] = None) -> SubsystemState:
        raise NotImplementedError("gather_local")

    def diff(self, left: SubsystemState, right: SubsystemState) -> tuple[SubsystemState, SubsystemState]:
        raise NotImplementedError("diff")

    def apply_partial_to_full(self, left: SubsystemState, partial: SubsystemState) -> SubsystemState:
        raise NotImplementedError("apply_partial_to_full")

    def combine(self, states: Iterable[SubsystemState]) -> Iterable[SubsystemState]:
        raise NotImplementedError("combine")

    def to_commands(self, desired: Optional[SubsystemState], undesired: Optional[SubsystemState]) -> Iterable[Sequence[str]]:
        raise NotImplementedError("to_commands")

    def is_valid(self, state: SubsystemState) -> Iterable[str]:
        raise NotImplementedError("is_valid")
