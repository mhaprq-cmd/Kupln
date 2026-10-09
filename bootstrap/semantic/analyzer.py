
"""Kupln Bootstrap Semantic Analyzer.

This module implements inheritance-cycle detection for the current AST.

It does not replace the Type System or validate rules that have not yet
been defined by the Kupln language specification.
"""

from __future__ import annotations

from bootstrap.parser.ast import (
    ClassDeclaration,
    CompilationUnit,
    ExportDeclaration,
    InterfaceDeclaration,
    TypeReference,
)


class SemanticAnalysisError(Exception):
    """Raised when a supported semantic rule is violated."""

    def __init__(self, message: str, position) -> None:
        self.message = message
        self.position = position
        super().__init__(
            f"{message} at line {position.line}, "
            f"column {position.column}"
        )


class SemanticAnalyzer:
    """Run semantic checks supported by the current AST and specification."""

    def analyze(self, compilation_unit: CompilationUnit) -> None:
        """Analyze a compilation unit and raise on the first semantic error."""
        self._validate_inheritance_cycles(compilation_unit)

    def _validate_inheritance_cycles(
        self,
        compilation_unit: CompilationUnit,
    ) -> None:
        """Detect cycles in class inheritance and interface inheritance.

        Only top-level declarations are collected, matching the current
        TypeChecker's registration of user-defined types.
        """

        node_types = {}

        for item in compilation_unit.items:
            declaration = (
                item.declaration
                if isinstance(item, ExportDeclaration)
                else item
            )

            if isinstance(declaration, ClassDeclaration):
                key = ("class", declaration.name.name)
                node_types.setdefault(
                    key,
                    (declaration, declaration.extends),
                )

            elif isinstance(declaration, InterfaceDeclaration):
                key = ("interface", declaration.name.name)
                node_types.setdefault(
                    key,
                    (declaration, declaration.extends),
                )

        # Each edge records the parent declaration and source position.
        edges: dict[
            tuple[str, str],
            tuple[tuple[str, str], TypeReference],
        ] = {}

        for key, (_, parent_reference) in node_types.items():
            if parent_reference is None:
                continue

            # The current TypeChecker only resolves single-part type names.
            if len(parent_reference.parts) != 1:
                continue

            parent_name = parent_reference.parts[0].name
            parent_key = (key[0], parent_name)

            # Class inheritance follows class declarations only.
            # Interface inheritance follows interface declarations only.
            if parent_key in node_types:
                edges[key] = (parent_key, parent_reference)

        # 0 = unseen, 1 = currently visiting, 2 = complete.
        state: dict[tuple[str, str], int] = {}
        stack: list[tuple[str, str]] = []

        def visit(node: tuple[str, str]) -> None:
            state[node] = 1
            stack.append(node)

            edge = edges.get(node)
            if edge is not None:
                parent, parent_reference = edge
                parent_state = state.get(parent, 0)

                if parent_state == 0:
                    visit(parent)

                elif parent_state == 1:
                    cycle_start = stack.index(parent)
                    cycle = stack[cycle_start:] + [parent]
                    cycle_names = [name for _, name in cycle]

                    raise SemanticAnalysisError(
                        "Inheritance cycle detected: "
                        + " -> ".join(cycle_names),
                        parent_reference.position,
                    )

            stack.pop()
            state[node] = 2

        for node in node_types:
            if state.get(node, 0) == 0:
                visit(node)


def analyze_compilation_unit(
    compilation_unit: CompilationUnit,
) -> None:
    """Analyze a compilation unit using a fresh semantic analyzer."""
    SemanticAnalyzer().analyze(compilation_unit)


__all__ = [
    "SemanticAnalysisError",
    "SemanticAnalyzer",
    "analyze_compilation_unit",
  ]
              
