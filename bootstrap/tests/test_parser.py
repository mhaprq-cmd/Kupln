```python
"""Tests for the Kupln bootstrap parser."""

from __future__ import annotations

import unittest

from bootstrap.lexer.lexer import Lexer
from bootstrap.parser.ast import (
    ArrayExpression,
    AssignmentExpression,
    BinaryExpression,
    Block,
    CallExpression,
    ClassDeclaration,
    CompilationUnit,
    ConditionalExpression,
    ExportDeclaration,
    ExpressionStatement,
    FieldDeclaration,
    ForStatement,
    FunctionDeclaration,
    IdentifierExpression,
    IfStatement,
    ImportDeclaration,
    IndexExpression,
    InterfaceDeclaration,
    LiteralExpression,
    MemberAccessExpression,
    NewExpression,
    ParenthesizedExpression,
    PostfixExpression,
    RecordDeclaration,
    ReturnStatement,
    StructDeclaration,
    TryStatement,
    TypeReference,
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
)
from bootstrap.parser.parser import (
    Parser,
    ParserError,
    UnexpectedTokenError,
)


def parse_source(source: str) -> CompilationUnit:
    """Tokenize and parse a complete Kupln source string."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class ParserTests(unittest.TestCase):
    """Validate parsing and AST construction."""

    def test_empty_source_returns_empty_compilation_unit(self) -> None:
        unit = parse_source("")

        self.assertIsInstance(unit, CompilationUnit)
        self.assertEqual(unit.items, ())

    def test_variable_declaration_with_type_and_initializer(self) -> None:
        unit = parse_source("let count: Int = 42;")

        self.assertEqual(len(unit.items), 1)

        declaration = unit.items[0]
        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(declaration.keyword, "let")
        self.assertEqual(declaration.name.name, "count")
        self.assertIsInstance(
            declaration.type_annotation,
            TypeReference,
        )
        self.assertEqual(
            declaration.type_annotation.parts[0].name,
            "Int",
        )
        self.assertIsInstance(
            declaration.initializer,
            LiteralExpression,
        )
        self.assertEqual(declaration.initializer.value, "42")

    def test_variable_without_type_or_initializer(self) -> None:
        unit = parse_source("var item;")

        declaration = unit.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(declaration.keyword, "var")
        self.assertIsNone(declaration.type_annotation)
        self.assertIsNone(declaration.initializer)

    def test_function_declaration(self) -> None:
        unit = parse_source(
            "function add(left: Int, right: Int): Int { "
            "return left + right; "
            "}"
        )

        function = unit.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(function.name.name, "add")
        self.assertEqual(len(function.parameters), 2)
        self.assertEqual(
            function.parameters[0].name.name,
            "left",
        )
        self.assertEqual(
            function.parameters[1].name.name,
            "right",
        )
        self.assertEqual(function.return_type.parts[0].name, "Int")
        self.assertIsInstance(function.body, Block)
        self.assertIsInstance(
            function.body.items[0],
            ReturnStatement,
        )

    def test_async_function_declaration(self) -> None:
        unit = parse_source(
            "async function load(): String { return \"ready\"; }"
        )

        function = unit.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertTrue(function.async_modifier)
        self.assertEqual(function.name.name, "load")

    def test_class_with_inheritance_and_members(self) -> None:
        unit = parse_source(
            "class Child extends Base implements Runnable { "
            "value: Int; "
            "function getValue(): Int { return this.value; } "
            "}"
        )

        declaration = unit.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(declaration.name.name, "Child")
        self.assertEqual(declaration.extends.parts[0].name, "Base")
        self.assertEqual(len(declaration.implements), 1)
        self.assertEqual(
            declaration.implements[0].parts[0].name,
            "Runnable",
        )
        self.assertEqual(len(declaration.members), 2)
        self.assertIsInstance(
            declaration.members[0],
            FieldDeclaration,
        )
        self.assertIsInstance(
            declaration.members[1],
            FunctionDeclaration,
        )

    def test_interface_declaration(self) -> None:
        unit = parse_source(
            "interface Runnable { function run(task: Task): Bool; }"
        )

        declaration = unit.items[0]

        self.assertIsInstance(declaration, InterfaceDeclaration)
        self.assertEqual(declaration.name.name, "Runnable")
        self.assertEqual(len(declaration.members), 1)
        self.assertEqual(
            declaration.members[0].name.name,
            "run",
        )
        self.assertEqual(
            declaration.members[0].parameters[0].name.name,
            "task",
        )
        self.assertEqual(
            declaration.members[0].return_type.parts[0].name,
            "Bool",
        )

    def test_struct_and_record_declarations(self) -> None:
        unit = parse_source(
            "struct Point { x: Int; y: Int; } "
            "record User { name: String; }"
        )

        point, user = unit.items

        self.assertIsInstance(point, StructDeclaration)
        self.assertEqual(point.name.name, "Point")
        self.assertEqual(len(point.fields), 2)

        self.assertIsInstance(user, RecordDeclaration)
        self.assertEqual(user.name.name, "User")
        self.assertEqual(len(user.fields), 1)

    def test_import_and_export_declarations(self) -> None:
        unit = parse_source(
            'import "library.kpl"; export class PublicType {}'
        )

        imported, exported = unit.items

        self.assertIsInstance(imported, ImportDeclaration)
        self.assertEqual(imported.path, '"library.kpl"')

        self.assertIsInstance(exported, ExportDeclaration)
        self.assertIsInstance(
            exported.declaration,
            ClassDeclaration,
        )
        self.assertEqual(
            exported.declaration.name.name,
            "PublicType",
        )

    def test_binary_operator_precedence(self) -> None:
        unit = parse_source("let result = 1 + 2 * 3;")

        declaration = unit.items[0]
        expression = declaration.initializer

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")
        self.assertIsInstance(expression.right, BinaryExpression)
        self.assertEqual(expression.right.operator, "*")

    def test_parenthesized_expression(self) -> None:
        unit = parse_source("let result = (1 + 2) * 3;")

        expression = unit.items[0].initializer

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "*")
        self.assertIsInstance(
            expression.left,
            ParenthesizedExpression,
        )

    def test_assignment_expression(self) -> None:
        unit = parse_source("value = 10;")

        statement = unit.items[0]

        self.assertIsInstance(statement, ExpressionStatement)
        self.assertIsInstance(
            statement.expression,
            AssignmentExpression,
        )
        self.assertIsInstance(
            statement.expression.target,
            IdentifierExpression,
        )
        self.assertEqual(
            statement.expression.target.identifier.name,
            "value",
        )

    def test_conditional_expression(self) -> None:
        unit = parse_source("let result = ready ? 1 : 0;")

        expression = unit.items[0].initializer

        self.assertIsInstance(expression, ConditionalExpression)
        self.assertIsInstance(
            expression.condition,
            IdentifierExpression,
        )

    def test_unary_and_postfix_expressions(self) -> None:
        unit = parse_source(
            "let negative = -value; value++;"
        )

        unary = unit.items[0].initializer
        postfix_statement = unit.items[1]

        self.assertIsInstance(unary, UnaryExpression)
        self.assertEqual(unary.operator, "-")

        self.assertIsInstance(
            postfix_statement,
            ExpressionStatement,
        )
        self.assertIsInstance(
            postfix_statement.expression,
            PostfixExpression,
        )
        self.assertEqual(
            postfix_statement.expression.operator,
            "++",
        )

    def test_call_member_and_index_expressions(self) -> None:
        unit = parse_source(
            "let result = service.run(items[0]);"
        )

        expression = unit.items[0].initializer

        self.assertIsInstance(expression, CallExpression)
        self.assertIsInstance(
            expression.callee,
            MemberAccessExpression,
        )
        self.assertEqual(expression.callee.member.name, "run")
        self.assertIsInstance(
            expression.arguments[0],
            IndexExpression,
        )

    def test_array_literal_and_new_expression(self) -> None:
        unit = parse_source(
            "let values = [1, 2]; "
            "let item = new Package.Item(1);"
        )

        array_expression = unit.items[0].initializer
        new_expression = unit.items[1].initializer

        self.assertIsInstance(array_expression, ArrayExpression)
        self.assertEqual(len(array_expression.elements), 2)

        self.assertIsInstance(new_expression, NewExpression)
        self.assertEqual(
            [part.name for part in new_expression.type_reference.parts],
            ["Package", "Item"],
        )
        self.assertEqual(len(new_expression.arguments), 1)

    def test_if_else_statement(self) -> None:
        unit = parse_source(
            "if (ready) { run(); } else { stop(); }"
        )

        statement = unit.items[0]

        self.assertIsInstance(statement, IfStatement)
        self.assertIsNotNone(statement.else_branch)
        self.assertIsInstance(statement.then_branch, Block)
        self.assertIsInstance(statement.else_branch, Block)

    def test_while_and_for_statements(self) -> None:
        unit = parse_source(
            "while (ready) { wait(); } "
            "for (let i: Int = 0; i < 3; i++) { run(); }"
        )

        while_statement, for_statement = unit.items

        self.assertIsInstance(while_statement, WhileStatement)
        self.assertIsInstance(for_statement, ForStatement)
        self.assertIsInstance(
            for_statement.initializer,
            VariableDeclaration,
        )
        self.assertIsNotNone(for_statement.condition)
        self.assertIsNotNone(for_statement.update)

    def test_try_catch_statement(self) -> None:
        unit = parse_source(
            "try { run(); } catch (error) { recover(); }"
        )

        statement = unit.items[0]

        self.assertIsInstance(statement, TryStatement)
        self.assertEqual(statement.catch_name.name, "error")
        self.assertIsInstance(statement.body, Block)
        self.assertIsInstance(statement.catch_body, Block)

    def test_comments_are_ignored(self) -> None:
        unit = parse_source(
            "// comment\nlet value = 1; /* another comment */"
        )

        self.assertEqual(len(unit.items), 1)
        self.assertIsInstance(
            unit.items[0],
            VariableDeclaration,
        )

    def test_syntax_error_raises_parser_error(self) -> None:
        with self.assertRaises(ParserError):
            parse_source("class Alpha {")

    def test_missing_expression_raises_unexpected_token_error(self) -> None:
        with self.assertRaises(UnexpectedTokenError):
            parse_source("let value = ;")


if __name__ == "__main__":
    unittest.main()
```
