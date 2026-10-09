"""Tests for the Kupln Bootstrap Semantic Analyzer."""

from __future__ import annotations

import unittest

from bootstrap.lexer.token import SourcePosition
from bootstrap.parser.ast import (
    Block,
    ClassDeclaration,
    CompilationUnit,
    ExportDeclaration,
    FunctionDeclaration,
    Identifier,
    InterfaceDeclaration,
    Parameter,
    RecordDeclaration,
    StructDeclaration,
    TypeReference,
)
from bootstrap.semantic.analyzer import (
    SemanticAnalysisError,
    analyze_compilation_unit,
)


POSITION = SourcePosition(line=1, column=1, offset=0)

TYPE_KINDS = (
    "class",
    "interface",
    "struct",
    "record",
)


def identifier(name: str) -> Identifier:
    return Identifier(position=POSITION, name=name)


def type_reference(name: str) -> TypeReference:
    return TypeReference(
        position=POSITION,
        parts=(identifier(name),),
    )


def parameter(name: str, type_name: str) -> Parameter:
    return Parameter(
        position=POSITION,
        name=identifier(name),
        type_annotation=type_reference(type_name),
    )


def function_declaration(
    name: str,
    parameters: tuple[Parameter, ...] = (),
    return_type: str | None = None,
    async_modifier: bool = False,
) -> FunctionDeclaration:
    return FunctionDeclaration(
        position=POSITION,
        async_modifier=async_modifier,
        modifiers=(),
        name=identifier(name),
        parameters=parameters,
        return_type=(
            type_reference(return_type)
            if return_type is not None
            else None
        ),
        body=Block(position=POSITION, items=()),
    )


def class_declaration(
    name: str,
    parent: str | None = None,
    implements: tuple[str, ...] = (),
    members: tuple = (),
) -> ClassDeclaration:
    return ClassDeclaration(
        position=POSITION,
        modifiers=(),
        name=identifier(name),
        extends=type_reference(parent) if parent else None,
        implements=tuple(
            type_reference(item) for item in implements
        ),
        members=members,
    )


def interface_declaration(
    name: str,
    parent: str | None = None,
    members: tuple[FunctionDeclaration, ...] = (),
) -> InterfaceDeclaration:
    return InterfaceDeclaration(
        position=POSITION,
        modifiers=(),
        name=identifier(name),
        extends=type_reference(parent) if parent else None,
        members=members,
    )


def struct_declaration(name: str) -> StructDeclaration:
    return StructDeclaration(
        position=POSITION,
        modifiers=(),
        name=identifier(name),
        fields=(),
    )


def record_declaration(name: str) -> RecordDeclaration:
    return RecordDeclaration(
        position=POSITION,
        modifiers=(),
        name=identifier(name),
        fields=(),
    )


def type_declaration(kind: str, name: str):
    """Create a declaration of the requested user-defined type kind."""
    declarations = {
        "class": class_declaration,
        "interface": interface_declaration,
        "struct": struct_declaration,
        "record": record_declaration,
    }

    try:
        factory = declarations[kind]
    except KeyError:
        raise ValueError(
            f"Unsupported type declaration kind: {kind}"
        ) from None

    return factory(name)


def export_declaration(declaration) -> ExportDeclaration:
    return ExportDeclaration(
        position=POSITION,
        declaration=declaration,
    )


def compilation_unit(*items) -> CompilationUnit:
    return CompilationUnit(
        position=POSITION,
        items=tuple(items),
    )


