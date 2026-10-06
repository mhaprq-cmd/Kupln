"""Kupln Bootstrap Reserved Keywords.

This module defines the reserved keywords recognized by the Kupln
bootstrap lexical foundation.

Responsibilities:
    - define the canonical reserved-keyword set
    - provide a stable keyword lookup boundary

This module intentionally does not perform:
    - source loading
    - lexical scanning
    - tokenization
    - parsing
    - semantic analysis
    - type checking
    - compilation
    - backend processing
"""

from __future__ import annotations


RESERVED_KEYWORDS: frozenset[str] = frozenset(
    {
        "let",
        "var",

        "function",
        "return",

        "if",
        "else",

        "for",
        "while",

        "class",
        "interface",
        "extends",
        "implements",

        "abstract",
        "final",

        "public",
        "private",
        "protected",

        "static",

        "struct",
        "record",

        "true",
        "false",

        "try",
        "catch",

        "async",
        "await",

        "import",
        "export",

        "new",

        "this",
        "super",

        "null",
    }
)


def is_reserved_keyword(value: str) -> bool:
    """Return whether a value is a reserved Kupln keyword."""
    return value in RESERVED_KEYWORDS
