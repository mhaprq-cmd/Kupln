"""Kupln Bootstrap Analysis Pipeline.

Coordinates source parsing and analysis while preserving
the responsibilities of each compiler stage.
"""

from __future__ import annotations

from bootstrap.lexer.lexer import Lexer
from bootstrap.parser.ast import CompilationUnit
from bootstrap.parser.parser import Parser
from bootstrap.semantic.analyzer import SemanticAnalyzer
from bootstrap.types.checker import TypeChecker


def parse_source(source: str) -> CompilationUnit:
    """Tokenize and parse Kupln source text."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def analyze_compilation_unit(
    compilation_unit: CompilationUnit,
) -> None:
    """Run type checking followed by semantic analysis."""
    TypeChecker().check(compilation_unit)
    SemanticAnalyzer().analyze(compilation_unit)


def analyze_source(source: str) -> CompilationUnit:
    """Parse and analyze source text, returning its AST."""
    compilation_unit = parse_source(source)
    analyze_compilation_unit(compilation_unit)
    return compilation_unit


__all__ = [
    "parse_source",
    "analyze_compilation_unit",
    "analyze_source",
]