class SemanticAnalyzerTests(unittest.TestCase):
    def test_independent_classes_pass(self) -> None:
        analyze_compilation_unit(
            compilation_unit(
                class_declaration("Alpha"),
                class_declaration("Beta"),
            )
        )

    def test_valid_class_inheritance_passes(self) -> None:
        analyze_compilation_unit(
            compilation_unit(
                class_declaration("Base"),
                class_declaration("Child", "Base"),
            )
        )

    def test_class_inheritance_cycle_is_rejected(self) -> None:
        unit = compilation_unit(
            class_declaration("Alpha", "Beta"),
            class_declaration("Beta", "Alpha"),
        )

        with self.assertRaises(
            SemanticAnalysisError
        ) as context:
            analyze_compilation_unit(unit)

        self.assertIn(
            "Inheritance cycle detected",
            str(context.exception),
        )
        self.assertEqual(
            context.exception.position,
            POSITION,
        )

    def test_interface_inheritance_cycle_is_rejected(self) -> None:
        unit = compilation_unit(
            interface_declaration("Readable", "Writable"),
            interface_declaration("Writable", "Readable"),
        )

        with self.assertRaises(SemanticAnalysisError):
            analyze_compilation_unit(unit)

    def test_exported_class_is_included(self) -> None:
        exported = export_declaration(
            class_declaration("Alpha", "Beta")
        )

        unit = compilation_unit(
            exported,
            class_declaration("Beta", "Alpha"),
        )

        with self.assertRaises(SemanticAnalysisError):
            analyze_compilation_unit(unit)

    def test_class_and_interface_cannot_share_a_type_name(
        self,
    ) -> None:
        unit = compilation_unit(
            class_declaration("Shared"),
            interface_declaration("Shared"),
        )

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "Duplicate type name 'Shared'",
        ):
            analyze_compilation_unit(unit)

    def test_duplicate_names_within_each_type_kind_are_rejected(
        self,
    ) -> None:
        for kind in TYPE_KINDS:
            with self.subTest(kind=kind):
                unit = compilation_unit(
                    type_declaration(kind, "Shared"),
                    type_declaration(kind, "Shared"),
                )

                with self.assertRaisesRegex(
                    SemanticAnalysisError,
                    "Duplicate type name 'Shared'",
                ):
                    analyze_compilation_unit(unit)

    def test_duplicate_names_across_all_type_kind_combinations_are_rejected(
        self,
    ) -> None:
        for first_kind in TYPE_KINDS:
            for second_kind in TYPE_KINDS:
                with self.subTest(
                    first_kind=first_kind,
                    second_kind=second_kind,
                ):
                    unit = compilation_unit(
                        type_declaration(
                            first_kind,
                            "Shared",
                        ),
                        type_declaration(
                            second_kind,
                            "Shared",
                        ),
                    )

                    with self.assertRaisesRegex(
                        SemanticAnalysisError,
                        "Duplicate type name 'Shared'",
                    ):
                        analyze_compilation_unit(unit)

    def test_duplicate_names_are_rejected_with_export_wrapping(
        self,
    ) -> None:
        for first_kind in TYPE_KINDS:
            for second_kind in TYPE_KINDS:
                for export_first in (False, True):
                    for export_second in (False, True):
                        with self.subTest(
                            first_kind=first_kind,
                            second_kind=second_kind,
                            export_first=export_first,
                            export_second=export_second,
                        ):
                            first = type_declaration(
                                first_kind,
                                "Shared",
                            )
                            second = type_declaration(
                                second_kind,
                                "Shared",
                            )

                            if export_first:
                                first = export_declaration(first)

                            if export_second:
                                second = export_declaration(second)

                            unit = compilation_unit(
                                first,
                                second,
                            )

                            with self.assertRaisesRegex(
                                SemanticAnalysisError,
                                "Duplicate type name 'Shared'",
                            ):
                                analyze_compilation_unit(unit)

    def test_duplicate_type_error_includes_conflicting_kinds(
        self,
    ) -> None:
        unit = compilation_unit(
            class_declaration("Shared"),
            interface_declaration("Shared"),
        )

        with self.assertRaises(
            SemanticAnalysisError
        ) as context:
            analyze_compilation_unit(unit)

        message = str(context.exception)

        self.assertIn("Duplicate type name 'Shared'", message)
        self.assertIn("Interface", message)
        self.assertIn("Class", message)

    def test_duplicate_type_error_includes_source_position(
        self,
    ) -> None:
        unit = compilation_unit(
            class_declaration("Shared"),
            record_declaration("Shared"),
        )

        with self.assertRaises(
            SemanticAnalysisError
        ) as context:
            analyze_compilation_unit(unit)

        self.assertEqual(
            context.exception.position,
            POSITION,
        )
        self.assertIn("line 1", str(context.exception))
        self.assertIn("column 1", str(context.exception))

    def test_class_cannot_extend_interface(self) -> None:
        unit = compilation_unit(
            interface_declaration("Contract"),
            class_declaration("Child", "Contract"),
        )

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "cannot extend interface",
        ):
            analyze_compilation_unit(unit)

    def test_class_cannot_implement_class(self) -> None:
        unit = compilation_unit(
            class_declaration("Concrete"),
            class_declaration(
                "Consumer",
                implements=("Concrete",),
            ),
        )

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "not an interface",
        ):
            analyze_compilation_unit(unit)

    def test_interface_cannot_extend_class(self) -> None:
        unit = compilation_unit(
            class_declaration("Concrete"),
            interface_declaration("Contract", "Concrete"),
        )

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "can extend interfaces only",
        ):
            analyze_compilation_unit(unit)

    def test_class_satisfies_interface_contract(self) -> None:
        required = function_declaration(
            "read",
            parameters=(
                parameter("count", "Int"),
            ),
            return_type="String",
        )

        implementation = function_declaration(
            "read",
            parameters=(
                parameter("count", "Int"),
            ),
            return_type="String",
        )

        analyze_compilation_unit(
            compilation_unit(
                interface_declaration(
                    "Readable",
                    members=(required,),
                ),
                class_declaration(
                    "Reader",
                    implements=("Readable",),
                    members=(implementation,),
                ),
            )
        )

    def test_missing_interface_method_is_rejected(self) -> None:
        required = function_declaration("read")

        unit = compilation_unit(
            interface_declaration(
                "Readable",
                members=(required,),
            ),
            class_declaration(
                "Reader",
                implements=("Readable",),
            ),
        )

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "does not implement required method 'read'",
        ):
            analyze_compilation_unit(unit)

    def test_incompatible_interface_method_signature_is_rejected(
        self,
    ) -> None:
        required = function_declaration(
            "read",
            parameters=(
                parameter("count", "Int"),
            ),
            return_type="String",
        )

        implementation = function_declaration(
            "read",
            parameters=(
                parameter("count", "Int"),
            ),
            return_type="Int",
        )

        unit = compilation_unit(
            interface_declaration(
                "Readable",
                members=(required,),
            ),
            class_declaration(
                "Reader",
                implements=("Readable",),
                members=(implementation,),
            ),
        )

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "does not match the signature",
        ):
            analyze_compilation_unit(unit)

    def test_inherited_interface_method_is_required(self) -> None:
        required = function_declaration("read")

        unit = compilation_unit(
            interface_declaration(
                "Readable",
                members=(required,),
            ),
            interface_declaration(
                "AdvancedReadable",
                "Readable",
            ),
            class_declaration(
                "Reader",
                implements=("AdvancedReadable",),
            ),
        )

        with self.assertRaisesRegex(
            SemanticAnalysisError,
            "required method 'read'",
        ):
            analyze_compilation_unit(unit)

    def test_method_inherited_from_base_class_satisfies_contract(
        self,
    ) -> None:
        required = function_declaration(
            "read",
            parameters=(
                parameter("count", "Int"),
            ),
            return_type="String",
        )

        inherited = function_declaration(
            "read",
            parameters=(
                parameter("count", "Int"),
            ),
            return_type="String",
        )

        analyze_compilation_unit(
            compilation_unit(
                interface_declaration(
                    "Readable",
                    members=(required,),
                ),
                class_declaration(
                    "Base",
                    members=(inherited,),
                ),
                class_declaration(
                    "Reader",
                    parent="Base",
                    implements=("Readable",),
                ),
            )
        )


if __name__ == "__main__":
    unittest.main()
