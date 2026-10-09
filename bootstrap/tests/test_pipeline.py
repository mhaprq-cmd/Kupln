"""Integration tests for the Kupln analysis pipeline."""

from __future__ import annotations

import unittest

from bootstrap.pipeline import analyze_source, parse_source
from bootstrap.parser.parser import ParserError
from bootstrap.semantic.analyzer import SemanticAnalysisError
from bootstrap.types.declaration_checker import TypeCheckError


class AnalysisPipelineTests(unittest.TestCase):
    def test_parse_source_returns_compilation_unit(self) -> None:
        unit = parse_source("class Alpha {}")

        self.assertEqual(len(unit.items), 1)

    def test_valid_source_passes_analysis(self) -> None:
        source = """
        class Base {}
        class Child extends Base {}
        """

        unit = analyze_source(source)

        self.assertEqual(len(unit.items), 2)

    def test_inheritance_cycle_is_rejected(self) -> None:
        source = """
        class Alpha extends Beta {}
        class Beta extends Alpha {}
        """

        with self.assertRaises(SemanticAnalysisError):
            analyze_source(source)

    def test_duplicate_type_names_are_rejected_by_full_pipeline(
        self,
    ) -> None:
        source = """
        class Shared {}
        interface Shared {}
        """

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "Duplicate type name 'Shared'",
        ):
            analyze_source(source)

    def test_duplicate_type_names_with_export_are_rejected_by_full_pipeline(
        self,
    ) -> None:
        source = """
        export class Shared {}
        record Shared {}
        """

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "Duplicate type name 'Shared'",
        ):
            analyze_source(source)

    def test_unknown_type_is_rejected(self) -> None:
        source = "let item: MissingType;"

        with self.assertRaises(TypeCheckError):
            analyze_source(source)

    def test_syntax_error_is_reported(self) -> None:
        with self.assertRaises(ParserError):
            analyze_source("class Alpha {")


if __name__ == "__main__":
    unittest.main()
