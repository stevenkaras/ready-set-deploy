import json
import re
import sys
import shlex
from collections.abc import Iterable
from typing import TextIO, Optional

import click
from more_itertools import sliced

from ready_set_deploy.model import DataclassEncoder, SystemState
from ready_set_deploy.registry import ProviderRegistry
from ready_set_deploy.logic import diff_state, combine_states, is_valid, partial_to_commands
from ready_set_deploy.config import load_registry_from_config


@click.group()
@click.pass_context
def main(ctx):
    ctx.obj = load_registry_from_config()


@main.command()
@click.argument("PROVIDER")
@click.option("--qualifier", default=None)
@click.pass_obj
def gather(registry: ProviderRegistry, provider: str, qualifier: Optional[str] = None):
    """
    Gather the local subsystem state for PROVIDER
    """
    state = SystemState.from_substates([registry.gather_local(provider, qualifier=qualifier)])

    print(json.dumps(state, cls=DataclassEncoder, sort_keys=True))


@main.command()
@click.argument("actual_file", metavar="ACTUAL", type=click.File("r"))
@click.argument("goal_file", metavar="GOAL", type=click.File("r"))
@click.pass_obj
def diff(registry: ProviderRegistry, actual_file: TextIO, goal_file: TextIO):
    """
    Compute the diff to move from ACTUAL to GOAL
    """
    actual_dict = json.load(actual_file)
    actual = SystemState.from_dict(actual_dict)
    goal_dict = json.load(goal_file)
    goal = SystemState.from_dict(goal_dict)

    partial = diff_state(registry, actual, goal)

    print(json.dumps(partial, cls=DataclassEncoder, sort_keys=True))


@main.command()
@click.argument("state_files", metavar="STATES", nargs=-1, type=click.File("r"))
@click.pass_obj
def combine(registry: ProviderRegistry, state_files: Iterable[TextIO]):
    """
    Combine multiple state files
    """
    print(type(state_files))
    states = [SystemState.from_dict(json.load(state_file)) for state_file in state_files]

    combined_state = combine_states(registry, *states)

    print(json.dumps(combined_state, cls=DataclassEncoder, sort_keys=True))


@main.command()
@click.argument("PARTIAL", type=click.File("r"))
@click.pass_obj
def commands(registry: ProviderRegistry, partial: TextIO):
    """
    Convert a PARTIAL state to commands to be run
    """
    partial_dict = json.load(partial)
    partial_state = SystemState.from_dict(partial_dict)

    for command in partial_to_commands(registry, partial_state):
        print(shlex.join(command))


@main.command()
@click.argument("state_file", metavar="STATE", type=click.File("r"))
@click.pass_obj
def validate(registry: ProviderRegistry, state_file: TextIO):
    """
    Validate if a state is consistent and conforms to the ready-set-deploy schema requirements
    """
    state_dict = json.load(state_file)
    state = SystemState.from_dict(state_dict)

    reasons = is_valid(registry, state)
    if not reasons:
        return 0

    for reason in reasons:
        print(reason)

    return 1


@main.command()
@click.argument("state_file", metavar="STATE", type=click.File("r"))
def providers(state_file: TextIO):
    """
    Output a list of provider/qualifier pairs
    """
    state_dict = json.load(state_file)
    state = SystemState.from_dict(state_dict)

    for provider, subsystems in state.subsystems.items():
        for subsystem in subsystems:
            print(f"p={provider}")
            if subsystem.qualifier is None:
                print()
            else:
                print(f"q={subsystem.qualifier}")


@main.command("gather-all")
@click.argument("providers_file", metavar="PROVIDERS", type=click.File("r"), default=sys.stdin)
@click.pass_obj
def gather_all(registry: ProviderRegistry, providers_file: TextIO):
    """
    Gather each provider/qualifier pair from stdin
    """
    subsystems = []
    for provider_line, qualifier_line in sliced(providers_file.readlines(), n=2, strict=True):
        [provider] = re.findall(r"p=(.*)", provider_line)
        qualifiers = re.findall(r"q=(.*)", qualifier_line)
        if qualifiers:
            [qualifier] = qualifiers
        else:
            qualifier = None

        subsystems.append(registry.gather_local(provider, qualifier=qualifier))

    state = SystemState.from_substates(subsystems)
    print(json.dumps(state, cls=DataclassEncoder, sort_keys=True))


@main.command()
@click.argument("role_file", metavar="ROLE", type=click.File("r"))
@click.pass_obj
def apply(registry: ProviderRegistry, role_file: TextIO):
    """
    Generate the commands for the diff from the local system to the provided ROLE
    """
    state_dict = json.load(role_file)
    role_state = SystemState.from_dict(state_dict)

    local_subsystems = []
    for provider, role_subsystems in role_state.subsystems.items():
        for role_subsystem in role_subsystems:
            local_subsystems.append(registry.gather_local(provider, qualifier=role_subsystem.qualifier))

    local_state = SystemState.from_substates(local_subsystems)
    partial_state = diff_state(registry, local_state, role_state)
    for command in partial_to_commands(registry, partial_state):
        print(shlex.join(command))


@main.command()
@click.pass_obj
def config(registry: ProviderRegistry):
    """
    Show the loaded configuration
    """
    print(registry)


if __name__ == "__main__":
    main()
