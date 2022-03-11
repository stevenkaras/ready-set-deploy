from io import StringIO
from typing import TextIO, cast
import json
import shlex

import click
import tomli

from ready_set_deploy.model import DataclassEncoder, SubsystemState
from ready_set_deploy.model import SystemState
from ready_set_deploy.registry import ProviderRegistry
from ready_set_deploy.itertools import dict_matching, iter_matching


def load_registry_from_config(configpath="config.toml") -> ProviderRegistry:
    with open(configpath, mode="rb") as f:
        config = tomli.load(f)

    return ProviderRegistry.from_dict(config)


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    ctx.obj = load_registry_from_config()


@main.command()
@click.argument("PROVIDER")
@click.pass_obj
def gather(registry: ProviderRegistry, provider: str):
    """
    Gather the local subsystem state for PROVIDER
    """
    if provider.lower() == "all":
        providers = registry.all()
    else:
        providers = [provider]

    substates = [registry.gather_local(provider) for provider in providers]
    state = SystemState.from_substates(substates)
    print(json.dumps(state, cls=DataclassEncoder))


@main.command()
@click.option("--actual-file", type=click.File("r"))
@click.option("--desired-file", type=click.File("r"))
@click.pass_obj
def diff(registry: ProviderRegistry, actual_file: TextIO, desired_file: TextIO):
    """
    Compute the diff to move from ACTUAL to DESIRED
    """
    actual_dict = json.load(actual_file)
    actual = SystemState.from_dict(actual_dict)
    desired_dict = json.load(desired_file)
    desired = SystemState.from_dict(desired_dict)

    all_partials = []
    for name, (actual_states, desired_states) in dict_matching(actual.subsystems, desired.subsystems, default=[]):
        actual_states = cast(list[SubsystemState], actual_states)
        desired_states = cast(list[SubsystemState], desired_states)
        for qualifier, (actual_state, desired_state) in iter_matching(
            actual_states, desired_states, key=lambda substate: substate.qualifier
        ):
            if actual_state is not None and desired_state is not None:
                partials = registry.diff(name, actual_state, desired_state)
            elif actual_state is not None and desired_state is None:
                partials = [
                    SubsystemState(
                        name=name,
                        qualifier=qualifier,
                        is_partial=True,
                        is_desired=False,
                        after_anchor=actual_state.after_anchor,
                        before_anchor=actual_state.before_anchor,
                        elements=actual_state.elements,
                    )
                ]
            elif actual_state is None and desired_state is not None:
                partials = [
                    SubsystemState(
                        name=name,
                        qualifier=qualifier,
                        is_partial=True,
                        is_desired=True,
                        after_anchor=desired_state.after_anchor,
                        before_anchor=desired_state.before_anchor,
                        elements=desired_state.elements,
                    )
                ]
            else:
                # can't happen, but for completeness's sake
                partials = []
            all_partials += partials

    state = SystemState.from_substates(all_partials)
    print(json.dumps(state, cls=DataclassEncoder))


@main.command()
@click.argument("PARTIAL", type=click.File("r"))
@click.pass_obj
def commands(registry: ProviderRegistry, partial: TextIO):
    partial_dict = json.load(partial)
    partial_state = SystemState.from_dict(partial_dict)

    for name, substates in partial_state.subsystems.items():
        substate_by_qualifier = {}
        for substate in substates:
            l = substate_by_qualifier.setdefault(substate.qualifier, [None, None])
            l[0 if substate.is_desired else 1] = substate

        for _, (desired, undesired) in substate_by_qualifier.items():
            for command in registry.to_commands(name, desired, undesired):
                print(shlex.join(command))


@main.command()
@click.pass_context
def test(context: click.Context):
    # context.invoke(gather, provider="packages.homebrew")

    actual = r"""
    {"subsystems": {"packages.homebrew": [{"name": "packages.homebrew", "qualifier": null, "is_partial": false, "is_desired": true, "after_anchor": null,
    "before_anchor": null, "elements": [
        ["tap-actual-only", "tap-shared"],
        [{"name": "cask-actual-only"}, {"name": "cask-shared"}],
        [{"name": "formula-actual-only"}, {"name": "formula-shared"}]]}]}}
    """
    desired = r"""
    {"subsystems": {"packages.homebrew": [{"name": "packages.homebrew", "qualifier": null, "is_partial": false, "is_desired": true, "after_anchor": null,
    "before_anchor": null, "elements": [
        ["tap-shared", "tap-desired-only"],
        [{"name": "cask-shared"}, {"name": "cask-desired-only"}],
        [{"name": "formula-shared"}, {"name": "formula-desired-only"}]]}]}}
    """
    context.invoke(diff, actual_file=StringIO(actual), desired_file=StringIO(desired))

    partial = r"""{"subsystems": {"packages.homebrew": [{"name": "packages.homebrew", "qualifier": null, "is_partial": true, "is_desired": true,
    "after_anchor": null, "before_anchor": null, "elements": [["tap-desired-only"], [{"name": "cask-desired-only"}], [{"name": "formula-desired-only"}]]},
    {"name": "packages.homebrew", "qualifier": null, "is_partial": true, "is_desired": false, "after_anchor": null, "before_anchor": null, "elements":
    [["tap-actual-only"], [{"name": "cask-actual-only"}], [{"name": "formula-actual-only"}]]}]}}"""
    context.invoke(commands, partial=StringIO(partial))


if __name__ == "__main__":
    registry = load_registry_from_config()
    test(obj=registry)
    # main()
