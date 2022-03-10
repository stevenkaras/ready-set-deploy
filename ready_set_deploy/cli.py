from io import StringIO
from typing import TextIO, cast
import click
import json
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
@click.pass_context
def baz(context: click.Context):
    actual = r"""{"subsystems": {"packages.homebrew.formulas": [{"name": "packages.homebrew.formulas", "qualifier": null, "is_partial": false, "is_desired": true, "after_anchor": null, "before_anchor": null, "elements": [["age", ["1.0.0"]], ["automake", ["1.16.5"]], ["bash", ["5.1.16"]], ["coreutils", ["9.0_1"]], ["git", ["2.35.1"]], ["git-lfs", ["3.1.2"]], ["gnupg", ["2.3.4"]], ["grep", ["3.7"]], ["htop", ["3.1.2"]], ["imagemagick", ["7.1.0-27"]], ["jq", ["1.6"]], ["libyaml", ["0.2.5"]], ["mas", ["1.8.6"]], ["mosh", ["1.3.2_18"]], ["nano", ["6.2"]], ["ncdu", ["2.1"]], ["nmap", ["7.92"]], ["nodenv", ["1.4.0"]], ["pinentry-mac", ["1.1.1.1"]], ["pipx", ["1.0.0"]], ["plantuml", ["1.2022.2_1"]], ["postgresql", ["14.2_1"]], ["pyenv", ["2.2.4-1"]], ["rbenv", ["1.2.0"]], ["reattach-to-user-namespace", ["2.9"]], ["shellcheck", ["0.8.0"]], ["starship", ["1.4.0"]], ["terraform-docs", ["0.16.0"]], ["terraform-ls", ["0.25.2"]], ["the_silver_searcher", ["2.2.0"]], ["tmux", ["3.2a"]], ["tree", ["2.0.2"]], ["unison-fsmonitor", ["0.3.0"]], ["v8", ["9.9.115.8"]], ["v8@3.15", ["3.15.11.18_1"]], ["watch", ["3.3.17"]], ["yq", ["4.21.1"]], ["zlib", ["1.2.11"]], ["zsh", ["5.8.1"]]]}]}}"""
    desired = r"""{"subsystems": {"packages.homebrew.formulas": [{"name": "packages.homebrew.formulas", "qualifier": null, "is_partial": false, "is_desired": true, "after_anchor": null, "before_anchor": null, "elements": [["age", ["1.0.1"]], ["bash", ["5.1.16", "4.1.5"]], ["bash-completion", ["1.3_3"]], ["coreutils", ["9.0_1"]], ["git", ["2.35.1"]], ["git-lfs", ["3.1.2"]], ["gnupg", ["2.3.4"]], ["grep", ["3.7"]], ["htop", ["3.1.2"]], ["imagemagick", ["7.1.0-27"]], ["jq", ["1.6"]], ["libyaml", ["0.2.5"]], ["mas", ["1.8.6"]], ["mosh", ["1.3.2_18"]], ["nano", ["6.2"]], ["ncdu", ["2.1"]], ["nmap", ["7.92"]], ["nodenv", ["1.4.0"]], ["pinentry-mac", ["1.1.1.1"]], ["pipx", ["1.0.0"]], ["plantuml", ["1.2022.2_1"]], ["postgresql", ["14.2_1"]], ["pyenv", ["2.2.4-1"]], ["rbenv", ["1.2.0"]], ["reattach-to-user-namespace", ["2.9"]], ["shellcheck", ["0.8.0"]], ["starship", ["1.4.0"]], ["terraform-docs", ["0.16.0"]], ["terraform-ls", ["0.25.2"]], ["the_silver_searcher", ["2.2.0"]], ["tmux", ["3.2a"]], ["tree", ["2.0.2"]], ["unison-fsmonitor", ["0.3.0"]], ["v8", ["9.9.115.8"]], ["v8@3.15", ["3.15.11.18_1"]], ["watch", ["3.3.17"]], ["yq", ["4.21.1"]], ["zlib", ["1.2.11"]], ["zsh", ["5.8.1"]]]}]}}"""
    context.invoke(diff, actual_file=StringIO(actual), desired_file=StringIO(desired))


if __name__ == "__main__":
    registry = load_registry_from_config()
    baz(obj=registry)
    # main()
