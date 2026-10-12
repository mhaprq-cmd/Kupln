
"""Kupln Bootstrap Compilation Pipeline.

Coordinates parsing, type checking, semantic analysis,
and lowering into the platform-independent IR.
"""

from __future__ import annotations

from bootstrap.ir.lowering import lower_compilation_unit
from bootstrap.ir.model import IRModule
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


def compile_to_ir(source: str) -> IRModule:
    """Parse, analyze, and lower supported source into IR.

    Parsing, type-checking, and semantic-analysis errors are
    propagated before IR lowering can begin.
    """
    compilation_unit = analyze_source(source)
    return lower_compilation_unit(compilation_unit)


__all__ = [
    "parse_source",
    "analyze_compilation_unit",
    "analyze_source",
    "compile_to_ir",
]
