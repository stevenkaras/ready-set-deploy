"""
Models for serialized data
"""
import json
import enum
import dataclasses
from typing import Optional
from collections.abc import Iterable


class SubsystemStateType(enum.Enum):
    FULL = "full"
    DESIRED = "desired"
    UNDESIRED = "undesired"


@dataclasses.dataclass
class SubsystemState:
    name: str
    state_type: SubsystemStateType
    qualifier: Optional[str] = None
    elements: list = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, source: dict):
        source["state_type"] = SubsystemStateType(source["state_type"])
        return cls(**source)

    def __str__(self):
        marker = ""
        if self.state_type == SubsystemStateType.DESIRED:
            marker = "+"
        if self.state_type == SubsystemStateType.UNDESIRED:
            marker = "-"
        return f"<SubsystemState.{self.name} {{{self.qualifier}}} e{marker}={self.elements}>"

    __repr__ = __str__


@dataclasses.dataclass
class SystemState:
    subsystems: dict[str, list[SubsystemState]] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_dict(cls, source):
        return cls(subsystems={name: [SubsystemState.from_dict(substate) for substate in substates] for name, substates in source["subsystems"].items()})

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
        if isinstance(o, enum.Enum):
            return o.value
        return super().default(o)
