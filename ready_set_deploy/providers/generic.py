"""
Holistic homebrew RSD provider

This provider hadnle
"""

from collections.abc import Iterable
from typing import Generic, TypeVar

from ready_set_deploy.model import SubsystemState, SubsystemStateType

_InternalElements = TypeVar("_InternalElements")


class GenericProviderMixin(Generic[_InternalElements]):
    PROVIDER_NAME: str = NotImplemented

    def convert_elements(self, elements: list) -> _InternalElements:
        raise NotImplementedError("convert_elements")

    def diff_left_only(self, left: _InternalElements, right: _InternalElements) -> _InternalElements:
        raise NotImplementedError("diff_left_only")

    def convert_elements_back(self, elements: _InternalElements) -> list:
        raise NotImplementedError("convert_elements_back")

    def diff(self, actual: SubsystemState, desired: SubsystemState) -> tuple[SubsystemState, SubsystemState]:
        # compute the diff that would transform actual into desired
        assert actual.state_type == SubsystemStateType.FULL
        assert desired.state_type == SubsystemStateType.FULL
        assert actual.qualifier == desired.qualifier

        actual_packages = self.convert_elements(actual.elements)
        desired_packages = self.convert_elements(desired.elements)

        to_add = self.diff_left_only(desired_packages, actual_packages)
        to_remove = self.diff_left_only(actual_packages, desired_packages)

        desired_state = SubsystemState(
            name=self.PROVIDER_NAME,
            state_type=SubsystemStateType.DESIRED,
            elements=self.convert_elements_back(to_add),
        )
        undesired_state = SubsystemState(
            name=self.PROVIDER_NAME,
            state_type=SubsystemStateType.UNDESIRED,
            elements=self.convert_elements_back(to_remove),
        )

        return desired_state, undesired_state

    def add_elements(self, left: _InternalElements, partial: _InternalElements) -> _InternalElements:
        raise NotImplementedError("add_elements")

    def remove_elements(self, left: _InternalElements, partial: _InternalElements) -> _InternalElements:
        raise NotImplementedError("remove_elements")

    def apply_partial_to_full(self, full: SubsystemState, partial: SubsystemState) -> SubsystemState:
        assert full.state_type == SubsystemStateType.FULL
        assert partial.state_type != SubsystemStateType.FULL

        full_packages = self.convert_elements(full.elements)
        partial_packages = self.convert_elements(partial.elements)

        if partial.state_type == SubsystemStateType.DESIRED:
            combined = self.add_elements(full_packages, partial_packages)
        else:
            combined = self.remove_elements(full_packages, partial_packages)

        return SubsystemState(
            name=self.PROVIDER_NAME,
            state_type=SubsystemStateType.FULL,
            elements=self.convert_elements_back(combined),
        )

    def combine(self, states: Iterable[SubsystemState]) -> Iterable[SubsystemState]:
        # first, check if we have a full state to start from

        desired_elements = None
        undesired_elements = None
        for state in states:
            elements = self.convert_elements(state.elements)
            if state.state_type == SubsystemStateType.DESIRED:
                if desired_elements is None:
                    desired_elements = elements

        return []
