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
from bootstrap.lexer.token import TokenKind
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
    SuperExpression,
    ThisExpression,
    TryStatement,
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
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

    def test_comments_are_ignored(self) -> None:
        tree = parse(
            """
            // comment
            let x = 1;
            /* another comment */
            x = 2;
            """
        )

        self.assertEqual(len(tree.items), 2)
        self.assertIsInstance(tree.items[0], VariableDeclaration)
        self.assertIsInstance(tree.items[1], ExpressionStatement)

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

    def test_if_without_else(self) -> None:
        tree = parse(
            """
            if (x) {
                foo();
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, IfStatement)
        self.assertIsNone(statement.else_branch)

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

    def test_for_statement_with_only_condition(self) -> None:
        tree = parse(
            """
            for (; ready; ) {
                work();
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsNone(statement.initializer)
        self.assertIsNotNone(statement.condition)
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


class ParserDeclarationTests(ParserTestCase):
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

    def test_class_with_modifiers(self) -> None:
        tree = parse(
            """
            public final class Person {
                name: String;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(
            declaration.modifiers,
            ("public", "final"),
        )

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

    def test_interface_extends(self) -> None:
        tree = parse(
            """
            interface Child extends Parent {
                function run(): Void;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, InterfaceDeclaration)
        self.assertIsNotNone(declaration.extends)
        self.assertEqual(
            declaration.extends.parts[0].name,
            "Parent",
        )

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

                declaration =
        tree.items[0]

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
        tree = parse("foo;")

        statement = tree.items[0]

        self.assertIsInstance(statement, ExpressionStatement)
        self.assertIsInstance(
            statement.expression,
            IdentifierExpression,
        )
        self.assertEqual(
            statement.expression.identifier.name,
            "foo",
        )

    def test_integer_literal(self) -> None:
        tree = parse("42;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.kind, "integer")
        self.assertEqual(expression.value, "42")

    def test_float_literal(self) -> None:
        tree = parse("3.14;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.kind, "float")
        self.assertEqual(expression.value, "3.14")

    def test_string_literal(self) -> None:
        tree = parse('"hello";')

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.kind, "string")

    def test_char_literal(self) -> None:
        tree = parse("'a';")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.kind, "char")

    def test_boolean_literals(self) -> None:
        tree = parse(
            """
            true;
            false;
            """
        )

        first = tree.items[0].expression
        second = tree.items[1].expression

        self.assertIsInstance(first, LiteralExpression)
        self.assertEqual(first.kind, "true")

        self.assertIsInstance(second, LiteralExpression)
        self.assertEqual(second.kind, "false")

    def test_null_literal(self) -> None:
        tree = parse("null;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.kind, "null")

    def test_binary_expression(self) -> None:
        tree = parse("a + b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")
        self.assertIsInstance(
            expression.left,
            IdentifierExpression,
        )
        self.assertIsInstance(
            expression.right,
            IdentifierExpression,
        )

    def test_assignment_expression(self) -> None:
        tree = parse("x = 10;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            AssignmentExpression,
        )
        self.assertIsInstance(
            expression.target,
            IdentifierExpression,
        )
        self.assertIsInstance(
            expression.value,
            LiteralExpression,
        )

    def test_conditional_expression(self) -> None:
        tree = parse("ready ? 1 : 2;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ConditionalExpression,
        )
        self.assertIsInstance(
            expression.condition,
            IdentifierExpression,
        )

    def test_null_coalescing_expression(self) -> None:
        tree = parse("value ?? fallback;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "??")

    def test_logical_or_precedence(self) -> None:
        tree = parse("a || b && c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "||")
        self.assertIsInstance(expression.right, BinaryExpression)
        self.assertEqual(expression.right.operator, "&&")

    def test_logical_and_precedence(self) -> None:
        tree = parse("a && b == c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "&&")
        self.assertIsInstance(expression.right, BinaryExpression)
        self.assertEqual(expression.right.operator, "==")

    def test_equality_precedence(self) -> None:
        tree = parse("a == b < c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "==")
        self.assertIsInstance(expression.right, BinaryExpression)
        self.assertEqual(expression.right.operator, "<")

    def test_additive_and_multiplicative_precedence(self) -> None:
        tree = parse("a + b * c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")
        self.assertIsInstance(expression.right, BinaryExpression)
        self.assertEqual(expression.right.operator, "*")

    def test_left_associative_addition(self) -> None:
        tree = parse("a + b + c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")
        self.assertIsInstance(expression.left, BinaryExpression)
        self.assertEqual(expression.left.operator, "+")

    def test_parenthesized_expression(self) -> None:
        tree = parse("(a + b) * c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "*")
        self.assertIsInstance(
            expression.left,
            ParenthesizedExpression,
        )

    def test_unary_expression(self) -> None:
        tree = parse("-value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "-")
        self.assertIsInstance(
            expression.operand,
            IdentifierExpression,
        )

    def test_logical_not_expression(self) -> None:
        tree = parse("!ready;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "!")

    def test_prefix_increment_expression(self) -> None:
        tree = parse("++value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "++")

    def test_prefix_decrement_expression(self) -> None:
        tree = parse("--value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "--")

    def test_await_expression(self) -> None:
        tree = parse("await task;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "await")
        self.assertIsInstance(
            expression.operand,
            IdentifierExpression,
        )

    def test_postfix_increment_expression(self) -> None:
        tree = parse("value++;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, PostfixExpression)
        self.assertEqual(expression.operator, "++")

    def test_postfix_decrement_expression(self) -> None:
        tree = parse("value--;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, PostfixExpression)
        self.assertEqual(expression.operator, "--")

    def test_function_call(self) -> None:
        tree = parse("foo(1, 2);")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, CallExpression)
        self.assertEqual(len(expression.arguments), 2)

    def test_empty_function_call(self) -> None:
        tree = parse("foo();")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, CallExpression)
        self.assertEqual(expression.arguments, ())

    def test_member_access(self) -> None:
        tree = parse("object.value;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            MemberAccessExpression,
        )
        self.assertEqual(expression.member.name, "value")

    def test_index_access(self) -> None:
        tree = parse("items[index];")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, IndexExpression)
        self.assertIsInstance(
            expression.index,
            IdentifierExpression,
        )

    def test_chained_postfix_expression(self) -> None:
        tree = parse("object.items[0].value();")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, CallExpression)
        self.assertIsInstance(
            expression.callee,
            MemberAccessExpression,
        )
        self.assertIsInstance(
            expression.callee.object,
            IndexExpression,
        )
        self.assertIsInstance(
            expression.callee.object.object,
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

    def test_new_expression_with_qualified_type(self) -> None:
        tree = parse("new Core.Person();")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, NewExpression)
        self.assertEqual(
            tuple(
                part.name
                for part in expression.type_reference.parts
            ),
            ("Core", "Person"),
        )

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

    def test_this_member_access(self) -> None:
        tree = parse("this.value;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            MemberAccessExpression,
        )
        self.assertIsInstance(
            expression.object,
            ThisExpression,
        )

    def test_right_associative_assignment(self) -> None:
        tree = parse("a = b = c;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            AssignmentExpression,
        )
        self.assertIsInstance(
            expression.value,
            AssignmentExpression,
        )

    def test_right_associative_conditional(self) -> None:
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

    def test_conditional_contains_expression_in_true_branch(self) -> None:
        tree = parse("a ? b + c : d;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ConditionalExpression,
        )
        self.assertIsInstance(
            expression.when_true,
            BinaryExpression,
        )

    def test_comments_inside_expression_are_ignored(self) -> None:
        tree = parse(
            """
            a /* comment */ + /* comment */ b;
            """
        )

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")


class ParserErrorTests(ParserTestCase):
    """Tests for syntax errors."""

    def test_missing_variable_semicolon(self) -> None:
        self.assertSyntaxError("let x = 1")

    def test_missing_expression_semicolon(self) -> None:
        self.assertSyntaxError("x = 1")

    def test_missing_identifier_after_let(self) -> None:
        self.assertSyntaxError("let = 1;")

    def test_missing_type_name(self) -> None:
        self.assertSyntaxError("let value: ;")

    def test_missing_function_name(self) -> None:
        self.assertSyntaxError(
            """
            function () {
                return;
            }
            """
        )

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

    def test_missing_closing_function_brace(self) -> None:
        self.assertSyntaxError(
            """
            function test() {
                return;
            """
        )

    def test_missing_if_parenthesis(self) -> None:
        self.assertSyntaxError(
            """
            if x {
                return;
            }
            """
        )

    def test_missing_if_closing_parenthesis(self) -> None:
        self.assertSyntaxError(
            """
            if (x {
                return;
            }
            """
        )

    def test_missing_while_parenthesis(self) -> None:
        self.assertSyntaxError(
            """
            while x {
                return;
            }
            """
        )

    def test_missing_for_parenthesis(self) -> None:
        self.assertSyntaxError(
            """
            for let i = 0; i < 10; i++ {
                return;
            }
            """
        )

    def test_missing_for_first_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            for (let i = 0 i < 10; i++) {
                return;
            }
            """
        )

    def test_missing_for_second_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            for (let i = 0; i < 10 i++) {
                return;
            }
            """
        )

    def test_missing_for_closing_parenthesis(self) -> None:
        self.assertSyntaxError(
            """
            for (let i = 0; i < 10; i++ {
                return;
            }
            """
        )

    def test_missing_try_block(self) -> None:
        self.assertSyntaxError(
            """
            try
            catch (error) {
                return;
            }
            """
        )

    def test_missing_catch_keyword(self) -> None:
        self.assertSyntaxError(
            """
            try {
                work();
            }
            """
        )

    def test_missing_catch_parameter(self) -> None:
        self.assertSyntaxError(
            """
            try {
                work();
            } catch () {
                recover();
            }
            """
        )

    def test_missing_catch_body(self) -> None:
        self.assertSyntaxError(
            """
            try {
                work();
            } catch (error);
            """
        )

    def test_missing_class_name(self) -> None:
        self.assertSyntaxError(
            """
            class {
                value: Int;
            }
            """
        )

    def test_missing_class_body(self) -> None:
        self.assertSyntaxError("class Person")

    def test_invalid_class_member(self) -> None:
        self.assertSyntaxError(
            """
            class Person {
                let value = 1;
            }
            """
        )

    def test_missing_class_field_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            class Person {
                value: Int
            }
            """
        )

    def test_missing_interface_keyword(self) -> None:
        self.assertSyntaxError(
            """
            interface Test {
                run();
            }
            """
        )

    def test_missing_interface_member_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            interface Test {
                function run()
            }
            """
        )

    def test_missing_struct_field_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            struct Point {
                x: Int
                y: Int;
            }
            """
        )

    def test_missing_record_field_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            record User {
                id: Int
                name: String;
            }
            """
        )

    def test_missing_import_string(self) -> None:
        self.assertSyntaxError("import core;")

    def test_missing_import_semicolon(self) -> None:
        self.assertSyntaxError('import "core/io"')

    def test_missing_export_declaration(self) -> None:
        self.assertSyntaxError("export;")

    def test_invalid_primary_expression(self) -> None:
        self.assertSyntaxError("@;")

    def test_missing_closing_parenthesis(self) -> None:
        self.assertSyntaxError("(1 + 2;")

    def test_missing_closing_array_bracket(self) -> None:
        self.assertSyntaxError("[1, 2;")

    def test_missing_index_closing_bracket(self) -> None:
        self.assertSyntaxError("items[index;")

    def test_missing_call_closing_parenthesis(self) -> None:
        self.assertSyntaxError("foo(1, 2;")

    def test_missing_member_identifier(self) -> None:
        self.assertSyntaxError("object.;")

    def test_missing_conditional_colon(self) -> None:
        self.assertSyntaxError("condition ? a;")

    def test_missing_new_constructor_parenthesis(self) -> None:
        self.assertSyntaxError("new Person;")

    def test_missing_new_constructor_closing_parenthesis(self) -> None:
        self.assertSyntaxError("new Person(1;")

    def test_missing_block_closing_brace(self) -> None:
        self.assertSyntaxError(
            """
            {
                let x = 1;
            """
        )   
def test_missing_try_block(self) -> None:
        self.assertSyntaxError(
            """
            try
                let x = 1;
            catch (error) {
                return;
            }
            """
        )

    def test_missing_catch(self) -> None:
        self.assertSyntaxError(
            """
            try {
                let x = 1;
            }
            """
        )

    def test_missing_catch_parameter(self) -> None:
        self.assertSyntaxError(
            """
            try {
                let x = 1;
            }
            catch () {
                return;
            }
            """
        )

    def test_missing_function_body(self) -> None:
        self.assertSyntaxError("function test();")

    def test_missing_function_parameter_name(self) -> None:
        self.assertSyntaxError("function test(: Int) {}")

    def test_missing_class_name(self) -> None:
        self.assertSyntaxError("class {}")

    def test_missing_class_body(self) -> None:
        self.assertSyntaxError("class User")

    def test_missing_interface_name(self) -> None:
        self.assertSyntaxError("interface {}")

    def test_missing_interface_function_keyword(self) -> None:
        self.assertSyntaxError(
            """
            interface User {
                run();
            }
            """
        )

    def test_missing_struct_name(self) -> None:
        self.assertSyntaxError("struct {}")

    def test_missing_record_name(self) -> None:
        self.assertSyntaxError("record {}")

    def test_missing_parameter_comma(self) -> None:
        self.assertSyntaxError(
            """
            function test(a: Int b: String) {}
            """
        )

    def test_missing_variable_name(self) -> None:
        self.assertSyntaxError("let = 1;")

    def test_missing_variable_semicolon(self) -> None:
        self.assertSyntaxError("let value = 1")

    def test_missing_expression_semicolon(self) -> None:
        self.assertSyntaxError("value = 1")

    def test_missing_return_semicolon(self) -> None:
        self.assertSyntaxError("return value")

    def test_missing_if_parentheses(self) -> None:
        self.assertSyntaxError("if value {}")

    def test_missing_if_closing_parenthesis(self) -> None:
        self.assertSyntaxError("if (value {}")

    def test_missing_while_parentheses(self) -> None:
        self.assertSyntaxError("while value {}")

    def test_missing_for_parentheses(self) -> None:
        self.assertSyntaxError("for let i = 0; i < 10; i++ {}")

    def test_missing_for_semicolon(self) -> None:
        self.assertSyntaxError("for (let i = 0 i < 10; i++) {}")

    def test_missing_for_closing_parenthesis(self) -> None:
        self.assertSyntaxError("for (let i = 0; i < 10; i++ {}")

    def test_missing_class_field_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            class User {
                name: String
            }
            """
        )

    def test_missing_struct_field_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            struct User {
                id: Int
                name: String;
            }
            """
        )

    def test_missing_record_field_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            record User {
                id: Int
                name: String;
            }
            """
        )

    def test_missing_import_string(self) -> None:
        self.assertSyntaxError("import core;")

    def test_missing_import_semicolon(self) -> None:
        self.assertSyntaxError('import "core/io"')

    def test_missing_export_declaration(self) -> None:
        self.assertSyntaxError("export;")

    def test_invalid_primary_expression(self) -> None:
        self.assertSyntaxError("@;")

    def test_missing_closing_parenthesis(self) -> None:
        self.assertSyntaxError("(1 + 2;")

    def test_missing_closing_array_bracket(self) -> None:
        self.assertSyntaxError("[1, 2;")

    def test_missing_index_closing_bracket(self) -> None:
        self.assertSyntaxError("items[index;")

    def test_missing_call_closing_parenthesis(self) -> None:
        self.assertSyntaxError("foo(1, 2;")

    def test_missing_member_identifier(self) -> None:
        self.assertSyntaxError("object.;")

    def test_missing_conditional_colon(self) -> None:
        self.assertSyntaxError("condition ? a;")

    def test_missing_new_constructor_parenthesis(self) -> None:
        self.assertSyntaxError("new Person;")

    def test_missing_new_constructor_closing_parenthesis(self) -> None:
        self.assertSyntaxError("new Person(1;")

    def test_missing_block_closing_brace(self) -> None:
        self.assertSyntaxError(
            """
            {
                let x = 1;
            """
        )

    def test_error_contains_source_position(self) -> None:
        with self.assertRaises(UnexpectedTokenError) as context:
            self.parse("let = 1;")

        message = str(context.exception)

        self.assertIn("1:5", message)
        self.assertIn("offset 4", message)


class ParserIntegrationTests(ParserTestCase):
    """Tests for larger parser combinations."""

    def test_complete_small_program(self) -> None:
        source = """
            import "core/io";

            export function main(name: String): Int {
                let count: Int = 0;

                if (name != null) {
                    count = 1;
                }

                return count;
            }
        """

        unit = self.parse(source)

        self.assertEqual(len(unit.items), 2)

        self.assertIsInstance(unit.items[0], ImportDeclaration)
        self.assertIsInstance(unit.items[1], ExportDeclaration)

        export = unit.items[1]
        self.assertIsInstance(export, ExportDeclaration)
        self.assertIsInstance(export.declaration, FunctionDeclaration)

        function = export.declaration
        self.assertEqual(function.name.name, "main")
        self.assertEqual(len(function.parameters), 1)
        self.assertEqual(function.parameters[0].name.name, "name")
        self.assertIsNotNone(function.return_type)
        self.assertEqual(function.return_type.parts[0].name, "Int")

        self.assertEqual(len(function.body.items), 3)
        self.assertIsInstance(function.body.items[0], VariableDeclaration)
        self.assertIsInstance(function.body.items[1], IfStatement)
        self.assertIsInstance(function.body.items[2], ReturnStatement)

    def test_nested_calls_and_member_access(self) -> None:
        source = """
            service.client.request(data).result;
        """

        unit = self.parse(source)

        statement = unit.items[0]
        self.assertIsInstance(statement, ExpressionStatement)
        self.assertIsInstance(statement.expression, MemberAccessExpression)

        expression = statement.expression
        self.assertEqual(expression.member.name, "result")

        self.assertIsInstance(expression.object, CallExpression)

        call = expression.object
        self.assertIsInstance(call.callee, MemberAccessExpression)

    def test_async_function_with_await(self) -> None:
        source = """
            async function load(): Result {
                let value = await fetch();
                return value;
            }
        """

        unit = self.parse(source)

        function = unit.items[0]
        self.assertIsInstance(function, FunctionDeclaration)
        self.assertTrue(function.async_modifier)

        declaration = function.body.items[0]
        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertIsInstance(declaration.initializer, UnaryExpression)

        self.assertEqual(declaration.initializer.operator, "await")
        self.assertIsInstance(
            declaration.initializer.operand,
            CallExpression,
        )


class ParserTokenBoundaryTests(ParserTestCase):
    """Tests for parser interaction with lexical token boundaries."""

    def test_comments_are_ignored(self) -> None:
        source = """
            // comment
            let value = 1;

            /*
             * block comment
             */
            value = value + 1;
        """

        unit = self.parse(source)

        self.assertEqual(len(unit.items), 2)
        self.assertIsInstance(unit.items[0], VariableDeclaration)
        self.assertIsInstance(unit.items[1], ExpressionStatement)

    def test_eof_is_consumed_as_compilation_boundary(self) -> None:
        unit = self.parse("let value = 1;")

        self.assertIsInstance(unit, CompilationUnit)
        self.assertEqual(len(unit.items), 1)

    def test_unknown_token_is_rejected(self) -> None:
        source = "let value = 1 @ 2;"

        with self.assertRaises(UnexpectedTokenError):
            self.parse(source)


if __name__ == "__main__":
    unittest.main()
