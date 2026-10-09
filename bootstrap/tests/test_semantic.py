"""Tests for the Kupln Bootstrap Semantic Analyzer."""

from __future__ import annotations

import unittest

from bootstrap.lexer.token import SourcePosition
from bootstrap.parser.ast import (
    ClassDeclaration,
    CompilationUnit,
    ExportDeclaration,
    Identifier,
    InterfaceDeclaration,
    TypeReference,
)
from bootstrap.semantic.analyzer import (
    SemanticAnalysisError,
    SemanticAnalyzer,
    analyze_compilation_unit,
)


POSITION = SourcePosition(line=1, column=1, offset=0)


def identifier(name: str) -> Identifier:
    return Identifier(position=POSITION, name=name)


def type_reference(name: str) -> TypeReference:
    return TypeReference(
        position=POSITION,
        parts=(identifier(name),),
    )


def class_declaration(
    name: str,
    parent: str | None = None,
) -> ClassDeclaration:
    return ClassDeclaration(
        position=POSITION,
        modifiers=(),
        name=identifier(name),
        extends=type_reference(parent) if parent else None,
        implements=(),
        members=(),
    )


def interface_declaration(
    name: str,
    parent: str | None = None,
) -> InterfaceDeclaration:
    return InterfaceDeclaration(
        position=POSITION,
        modifiers=(),
        name=identifier(name),
        extends=type_reference(parent) if parent else None,
        members=(),
    )


def compilation_unit(*items) -> CompilationUnit:
    return CompilationUnit(position=POSITION, items=tuple(items))


class SemanticAnalyzerTests(unittest.TestCase):
    def test_independent_classes_pass(self) -> None:
        unit = compilation_unit(
            class_declaration("Alpha"),
            class_declaration("Beta"),
        )

        SemanticAnalyzer().analyze(unit)

    def test_valid_class_inheritance_passes(self) -> None:
        unit = compilation_unit(
            class_declaration("Base"),
            class_declaration("Child", "Base"),
        )

        analyze_compilation_unit(unit)

    def test_class_inheritance_cycle_is_rejected(self) -> None:
        unit = compilation_unit(
            class_declaration("Alpha", "Beta"),
            class_declaration("Beta", "Alpha"),
        )

        with self.assertRaises(SemanticAnalysisError) as context:
            analyze_compilation_unit(unit)

        self.assertIn(
            "Inheritance cycle detected",
            str(context.exception),
        )
        self.assertEqual(context.exception.position, POSITION)

    def test_interface_inheritance_cycle_is_rejected(self) -> None:
        unit = compilation_unit(
            interface_declaration("Readable", "Writable"),
            interface_declaration("Writable", "Readable"),
        )

        with self.assertRaises(SemanticAnalysisError):
            analyze_compilation_unit(unit)

    def test_exported_class_is_included(self) -> None:
        exported = ExportDeclaration(
            position=POSITION,
            declaration=class_declaration("Alpha", "Beta"),
        )

        unit = compilation_unit(
            exported,
            class_declaration("Beta", "Alpha"),
        )

        with self.assertRaises(SemanticAnalysisError):
            analyze_compilation_unit(unit)

    def test_class_and_interface_names_are_separate_graph_nodes(self) -> None:
        unit = compilation_unit(
            class_declaration("Shared"),
            interface_declaration("Shared"),
        )

        analyze_compilation_unit(unit)


if __name__ == "__main__":
    unittest.main()

