"""
Models for serialized data
"""
import json
import dataclasses
from typing import Optional
from collections.abc import Iterable


@dataclasses.dataclass
class SubsystemState:
    name: str
    qualifier: Optional[str] = None
    is_partial: bool = False
    is_desired: bool = True
    after_anchor: Optional[str] = None
    before_anchor: Optional[str] = None
    elements: list = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, source: dict):
        return cls(**source)

    def __str__(self):
        marker = ""
        if self.is_partial:
            marker = "+"
        if not self.is_desired:
            marker = "-"
        return f"<SubsystemState.{self.name} {{{self.qualifier}}} e{marker}={self.elements}>"

    __repr__ = __str__


@dataclasses.dataclass
class SystemState:
    subsystems: dict[str, list[SubsystemState]] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_dict(cls, source):
        return cls(
            subsystems={
                name: [SubsystemState.from_dict(substate) for substate in substates]
                for name, substates in source["subsystems"].items()
            }
        )

    @classmethod
    def from_substates(cls, substates: Iterable[SubsystemState]) -> "SystemState":
        state = cls()
        for substate in substates:
            state.subsystems.setdefault(substate.name, []).append(substate)

        return state


def _dataclass_to_shallow_dict(obj):
    return {field.name: getattr(obj, field.name) for field in dataclasses.fields(obj)}


class DataclassEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return _dataclass_to_shallow_dict(o)
        return super().default(o)
