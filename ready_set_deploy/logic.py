from typing import cast
from collections.abc import Iterable, Sequence

from more_itertools import flatten

from ready_set_deploy.registry import ProviderRegistry
from ready_set_deploy.model import SubsystemStateType, SubsystemState, SystemState
from ready_set_deploy.itertools import dict_matching, iter_matching, bucketdict


def diff_state(registry: ProviderRegistry, actual: SystemState, desired: SystemState) -> SystemState:
    """
    Compute the partial state that when applied would move actual to the desired state
    """
    all_partials = []
    for name, (actual_states, desired_states) in dict_matching(actual.subsystems, desired.subsystems, default=[]):
        actual_states = cast(list[SubsystemState], actual_states)
        desired_states = cast(list[SubsystemState], desired_states)
        for qualifier, (actual_state, desired_state) in iter_matching(actual_states, desired_states, key=lambda substate: substate.qualifier):
            if actual_state is not None and desired_state is not None:
                partials = registry.diff(name, actual_state, desired_state)
            elif actual_state is not None and desired_state is None:
                partials = [
                    SubsystemState(
                        name=name,
                        qualifier=qualifier,
                        state_type=SubsystemStateType.UNDESIRED,
                        elements=actual_state.elements,
                    )
                ]
            elif actual_state is None and desired_state is not None:
                partials = [
                    SubsystemState(
                        name=name,
                        qualifier=qualifier,
                        state_type=SubsystemStateType.DESIRED,
                        elements=desired_state.elements,
                    )
                ]
            else:
                # can't happen, but for completeness's sake
                partials = []
            all_partials += partials

    return SystemState.from_substates(all_partials)


def combine_states(registry: ProviderRegistry, *args: SystemState) -> SystemState:
    all_combined = []

    all_subsystems = flatten(flatten(state.subsystems.values() for state in args))

    for (name, _), subsystems in bucketdict(all_subsystems, key=lambda s: (s.name, s.qualifier)).items():
        combined = registry.combine(name, subsystems)
        all_combined += combined

    return SystemState.from_substates(all_combined)


def partial_to_commands(registry: ProviderRegistry, partial_state: SystemState) -> Iterable[Sequence[str]]:
    for name, substates in partial_state.subsystems.items():
        substate_by_qualifier = {}
        for substate in substates:
            l = substate_by_qualifier.setdefault(substate.qualifier, [None, None])
            l[0 if substate.state_type == SubsystemStateType.DESIRED else 1] = substate

        for _, (desired, undesired) in substate_by_qualifier.items():
            yield from registry.to_commands(name, desired, undesired)


def is_valid(registry: ProviderRegistry, system_state: SystemState) -> Iterable[str]:
    """
    Determine if a given system state is invalid, along with the reasons why
    """

    for name, subsystems in system_state.subsystems.items():
        for states in bucketdict(subsystems, lambda s: s.qualifier).values():
            num_desired = sum(1 for state in states if state.state_type == SubsystemStateType.DESIRED)
            if num_desired > 1:
                yield f"Found {num_desired} desired states. There must be at most 1"
            num_undesired = sum(1 for state in states if state.state_type == SubsystemStateType.UNDESIRED)
            if num_undesired > 1:
                yield f"Found {num_undesired} undesired states. There must be at most 1"

            num_full = sum(1 for state in states if state.state_type == SubsystemStateType.FULL)
            if num_full > 1:
                yield f"Found {num_full} full states. There must be at most 1"
            if num_full == 1 and (num_desired > 0 or num_undesired > 0):
                yield "Found full and partial states defined together. They are mutually exclusive"

            for state in states:
                yield from registry.is_valid(name, state)


def main():
    import tomli
    import json
    from ready_set_deploy.model import DataclassEncoder

    registry = ProviderRegistry.from_dict(
        tomli.loads(
            """
        packages.homebrew = "ready_set_deploy.providers.homebrew.HomebrewProvider"
        """
        )
    )

    actual = SystemState.from_dict(
        json.loads(
            r"""
    {"subsystems": {"packages.homebrew": [{"name": "packages.homebrew", "qualifier": null, "state_type": "full", "elements": [
        ["tap-actual-only", "tap-shared"],
        [{"name": "cask-actual-only"}, {"name": "cask-shared"}],
        [{"name": "formula-actual-only"}, {"name": "formula-shared"}]]}]}}
    """
        )
    )
    desired = SystemState.from_dict(
        json.loads(
            r"""
    {"subsystems": {"packages.homebrew": [{"name": "packages.homebrew", "qualifier": null, "state_type": "full", "elements": [
        ["tap-desired-only", "tap-shared"],
        [{"name": "cask-desired-only"}, {"name": "cask-shared"}],
        [{"name": "formula-desired-only"}, {"name": "formula-shared"}]]}]}}
    """
        )
    )
    diff = diff_state(registry, actual, desired)
    print(json.dumps(diff, cls=DataclassEncoder, sort_keys=True))

    partial = SystemState.from_dict(
        json.loads(
            r"""
    {"subsystems": {"packages.homebrew": [{"name": "packages.homebrew", "qualifier": null, "state_type": "desired", "elements":
        [["tap-desired-only"], [{"name": "cask-desired-only"}],[{"name": "formula-desired-only"}]]},
    {"name": "packages.homebrew", "qualifier": null, "state_type": "undesired", "elements":
        [["tap-actual-only"], [{"name": "cask-actual-only"}], [{"name": "formula-actual-only"}]]}]}}"""
        )
    )

    combined = combine_states(registry, partial, actual)
    print(json.dumps(desired, cls=DataclassEncoder, sort_keys=True))
    print(json.dumps(combined, cls=DataclassEncoder, sort_keys=True))

    import shlex

    for command in partial_to_commands(registry, partial):
        print(shlex.join(command))


if __name__ == "__main__":
    main()
