
"""Platform-independent Intermediate Representation model for Kupln."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


@dataclass(frozen=True)
class IRSourceLocation:
    """Source location preserved for diagnostics."""

    line: int
    column: int
    offset: int


@dataclass(frozen=True)
class IRValue:
    """Reference to a value produced or consumed by IR instructions."""

    name: str
    type_name: str | None = None


@dataclass(frozen=True)
class IRConstant:
    """A literal value represented independently of source AST nodes."""

    kind: str
    value: str


class IROpcode(Enum):
    """Initial platform-independent IR operation kinds."""

    CONSTANT = auto()
    PARAMETER = auto()
    DECLARE_VARIABLE = auto()
    STORE = auto()
    LOAD = auto()
    UNARY = auto()
    BINARY = auto()
    CALL = auto()
    RETURN = auto()


@dataclass(frozen=True)
class IRInstruction:
    """One explicitly structured IR operation."""

    opcode: IROpcode
    result: IRValue | None = None
    operands: tuple[IRValue | IRConstant | str, ...] = ()
    source_location: IRSourceLocation | None = None


@dataclass(frozen=True)
class IRParameter:
    """Function parameter in the IR model."""

    name: str
    type_name: str | None = None


@dataclass(frozen=True)
class IRBasicBlock:
    """Ordered instructions belonging to one basic block."""

    name: str
    instructions: tuple[IRInstruction, ...] = ()


@dataclass(frozen=True)
class IRFunction:
    """Platform-independent representation of a function."""

    name: str
    parameters: tuple[IRParameter, ...] = ()
    return_type: str | None = None
    blocks: tuple[IRBasicBlock, ...] = ()


@dataclass(frozen=True)
class IRModule:
    """Ordered IR functions produced for a compilation unit."""

    functions: tuple[IRFunction, ...] = ()


__all__ = [
    "IRSourceLocation",
    "IRValue",
    "IRConstant",
    "IROpcode",
    "IRInstruction",
    "IRParameter",
    "IRBasicBlock",
    "IRFunction",
    "IRModule",
  ]
