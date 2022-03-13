"""
Holistic homebrew RSD provider

This provider hadnle
"""
from functools import reduce
from collections.abc import Iterable
from typing import Generic, TypeVar, cast
from ready_set_deploy.itertools import bucketdict

from ready_set_deploy.model import SubsystemState, SubsystemStateType

_InternalElements = TypeVar("_InternalElements")


class GenericProviderMixin(Generic[_InternalElements]):
    PROVIDER_NAME: str = NotImplemented

    def convert_elements(self, elements: list) -> _InternalElements:
        raise NotImplementedError("convert_elements")

    def convert_elements_back(self, elements: _InternalElements) -> list:
        raise NotImplementedError("convert_elements_back")

    def diff_left_only(self, left: _InternalElements, right: _InternalElements) -> _InternalElements:
        raise NotImplementedError("diff_left_only")

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

    def add_elements(self, left: _InternalElements, right: _InternalElements) -> _InternalElements:
        raise NotImplementedError("add_elements")

    def remove_elements(self, left: _InternalElements, right: _InternalElements) -> _InternalElements:
        raise NotImplementedError("remove_elements")

    def combine(self, states: Iterable[SubsystemState]) -> Iterable[SubsystemState]:
        # first, combine all the desired and undesired states
        # then check if we have a full state and apply them to it

        states_by_type = bucketdict(states, key=lambda s: s.state_type)

        _empty = object()
        desired_elements = [self.convert_elements(state.elements) for state in states_by_type.get(SubsystemStateType.DESIRED, [])]
        if desired_elements:
            combined_desired = reduce(self.add_elements, desired_elements)
        else:
            combined_desired = _empty
        undesired_elements = [self.convert_elements(state.elements) for state in states_by_type.get(SubsystemStateType.UNDESIRED, [])]
        if undesired_elements:
            combined_undesired = reduce(self.add_elements, undesired_elements)
        else:
            combined_undesired = _empty

        full_states = states_by_type.get(SubsystemStateType.FULL, [])
        assert len(full_states) in (0, 1)
        if full_states:
            full_state = full_states[0]
            full_elements = self.convert_elements(full_state.elements)
            if combined_desired is not _empty:
                combined_desired = cast(_InternalElements, combined_desired)
                full_elements = self.add_elements(full_elements, combined_desired)
            if combined_undesired is not _empty:
                combined_undesired = cast(_InternalElements, combined_undesired)
                full_elements = self.remove_elements(full_elements, combined_undesired)

            return [SubsystemState(name=self.PROVIDER_NAME, state_type=SubsystemStateType.FULL, elements=self.convert_elements_back(full_elements))]

        states = []
        if combined_desired is not _empty:
            combined_desired = cast(_InternalElements, combined_desired)
            desired_state = SubsystemState(
                name=self.PROVIDER_NAME, state_type=SubsystemStateType.DESIRED, elements=self.convert_elements_back(combined_desired)
            )
            states.append(desired_state)

        if combined_undesired is not _empty:
            combined_undesired = cast(_InternalElements, combined_undesired)
            undesired_state = SubsystemState(
                name=self.PROVIDER_NAME, state_type=SubsystemStateType.UNDESIRED, elements=self.convert_elements_back(combined_undesired)
            )
            states.append(undesired_state)

        return states
