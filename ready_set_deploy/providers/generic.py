"""
Holistic homebrew RSD provider

This provider hadnle
"""

from collections.abc import Iterable, Sequence
from typing import Generic, TypeVar

from ready_set_deploy.model import SubsystemState

_InternalElements = TypeVar("_InternalElements")


class GenericProviderMixin(Generic[_InternalElements]):
    STATE_TYPE: str = NotImplemented

    def convert_elements(self, elements: list) -> _InternalElements:
        raise NotImplementedError("convert_elements")

    def diff_left_only(self, left: _InternalElements, right: _InternalElements) -> _InternalElements:
        raise NotImplementedError("diff_left_only")

    def convert_elements_back(self, elements: _InternalElements) -> list:
        raise NotImplementedError("convert_elements_back")

    def diff(self, actual: SubsystemState, desired: SubsystemState) -> tuple[SubsystemState, SubsystemState]:
        # compute the diff that would transform actual into desired
        assert not actual.is_partial
        assert not desired.is_partial
        assert actual.is_desired
        assert desired.is_desired
        assert actual.qualifier == desired.qualifier

        actual_packages = self.convert_elements(actual.elements)
        desired_packages = self.convert_elements(desired.elements)

        to_add = self.diff_left_only(desired_packages, actual_packages)
        to_remove = self.diff_left_only(actual_packages, desired_packages)

        return SubsystemState(
            name=self.STATE_TYPE,
            is_partial=True,
            elements=self.convert_elements_back(to_add),
        ), SubsystemState(
            name=self.STATE_TYPE,
            is_desired=False,
            is_partial=True,
            elements=self.convert_elements_back(to_remove),
        )

    def apply_partial_to_full(self, left: SubsystemState, partial: SubsystemState) -> SubsystemState:
        raise NotImplementedError("apply_partial_to_full")

    def to_commands(self, state: SubsystemState) -> Iterable[Sequence[str]]:
        raise NotImplementedError("to_commands")
