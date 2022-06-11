import json
import logging
import subprocess
from collections.abc import Iterable, Sequence
from typing import Optional

from more_itertools import chunked

log = logging.getLogger(__name__)


class CommandRunner:
    def __init__(self):
        self.max_cli_params = 1024

    def to_commands(self, command: list[str], params: Optional[Iterable[str]] = None) -> Iterable[Sequence[str]]:
        if params is None:
            yield command
            return

        for chunk in chunked(params, self.max_cli_params - len(command)):
            yield command + chunk

    def lines(self, command: list[str], params: Iterable[str] = []) -> Iterable[str]:
        for chunk_command in self.to_commands(command, params):
            for line in self.run(chunk_command).split("\n"):
                if not line:
                    continue
                yield line

    def json(self, command: list[str]) -> dict:
        return json.loads(self.run(command))

    def run(self, command: Sequence[str]) -> str:
        log.debug("Running `%s`", " ".join(command))
        result = subprocess.run(command, capture_output=True, encoding="utf-8")
        return result.stdout


Runner = CommandRunner()
