from typing import TextIO, Optional
import json
import shlex
from collections.abc import Iterable

import click

from ready_set_deploy.model import DataclassEncoder, SystemState
from ready_set_deploy.registry import ProviderRegistry
from ready_set_deploy.logic import diff_state, combine_states, is_valid, partial_to_commands
from ready_set_deploy.config import load_registry_from_config


@click.group(invoke_without_command=True)
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
    if provider.lower() == "all":
        providers = [provider for provider, _ in registry.all()]
    else:
        providers = [provider]

    substates = [registry.gather_local(provider, qualifier=qualifier) for provider in providers]
    state = SystemState.from_substates(substates)

    print(json.dumps(state, cls=DataclassEncoder, sort_keys=True))


@main.command()
@click.argument("actual_file", metavar="ACTUAL", type=click.File("r"))
@click.argument("desired_file", metavar="DESIRED", type=click.File("r"))
@click.pass_obj
def diff(registry: ProviderRegistry, actual_file: TextIO, desired_file: TextIO):
    """
    Compute the diff to move from ACTUAL to DESIRED
    """
    actual_dict = json.load(actual_file)
    actual = SystemState.from_dict(actual_dict)
    desired_dict = json.load(desired_file)
    desired = SystemState.from_dict(desired_dict)

    partial = diff_state(registry, actual, desired)

    print(json.dumps(partial, cls=DataclassEncoder, sort_keys=True))


@main.command()
@click.argument("state_files", metavar="STATES", nargs=-2, type=click.File("r"))
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
@click.pass_obj
def config(registry: ProviderRegistry):
    """
    Show the loaded configuration
    """
    print(registry)


if __name__ == "__main__":
    main()
