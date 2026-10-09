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
    TypeReference,
)
from bootstrap.semantic.analyzer import (
    SemanticAnalysisError,
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
        implements=tuple(type_reference(item) for item in implements),
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


def compilation_unit(*items) -> CompilationUnit:
    return CompilationUnit(position=POSITION, items=tuple(items))


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
            class_declaration("Consumer", implements=("Concrete",)),
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
            parameters=(parameter("count", "Int"),),
            return_type="String",
        )
        implementation = function_declaration(
            "read",
            parameters=(parameter("count", "Int"),),
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
            class_declaration("Reader", implements=("Readable",)),
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
            parameters=(parameter("count", "Int"),),
            return_type="String",
        )
        implementation = function_declaration(
            "read",
            parameters=(parameter("count", "Int"),),
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
            interface_declaration("AdvancedReadable", "Readable"),
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
            parameters=(parameter("count", "Int"),),
            return_type="String",
        )
        inherited = function_declaration(
            "read",
            parameters=(parameter("count", "Int"),),
            return_type="String",
        )

        analyze_compilation_unit(
            compilation_unit(
                interface_declaration(
                    "Readable",
                    members=(required,),
                ),
                class_declaration("Base", members=(inherited,)),
                class_declaration(
                    "Reader",
                    parent="Base",
                    implements=("Readable",),
                ),
            )
        )


if __name__ == "__main__":
    unittest.main()
