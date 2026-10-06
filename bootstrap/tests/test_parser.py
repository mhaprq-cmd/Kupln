"""Tests for the Kupln bootstrap parser.

These tests verify that the parser:
    - accepts valid Kupln syntax
    - constructs the expected AST node types
    - respects expression precedence
    - ignores comments as syntax trivia
    - rejects invalid syntax
"""

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
    EmptyStatement,
    ExportDeclaration,
    ExpressionStatement,
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
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
    ForStatement,
    ThisExpression,
    SuperExpression,
)


from bootstrap.parser.parser import Parser, UnexpectedTokenError


def parse(source: str) -> CompilationUnit:
    """Lex and parse a Kupln source string."""

    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class ParserTestCase(unittest.TestCase):
    """Common parser test helpers."""

    def assertSyntaxError(self, source: str) -> None:
        """Assert that source produces a parser syntax error."""

        with self.assertRaises(UnexpectedTokenError):
            parse(source)


class ParserCompilationUnitTests(ParserTestCase):
    """Tests for compilation units and top-level constructs."""

    def test_empty_compilation_unit(self) -> None:
        tree = parse("")

        self.assertIsInstance(tree, CompilationUnit)
        self.assertEqual(tree.items, ())

    def test_multiple_top_level_items(self) -> None:
        tree = parse(
            """
            let x = 1;
            let y = 2;
            x = y;
            """
        )

        self.assertEqual(len(tree.items), 3)
        self.assertIsInstance(tree.items[0], VariableDeclaration)
        self.assertIsInstance(tree.items[1], VariableDeclaration)
        self.assertIsInstance(tree.items[2], ExpressionStatement)

    def test_import_declaration(self) -> None:
        tree = parse('import "core/io";')

        self.assertEqual(len(tree.items), 1)
        self.assertIsInstance(tree.items[0], ImportDeclaration)
        self.assertEqual(tree.items[0].path, '"core/io"')

    def test_export_declaration(self) -> None:
        tree = parse(
            """
            export function greet() {
                return;
            }
            """
        )

        self.assertEqual(len(tree.items), 1)
        self.assertIsInstance(tree.items[0], ExportDeclaration)
        self.assertIsInstance(
            tree.items[0].declaration,
            FunctionDeclaration,
        )


