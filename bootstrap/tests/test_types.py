"""Tests for the Kupln Bootstrap Type System."""

from __future__ import annotations

import unittest

from bootstrap.parser.ast import (
    BinaryExpression,
    CompilationUnit,
    Identifier,
    IdentifierExpression,
    LiteralExpression,
    SourcePosition,
    TypeReference,
    VariableDeclaration,
)
from bootstrap.types.checker import (
    InvalidAssignmentError,
    InvalidTypeOperationError,
    TypeChecker,
    UnknownTypeError,
    check_compilation_unit,
)
from bootstrap.types.type_system import (
    ANY,
    BOOL,
    FLOAT,
    INT,
    NULL,
    STRING,
    VOID,
    TypeKind,
    array_type,
    function_type,
)


POSITION = SourcePosition(
    line=1,
    column=1,
    offset=0,
)


def identifier(name: str) -> Identifier:
    return Identifier(
        position=POSITION,
        name=name,
    )


def type_reference(name: str) -> TypeReference:
    return TypeReference(
        position=POSITION,
        parts=(identifier(name),),
    )


def literal(kind: str, value: str) -> LiteralExpression:
    return LiteralExpression(
        position=POSITION,
        kind=kind,
        value=value,
    )


class TypeSystemTests(unittest.TestCase):
    def test_builtin_types_exist(self) -> None:
        self.assertEqual(INT.kind, TypeKind.INT)
        self.assertEqual(FLOAT.kind, TypeKind.FLOAT)
        self.assertEqual(BOOL.kind, TypeKind.BOOL)
        self.assertEqual(STRING.kind, TypeKind.STRING)
        self.assertEqual(NULL.kind, TypeKind.NULL)
        self.assertEqual(ANY.kind, TypeKind.ANY)
        self.assertEqual(VOID.kind, TypeKind.VOID)

    def test_array_type(self) -> None:
        values = array_type(INT)

        self.assertEqual(values.kind, TypeKind.ARRAY)
        self.assertEqual(values.element_type, INT)
        self.assertEqual(values.name, "Int[]")

    def test_function_type(self) -> None:
        function = function_type(
            parameter_types=(INT, STRING),
            return_type=BOOL,
        )

        self.assertEqual(function.kind, TypeKind.FUNCTION)
        self.assertEqual(
            function.parameter_types,
            (INT, STRING),
        )
        self.assertEqual(function.return_type, BOOL)
        self.assertFalse(function.async_function)

    def test_assignability(self) -> None:
        checker = TypeChecker()

        self.assertTrue(
            checker.is_assignable(INT, INT)
        )
        self.assertTrue(
            checker.is_assignable(INT, ANY)
        )
        self.assertFalse(
            checker.is_assignable(INT, STRING)
        )
        self.assertTrue(
            checker.is_assignable(NULL, STRING)
        )

    def test_unknown_type_is_rejected(self) -> None:
        checker = TypeChecker()

        with self.assertRaises(UnknownTypeError):
            checker.resolve_type(
                type_reference("MissingType")
            )

    def test_integer_variable_inference(self) -> None:
        declaration = VariableDeclaration(
            position=POSITION,
            modifiers=(),
            keyword="let",
            name=identifier("count"),
            type_annotation=None,
            initializer=literal("INTEGER", "10"),
        )

        unit = CompilationUnit(
            position=POSITION,
            items=(declaration,),
        )

        check_compilation_unit(unit)

    def test_incompatible_variable_assignment_is_rejected(self) -> None:
        declaration = VariableDeclaration(
            position=POSITION,
            modifiers=(),
            keyword="let",
            name=identifier("count"),
            type_annotation=type_reference("Int"),
            initializer=literal("STRING", "hello"),
        )

        unit = CompilationUnit(
            position=POSITION,
            items=(declaration,),
        )

        with self.assertRaises(InvalidAssignmentError):
            check_compilation_unit(unit)

    def test_numeric_addition(self) -> None:
        checker = TypeChecker()

        expression = BinaryExpression(
            position=POSITION,
            left=literal("INTEGER", "1"),
            operator="+",
            right=literal("INTEGER", "2"),
        )

        self.assertEqual(
            checker._check_expression(expression),
            INT,
        )

  def test_mixed_numeric_addition_is_rejected(self) -> None:
        checker = TypeChecker()

        expression = BinaryExpression(
            position=POSITION,
            left=literal("INTEGER", "1"),
            operator="+",
            right=literal("FLOAT", "2.5"),
        )

        with self.assertRaises(InvalidTypeOperationError):
            checker._check_expression(expression)

    def test_invalid_numeric_operation_is_rejected(self) -> None:
        checker = TypeChecker()

        expression = BinaryExpression(
            position=POSITION,
            left=literal("BOOL", "true"),
            operator="*",
            right=literal("INTEGER", "2"),
        )

        with self.assertRaises(InvalidTypeOperationError):
            checker._check_expression(expression)


if __name__ == "__main__":
    unittest.main()
