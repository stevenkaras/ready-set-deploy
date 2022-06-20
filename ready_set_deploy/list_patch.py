import click
import json
import sys
from typing import TextIO

from ready_set_deploy.elements import List, ListDiff


@click.command()
@click.argument("file", metavar="TARGET", type=click.File("r"))
@click.argument("raw_list_diff", metavar="LIST_DIFF")
def main(file: TextIO, raw_list_diff: str):
    """
    Apply LIST_DIFF to the TARGET file
    """
    list_diff = ListDiff.from_primitive(json.loads(raw_list_diff))
    if not isinstance(list_diff, ListDiff):
        click.echo("LIST_DIFF is not a list diff", err=True)
        raise click.exceptions.Exit(1)

    file_contents = List.infer(list(file.readlines()))

    applied = file_contents.apply(list_diff)
    print("".join(a.value for a in applied))


if __name__ == "__main__":
    main()