class ParserVariableTests(ParserTestCase):
    """Tests for variable declarations."""

    def test_let_variable(self) -> None:
        tree = parse("let x = 10;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(declaration.keyword, "let")
        self.assertEqual(declaration.name.name, "x")
        self.assertIsInstance(
            declaration.initializer,
            LiteralExpression,
        )

    def test_var_variable_with_type(self) -> None:
        tree = parse("var count: Int = 42;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(declaration.keyword, "var")
        self.assertEqual(declaration.name.name, "count")
        self.assertIsNotNone(declaration.type_annotation)
        self.assertEqual(
            declaration.type_annotation.parts[0].name,
            "Int",
        )

    def test_variable_without_initializer(self) -> None:
        tree = parse("let value: Int;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertIsNone(declaration.initializer)

    def test_variable_modifiers(self) -> None:
        tree = parse("public static let value = 1;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(
            declaration.modifiers,
            ("public", "static"),
        )


class ParserFunctionTests(ParserTestCase):
    """Tests for function declarations."""

    def test_function_without_parameters(self) -> None:
        tree = parse(
            """
            function greet() {
                return;
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(function.name.name, "greet")
        self.assertEqual(function.parameters, ())
        self.assertIsInstance(function.body, Block)
        self.assertEqual(len(function.body.items), 1)
        self.assertIsInstance(
            function.body.items[0],
            ReturnStatement,
        )

    def test_function_with_parameters_and_return_type(self) -> None:
        tree = parse(
            """
            function add(a: Int, b: Int): Int {
                return a + b;
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(function.name.name, "add")
        self.assertEqual(len(function.parameters), 2)
        self.assertEqual(function.parameters[0].name.name, "a")
        self.assertEqual(function.parameters[1].name.name, "b")
        self.assertIsNotNone(function.return_type)
        self.assertEqual(function.return_type.parts[0].name, "Int")

    def test_async_function(self) -> None:
        tree = parse(
            """
            async function load() {
                return;
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertTrue(function.async_modifier)

    def test_function_modifiers(self) -> None:
        tree = parse(
            """
            public static function compute() {
                return;
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(
            function.modifiers,
            ("public", "static"),
        )


class ParserStatementTests(ParserTestCase):
    """Tests for statements."""

    def test_block_statement(self) -> None:
        tree = parse(
            """
            {
                let x = 1;
                x = 2;
            }
            """
        )

        block = tree.items[0]

        self.assertIsInstance(block, Block)
        self.assertEqual(len(block.items), 2)

    def test_empty_statement(self) -> None:
        tree = parse(";")

        self.assertIsInstance(tree.items[0], EmptyStatement)

    def test_expression_statement(self) -> None:
        tree = parse("foo();")

        statement = tree.items[0]

        self.assertIsInstance(statement, ExpressionStatement)
        self.assertIsInstance(statement.expression, CallExpression)

    def test_return_without_expression(self) -> None:
        tree = parse(
            """
            function stop() {
                return;
            }
            """
        )

        function = tree.items[0]
        statement = function.body.items[0]

        self.assertIsInstance(statement, ReturnStatement)
        self.assertIsNone(statement.expression)

    def test_return_with_expression(self) -> None:
        tree = parse(
            """
            function get() {
                return 42;
            }
            """
        )

        function = tree.items[0]
        statement = function.body.items[0]

        self.assertIsInstance(statement, ReturnStatement)
        self.assertIsInstance(
            statement.expression,
            LiteralExpression,
        )

    def test_if_statement(self) -> None:
        tree = parse(
            """
            if (x > 0) {
                return;
            } else {
                return;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, IfStatement)
        self.assertIsNotNone(statement.else_branch)

    def test_while_statement(self) -> None:
        tree = parse(
            """
            while (x > 0) {
                x--;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, WhileStatement)
        self.assertIsInstance(statement.body, Block)

    def test_for_statement_with_variable_initializer(self) -> None:
        tree = parse(
            """
            for (let i = 0; i < 10; i++) {
                foo(i);
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsInstance(
            statement.initializer,
            VariableDeclaration,
        )
        self.assertIsInstance(statement.condition, BinaryExpression)
        self.assertIsInstance(statement.update, PostfixExpression)

    def test_for_statement_with_expression_initializer(self) -> None:
        tree = parse(
            """
            for (i = 0; i < 10; i++) {
                foo(i);
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsInstance(
            statement.initializer,
            ExpressionStatement,
        )

    def test_for_statement_with_empty_clauses(self) -> None:
        tree = parse(
            """
            for (;;) {
                return;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsNone(statement.initializer)
        self.assertIsNone(statement.condition)
        self.assertIsNone(statement.update)

    def test_try_catch_statement(self) -> None:
        tree = parse(
            """
            try {
                foo();
            } catch (error) {
                bar(error);
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, TryStatement)
        self.assertEqual(statement.catch_name.name, "error")


class ParserTypeAndDeclarationTests(ParserTestCase):
    """Tests for classes, interfaces, structs, and records."""

    def test_class_with_field_and_method(self) -> None:
        tree = parse(
            """
            class Person {
                name: String;

                function greet() {
                    return;
                }
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(declaration.name.name, "Person")
        self.assertEqual(len(declaration.members), 2)

    def test_class_extends_and_implements(self) -> None:
        tree = parse(
            """
            class Child extends Parent implements Printable, Serializable {
                value: Int;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertIsNotNone(declaration.extends)
        self.assertEqual(
            declaration.extends.parts[0].name,
            "Parent",
        )
        self.assertEqual(len(declaration.implements), 2)

    def test_interface(self) -> None:
        tree = parse(
            """
            interface Printable {
                function print(value: String): Void;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, InterfaceDeclaration)
        self.assertEqual(declaration.name.name, "Printable")
        self.assertEqual(len(declaration.members), 1)

    def test_struct(self) -> None:
        tree = parse(
            """
            struct Point {
                x: Int;
                y: Int;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, StructDeclaration)
        self.assertEqual(declaration.name.name, "Point")
        self.assertEqual(len(declaration.fields), 2)

    def test_record(self) -> None:
        tree = parse(
            """
            record User {
                id: Int;
                name: String;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, RecordDeclaration)
        self.assertEqual(declaration.name.name, "User")
        self.assertEqual(len(declaration.fields), 2)

    def test_qualified_type_reference(self) -> None:
        tree = parse(
            """
            let value: Core.Types.Value;
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertIsNotNone(declaration.type_annotation)

        parts = declaration.type_annotation.parts

        self.assertEqual(
            tuple(part.name for part in parts),
            ("Core", "Types", "Value"),
        )
        class ParserExpressionTests(ParserTestCase):
    """Tests for expressions."""

    def test_identifier_expression(self) -> None:
        tree = parse("value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, IdentifierExpression)
        self.assertEqual(
            expression.identifier.name,
            "value",
        )

    def test_literal_expressions(self) -> None:
        tree = parse(
            """
            123;
            3.14;
            "hello";
            'x';
            true;
            false;
            null;
            """
        )

        self.assertEqual(len(tree.items), 7)

        for item in tree.items:
            self.assertIsInstance(item, ExpressionStatement)
            self.assertIsInstance(
                item.expression,
                LiteralExpression,
            )

    def test_binary_expression(self) -> None:
        tree = parse("a + b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")

    def test_assignment_expression(self) -> None:
        tree = parse("x = 10;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            AssignmentExpression,
        )

    def test_conditional_expression(self) -> None:
        tree = parse("x > 0 ? 1 : 2;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ConditionalExpression,
        )

    def test_null_coalescing_expression(self) -> None:
        tree = parse("value ?? fallback;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "??")

    def test_logical_precedence(self) -> None:
        tree = parse("a && b || c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "||")
        self.assertIsInstance(expression.left, BinaryExpression)
        self.assertEqual(expression.left.operator, "&&")

    def test_arithmetic_precedence(self) -> None:
        tree = parse("a + b * c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")
        self.assertIsInstance(expression.right, BinaryExpression)
        self.assertEqual(expression.right.operator, "*")

    def test_parenthesized_expression(self) -> None:
        tree = parse("(a + b) * c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertIsInstance(
            expression.left,
            ParenthesizedExpression,
        )

    def test_unary_expression(self) -> None:
        tree = parse("!value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "!")

    def test_await_expression(self) -> None:
        tree = parse("await load();")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "await")
        self.assertIsInstance(
            expression.operand,
            CallExpression,
        )

    def test_prefix_increment(self) -> None:
        tree = parse("++value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "++")

    def test_postfix_increment(self) -> None:
        tree = parse("value++;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, PostfixExpression)
        self.assertEqual(expression.operator, "++")

    def test_function_call(self) -> None:
        tree = parse("add(1, 2);")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, CallExpression)
        self.assertEqual(len(expression.arguments), 2)

    def test_member_access(self) -> None:
        tree = parse("user.name;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            MemberAccessExpression,
        )
        self.assertEqual(expression.member.name, "name")

    def test_index_access(self) -> None:
        tree = parse("items[index];")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, IndexExpression)
        self.assertIsInstance(
            expression.index,
            IdentifierExpression,
        )

    def test_chained_postfix_expression(self) -> None:
        tree = parse("users[0].name.toString();")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, CallExpression)
        self.assertIsInstance(
            expression.callee,
            MemberAccessExpression,
        )

    def test_new_expression(self) -> None:
        tree = parse("new Person(name);")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, NewExpression)
        self.assertEqual(
            expression.type_reference.parts[0].name,
            "Person",
        )
        self.assertEqual(len(expression.arguments), 1)

    def test_array_expression(self) -> None:
        tree = parse("[1, 2, 3];")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, ArrayExpression)
        self.assertEqual(len(expression.elements), 3)

    def test_empty_array_expression(self) -> None:
        tree = parse("[];")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, ArrayExpression)
        self.assertEqual(expression.elements, ())

    def test_this_expression(self) -> None:
        tree = parse("this;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, ThisExpression)

    def test_super_expression(self) -> None:
        tree = parse("super;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, SuperExpression)

    def test_assignment_is_right_associative(self) -> None:
        tree = parse("a = b = c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, AssignmentExpression)
        self.assertIsInstance(
            expression.value,
            AssignmentExpression,
        )

    def test_conditional_is_right_associative(self) -> None:
        tree = parse("a ? b : c ? d : e;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ConditionalExpression,
        )
        self.assertIsInstance(
            expression.when_false,
            ConditionalExpression,
        )

    def test_comments_are_ignored(self) -> None:
        tree = parse(
            """
            // first comment
            let x = 1;

            /*
                second comment
            */

            x + 2;
            """
        )

        self.assertEqual(len(tree.items), 2)


class ParserErrorTests(ParserTestCase):
    """Tests for syntax errors."""

    def test_missing_semicolon_after_variable(self) -> None:
        self.assertSyntaxError("let x = 1")

    def test_missing_identifier_after_let(self) -> None:
        self.assertSyntaxError("let = 1;")

    def test_missing_function_parenthesis(self) -> None:
        self.assertSyntaxError(
            """
            function test {
                return;
            }
            """
        )

    def test_missing_function_body(self) -> None:
        self.assertSyntaxError(
            """
            function test();
            """
        )

    def test_missing_if_closing_parenthesis(self) -> None:
        self.assertSyntaxError(
            """
            if (x > 0 {
                return;
            }
            """
        )

    def test_missing_block_closing_brace(self) -> None:
        self.assertSyntaxError(
            """
            function test() {
                return;
            """
        )

    def test_missing_for_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            for (let i = 0 i < 10; i++) {
                return;
            }
            """
        )

    def test_missing_catch(self) -> None:
        self.assertSyntaxError(
            """
            try {
                foo();
            }
            """
        )

    def test_missing_interface_function_keyword(self) -> None:
        self.assertSyntaxError(
            """
            interface Test {
                run();
            }
            """
        )

    def test_missing_class_member_terminator(self) -> None:
        self.assertSyntaxError(
            """
            class Test {
                value: Int
            }
            """
        )

    def test_invalid_import(self) -> None:
        self.assertSyntaxError("import core;")

    def test_invalid_expression(self) -> None:
        self.assertSyntaxError("; +;")

    def test_unclosed_parenthesized_expression(self) -> None:
        self.assertSyntaxError("(1 + 2;")

    def test_unclosed_array_expression(self) -> None:
        self.assertSyntaxError("[1, 2;")

    def test_missing_constructor_parenthesis(self) -> None:
        self.assertSyntaxError("new Person;")

    def test_missing_conditional_colon(self) -> None:
        self.assertSyntaxError("x ? 1;")

    def test_missing_index_closing_bracket(self) -> None:
        self.assertSyntaxError("items[0;")

    def test_missing_call_closing_parenthesis(self) -> None:
        self.assertSyntaxError("foo(1, 2;")

    def test_error_contains_source_position(self) -> None:
        with self.assertRaises(UnexpectedTokenError) as context:
            parse("let = 1;")

        message = str(context.exception)

        self.assertIn("1:5", message)
        self.assertIn("offset", message)


if __name__ == "__main__":
    unittest.main()
