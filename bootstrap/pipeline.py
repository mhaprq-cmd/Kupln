
"""Kupln Bootstrap Analysis Pipeline.

Coordinates existing analysis stages without merging their
responsibilities.
"""

from __future__ import annotations

from bootstrap.parser.ast import CompilationUnit
from bootstrap.semantic.analyzer import SemanticAnalyzer
from bootstrap.types.checker import TypeChecker


def analyze_compilation_unit(
    compilation_unit: CompilationUnit,
) -> None:
    """Run type checking followed by semantic analysis.

    Raises:
        TypeCheckError: When the existing type checker rejects the unit.
        SemanticAnalysisError: When a supported semantic rule is violated.
    """
    TypeChecker().check(compilation_unit)
    SemanticAnalyzer().analyze(compilation_unit)


__all__ = ["analyze_compilation_unit"]
  
