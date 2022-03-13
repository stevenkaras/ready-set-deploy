"""
Holistic homebrew RSD provider

This provider hadnle
"""

from collections.abc import Iterable
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

        desired_state = SubsystemState(
            name=self.STATE_TYPE,
            is_partial=True,
            elements=self.convert_elements_back(to_add),
        )
        undesired_state = SubsystemState(
            name=self.STATE_TYPE,
            is_desired=False,
            is_partial=True,
            elements=self.convert_elements_back(to_remove),
        )

        return desired_state, undesired_state

    def add_elements(self, left: _InternalElements, partial: _InternalElements) -> _InternalElements:
        raise NotImplementedError("add_elements")

    def remove_elements(self, left: _InternalElements, partial: _InternalElements) -> _InternalElements:
        raise NotImplementedError("remove_elements")

    def apply_partial_to_full(self, left: SubsystemState, partial: SubsystemState) -> SubsystemState:
        assert left.is_desired
        assert partial.is_partial

        left_packages = self.convert_elements(left.elements)
        partial_packages = self.convert_elements(partial.elements)

        if partial.is_desired:
            combined = self.add_elements(left_packages, partial_packages)
        else:
            combined = self.remove_elements(left_packages, partial_packages)

        return SubsystemState(
            name=self.STATE_TYPE,
            elements=self.convert_elements_back(combined),
        )

    def combine(self, states: Iterable[SubsystemState]) -> Iterable[SubsystemState]:
        desired_elements = None
        undesired_elements = None
        for state in states:
            elements = self.convert_elements(state.elements)
            if state.is_desired:
                if desired_elements is None:
                    desired_elements = elements

        return []
