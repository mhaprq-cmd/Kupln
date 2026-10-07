"""Kupln Bootstrap Type System.

This module defines the initial type representation used by the
Kupln bootstrap Type System.

Responsibilities:
    - represent built-in types
    - represent named user-defined types
    - represent array types
    - represent function types
    - provide deterministic type identity

This module intentionally does not perform:
    - parsing
    - name resolution
    - type checking
    - semantic analysis
    - code generation
    - runtime execution
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TypeKind(Enum):
    """Categories of types recognized by the bootstrap Type System."""

    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    CHAR = auto()
    NULL = auto()
    ANY = auto()
    VOID = auto()

    CLASS = auto()
    INTERFACE = auto()
    STRUCT = auto()
    RECORD = auto()

    ARRAY = auto()
    FUNCTION = auto()


@dataclass(frozen=True)
class Type:
    """Base immutable type representation."""

    kind: TypeKind
    name: str

    def is_value_type(self) -> bool:
        """Return whether this type is a primitive/value type."""
        return self.kind in {
            TypeKind.INT,
            TypeKind.FLOAT,
            TypeKind.BOOL,
            TypeKind.CHAR,
        }

    def is_reference_type(self) -> bool:
        """Return whether this type behaves as a reference type."""
        return self.kind in {
            TypeKind.STRING,
            TypeKind.CLASS,
            TypeKind.INTERFACE,
            TypeKind.RECORD,
            TypeKind.ARRAY,
        }


@dataclass(frozen=True)
class NamedType(Type):
    """A named user-defined type."""

    declaration_kind: TypeKind


@dataclass(frozen=True)
class ArrayType(Type):
    """An array type with a single element type."""

    element_type: Type

    def __init__(self, element_type: Type):
        object.__setattr__(self, "kind", TypeKind.ARRAY)
        object.__setattr__(self, "name", f"{element_type.name}[]")
        object.__setattr__(self, "element_type", element_type)


@dataclass(frozen=True)
class FunctionType(Type):
    """A function type."""

    parameter_types: tuple[Type, ...]
    return_type: Type
    async_function: bool = False

    def __init__(
        self,
        parameter_types: tuple[Type, ...],
        return_type: Type,
        async_function: bool = False,
    ):
        object.__setattr__(self, "kind", TypeKind.FUNCTION)

        prefix = "async " if async_function else ""
        parameters = ", ".join(
            parameter.name for parameter in parameter_types
        )

        object.__setattr__(
            self,
            "name",
            f"{prefix}({parameters}) -> {return_type.name}",
        )

        object.__setattr__(self, "parameter_types", parameter_types)
        object.__setattr__(self, "return_type", return_type)
        object.__setattr__(self, "async_function", async_function)


INT = Type(TypeKind.INT, "Int")
FLOAT = Type(TypeKind.FLOAT, "Float")
BOOL = Type(TypeKind.BOOL, "Bool")
STRING = Type(TypeKind.STRING, "String")
CHAR = Type(TypeKind.CHAR, "Char")
NULL = Type(TypeKind.NULL, "Null")
ANY = Type(TypeKind.ANY, "Any")
VOID = Type(TypeKind.VOID, "Void")


BUILTIN_TYPES: dict[str, Type] = {
    INT.name: INT,
    FLOAT.name: FLOAT,
    BOOL.name: BOOL,
    STRING.name: STRING,
    CHAR.name: CHAR,
    NULL.name: NULL,
    ANY.name: ANY,
    VOID.name: VOID,
}


def builtin_type(name: str) -> Type | None:
    """Return a built-in type by its language-level name."""
    return BUILTIN_TYPES.get(name)


def named_type(name: str, kind: TypeKind) -> NamedType:
    """Create a named user-defined type."""
    if kind not in {
        TypeKind.CLASS,
        TypeKind.INTERFACE,
        TypeKind.STRUCT,
        TypeKind.RECORD,
    }:
        raise ValueError(
            "named_type requires a user-defined declaration kind"
        )

    return NamedType(
        kind=kind,
        name=name,
        declaration_kind=kind,
    )


def array_type(element_type: Type) -> ArrayType:
    """Create an array type."""
    return ArrayType(element_type)


def function_type(
    parameter_types: tuple[Type, ...],
    return_type: Type,
    async_function: bool = False,
) -> FunctionType:
    """Create a function type."""
    return FunctionType(
        parameter_types=parameter_types,
        return_type=return_type,
        async_function=async_function,
    )


def is_numeric(type_: Type) -> bool:
    """Return whether a type is numeric."""
    return type_.kind in {
        TypeKind.INT,
        TypeKind.FLOAT,
    }


def is_boolean(type_: Type) -> bool:
    """Return whether a type is Bool."""
    return type_.kind is TypeKind.BOOL


def is_nullable(type_: Type) -> bool:
    """Return whether a type can represent null."""
    return (
        type_.kind is TypeKind.NULL
        or type_.is_reference_type()
        or type_.kind is TypeKind.ANY
  )
