"""Kupln Bootstrap Type Environment.

This module provides scoped storage for names and their associated
types during Type System analysis.

Responsibilities:
    - maintain nested lexical scopes
    - define names and types
    - resolve names through enclosing scopes
    - prevent duplicate definitions in the same scope
    - provide deterministic symbol lookup

This module intentionally does not perform:
    - parsing
    - expression type checking
    - semantic analysis
    - code generation
    - runtime execution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from bootstrap.types.type_system import Type


class TypeEnvironmentError(Exception):
    """Base error for Type Environment failures."""


class DuplicateDefinitionError(TypeEnvironmentError):
    """Raised when a name is defined twice in the same scope."""


class UnknownNameError(TypeEnvironmentError):
    """Raised when a requested name cannot be resolved."""


@dataclass(frozen=True)
class Symbol:
    """Immutable symbol definition."""

    name: str
    type: Type


class TypeEnvironment:
    """A lexical scope containing typed symbols."""

    def __init__(self, parent: TypeEnvironment | None = None):
        self._parent = parent
        self._symbols: dict[str, Symbol] = {}

    @property
    def parent(self) -> TypeEnvironment | None:
        """Return the enclosing environment."""
        return self._parent

    def define(self, name: str, type_: Type) -> Symbol:
        """Define a name in the current scope."""
        if name in self._symbols:
            raise DuplicateDefinitionError(
                f"Name '{name}' is already defined in this scope."
            )

        symbol = Symbol(name=name, type=type_)
        self._symbols[name] = symbol
        return symbol

    def define_many(
        self,
        definitions: Iterable[tuple[str, Type]],
    ) -> tuple[Symbol, ...]:
        """Define multiple names in the current scope."""
        symbols = []

        for name, type_ in definitions:
            symbols.append(self.define(name, type_))

        return tuple(symbols)

    def contains_local(self, name: str) -> bool:
        """Return whether a name exists in the current scope."""
        return name in self._symbols

    def contains(self, name: str) -> bool:
        """Return whether a name exists in this scope or an enclosing scope."""
        if name in self._symbols:
            return True

        if self._parent is not None:
            return self._parent.contains(name)

        return False

    def resolve_local(self, name: str) -> Symbol | None:
        """Resolve a name only in the current scope."""
        return self._symbols.get(name)

    def resolve(self, name: str) -> Symbol:
        """Resolve a name through the enclosing scope chain."""
        symbol = self._symbols.get(name)

        if symbol is not None:
            return symbol

        if self._parent is not None:
            return self._parent.resolve(name)

        raise UnknownNameError(
            f"Unknown name '{name}'."
        )

    def child(self) -> TypeEnvironment:
        """Create a nested child scope."""
        return TypeEnvironment(parent=self)

    def names(self) -> tuple[str, ...]:
        """Return names defined directly in this scope."""
        return tuple(self._symbols.keys())

    def symbols(self) -> tuple[Symbol, ...]:
        """Return symbols defined directly in this scope."""
        return tuple(self._symbols.values())


def create_root_environment() -> TypeEnvironment:
    """Create an empty root Type Environment."""
    return TypeEnvironment()
