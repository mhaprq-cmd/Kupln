"""Kupln Bootstrap Token Model.

This module defines the lexical token representation used by the Kupln
bootstrap lexer and later parser stages.

Responsibilities:
    - define token categories
    - represent a lexical token
    - preserve the original token text
    - preserve the token source location

This module intentionally does not perform:
    - source loading
    - lexical scanning
    - parsing
    - semantic analysis
    - type checking
    - compilation
    - backend processing
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    """Categories of lexical tokens recognized by Kupln."""

    EOF = auto()

    IDENTIFIER = auto()
    KEYWORD = auto()

    INTEGER = auto()
    FLOAT = auto()

    STRING = auto()
    CHAR = auto()

    OPERATOR = auto()
    PUNCTUATION = auto()

    COMMENT = auto()

    UNKNOWN = auto()


@dataclass(frozen=True)
class SourcePosition:
    """Immutable position of a token inside a Kupln source file."""

    line: int
    column: int
    offset: int


@dataclass(frozen=True)
class Token:
    """Immutable lexical token representation."""

    kind: TokenKind
    lexeme: str
    position: SourcePosition
