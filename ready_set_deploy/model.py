"""
Models for serialized data
"""
from typing import Optional

class SystemState:
    def __init__(self):
        self.subsystems: dict[str, list[SubsystemState]] = {}


class SubsystemState:
    def __init__(
        self,
        name: str,
        qualifier: Optional[str] = None,
        is_partial: bool = False,
        is_desired: bool = True,
        after_anchor: Optional[str] = None,
        before_anchor: Optional[str] = None,
        elements: list = None,
    ):
        self.name = name
        self.qualifier = qualifier
        self.is_partial = is_partial
        self.is_desired = is_desired
        self.after_anchor = after_anchor
        self.before_anchor = before_anchor
        self.elements = elements if elements is not None else []

    def __str__(self):
        marker = ""
        if self.is_partial:
            marker = "+"
        if not self.is_desired:
            marker = "-"
        return f"<SubsystemState.{self.name} {{{self.qualifier}}} e{marker}={self.elements}>"

    __repr__ = __str__
