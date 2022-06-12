import json
import re
import sys
import shlex
from typing import TextIO, Optional
from collections.abc import Iterable

import click
from more_itertools import sliced

from ready_set_deploy.config import Config
from ready_set_deploy.systems import System


QUALIFIER_PATTERN = re.compile(r"/")


def _parse_qualifier(qualifier: Optional[str]) -> tuple[str, ...]:
    if qualifier is None:
        return ()

    return tuple(re.split(QUALIFIER_PATTERN, qualifier))


@click.group()
@click.pass_context
def main(ctx):
    ctx.obj = Config.load_from_files()


@main.command()
@click.argument("PROVIDER")
@click.option("--qualifier", default=None)
@click.pass_obj
def gather(config: Config, provider: str, qualifier: Optional[str] = None):
    """
    Gather the local subsystem state for PROVIDER
    """
    component = config.gatherers.gather_local(provider, qualifier=_parse_qualifier(qualifier))
    system = System(components=[component])
    print(json.dumps(system.to_primitive(), sort_keys=True))


@main.command()
@click.argument("actual_file", metavar="ACTUAL", type=click.File("r"))
@click.argument("goal_file", metavar="GOAL", type=click.File("r"))
def diff(actual_file: TextIO, goal_file: TextIO):
    """
    Compute the diff to move from ACTUAL to GOAL
    """
    actual_dict = json.load(actual_file)
    actual = System.from_primitive(actual_dict)
    goal_dict = json.load(goal_file)
    goal = System.from_primitive(goal_dict)

    diff = actual.diff(goal)

    print(json.dumps(diff.to_primitive(), sort_keys=True))


@main.command()
@click.argument("actual_file", metavar="ACTUAL", type=click.File("r"))
@click.argument("diff_file", metavar="DIFF", type=click.File("r"))
def apply(actual_file: TextIO, diff_file: TextIO):
    """
    Apply a diff from DIFF to the system state in ACTUAL
    """
    actual_dict = json.load(actual_file)
    actual = System.from_primitive(actual_dict)
    diff_dict = json.load(diff_file)
    diff = System.from_primitive(diff_dict)

    applied = actual.apply(diff)

    print(json.dumps(applied.to_primitive(), sort_keys=True))


@main.command()
@click.argument("state_files", metavar="STATES", nargs=-1, type=click.File("r"))
def combine(state_files: Iterable[TextIO]):
    """
    Combine multiple state files
    """
    print(type(state_files))
    states = [System.from_primitive(json.load(state_file)) for state_file in state_files]

    raise NotImplementedError("combine")


@main.command()
@click.argument("diff_file", metavar="DIFF", type=click.File("r"))
@click.pass_obj
def commands(config: Config, diff_file: TextIO):
    """
    Convert a PARTIAL state to commands to be run
    """
    diff_dict = json.load(diff_file)
    diff = System.from_primitive(diff_dict)

    for component in diff:
        for command in config.renderers.to_commands(component.name, component):
            print(shlex.join(command))


@main.command()
@click.argument("state_file", metavar="STATE", type=click.File("r"))
def providers(state_file: TextIO):
    """
    Output a list of provider/qualifier pairs
    """
    state_dict = json.load(state_file)
    state = System.from_primitive(state_dict)

    for component in state:
        print(f"p={component.name}")
        print(f"q={'/'.join(component.qualifier)}")


@main.command(name="gather-all")
@click.argument("providers_file", metavar="PROVIDERS", type=click.File("r"), default=sys.stdin)
@click.pass_obj
def gather_all(config: Config, providers_file: TextIO):
    """
    Gather each provider/qualifier pair from stdin
    """
    components = []
    for provider_line, qualifier_line in sliced(providers_file.readlines(), n=2, strict=True):
        [provider] = re.findall(r"p=(.*)", provider_line)
        [qualifier] = re.findall(r"q=(.*)", qualifier_line)

        components.append(config.gatherers.gather_local(provider, qualifier=_parse_qualifier(qualifier)))

    state = System(components=components)
    print(json.dumps(state.to_primitive(), sort_keys=True))


@main.command(name="apply-local")
@click.argument("role_file", metavar="[ROLE|PLAN]", type=click.File("r"))
@click.pass_obj
def apply_local(config: Config, role_file: TextIO):
    """
    Generate the commands for the diff from the local system to the provided ROLE or the given PLAN
    """
    state_dict = json.load(role_file)
    role = System.from_primitive(state_dict)

    local_components = []
    for component in role:
        local_components.append(config.gatherers.gather_local(component.name, qualifier=component.qualifier))

    local_state = System(components=local_components)

    if role.is_diff():
        applied = local_state.apply(role)
        diff = local_state.diff(applied)
    else:
        diff = local_state.diff(role)
    for component in diff.components:
        for command in config.renderers.to_commands(component.name, component):
            print(shlex.join(command))


@main.command(name="config")
@click.pass_obj
def print_config(config: Config):
    """
    Show the loaded configuration
    """
    print(config)


if __name__ == "__main__":
    main()
