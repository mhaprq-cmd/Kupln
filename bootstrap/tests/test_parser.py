"""Tests for the Kupln bootstrap parser."""

import unittest

from bootstrap.lexer.lexer import Lexer
from bootstrap.parser.ast import (
    ArrayExpression,
    AssignmentExpression,
    BinaryExpression,
    CallExpression,
    ClassDeclaration,
    ConditionalExpression,
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
    ReturnStatement,
    StructDeclaration,
    SuperExpression,
    ThisExpression,
    TryStatement,
    TypeReference,
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
)
from bootstrap.parser.parser import Parser, ParserError


def parse(source: str):
    """Lex and parse a Kupln source string."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class ParserTestCase(unittest.TestCase):
    """Common helpers for parser tests."""

    def first(self, source: str):
        return parse(source).items[0]


class ParserDeclarationTests(ParserTestCase):
    """Tests for declarations."""

    def test_variable_without_initializer(self):
        node = self.first("let value;")
        self.assertIsInstance(node, VariableDeclaration)
        self.assertEqual(node.keyword, "let")
        self.assertEqual(node.name.name, "value")
        self.assertIsNone(node.initializer)

    def test_variable_with_initializer(self):
        node = self.first("var value = 42;")
        self.assertIsInstance(node, VariableDeclaration)
        self.assertEqual(node.keyword, "var")
        self.assertIsInstance(node.initializer, LiteralExpression)
        self.assertEqual(node.initializer.value, "42")

    def test_variable_with_type(self):
        node = self.first("let value: Number;")
        self.assertIsInstance(node, VariableDeclaration)
        self.assertIsInstance(node.type_annotation, TypeReference)
        self.assertEqual(
            tuple(part.name for part in node.type_annotation.parts),
            ("Number",),
        )

    def test_qualified_type(self):
        node = self.first("let value: Core.Types.Value;")
        self.assertIsInstance(node, VariableDeclaration)
        self.assertIsNotNone(node.type_annotation)
        self.assertEqual(
            tuple(part.name for part in node.type_annotation.parts),
            ("Core", "Types", "Value"),
        )

    def test_function(self):
        node = self.first(
            """
            function add(a: Number, b: Number): Number {
                return a + b;
            }
            """
        )
        self.assertIsInstance(node, FunctionDeclaration)
        self.assertEqual(node.name.name, "add")
        self.assertEqual(len(node.parameters), 2)
        self.assertIsNotNone(node.return_type)
        self.assertEqual(len(node.body.items), 1)

    def test_async_function(self):
        node = self.first(
            """
            async function load(): Value {
                return value;
            }
            """
        )
        self.assertIsInstance(node, FunctionDeclaration)
        self.assertTrue(node.async_modifier)

    def test_function_modifiers(self):
        node = self.first(
            """
            public static function run() {
                return;
            }
            """
        )
        self.assertIsInstance(node, FunctionDeclaration)
        self.assertEqual(node.modifiers, ("public", "static"))

    def test_class(self):
        node = self.first(
            """
            class Person {
                let name;
                function getName() {
                    return name;
                }
            }
            """
        )
        self.assertIsInstance(node, ClassDeclaration)
        self.assertEqual(node.name.name, "Person")
        self.assertEqual(len(node.members), 2)

    def test_class_inheritance(self):
        node = self.first(
            """
            class Child extends Parent implements Printable {
                function print() {
                    return;
                }
            }
            """
        )
        self.assertIsInstance(node, ClassDeclaration)
        self.assertIsNotNone(node.extends)
        self.assertEqual(node.extends.parts[0].name, "Parent")
        self.assertEqual(len(node.implements), 1)

    def test_interface(self):
        node = self.first(
            """
            interface Printable {
                function print(): Value;
            }
            """
        )
        self.assertIsInstance(node, InterfaceDeclaration)
        self.assertEqual(node.name.name, "Printable")
        self.assertEqual(len(node.members), 1)

    def test_struct(self):
        node = self.first(
            """
            struct Point {
                let x: Number;
                let y: Number;
            }
            """
        )
        self.assertIsInstance(node, StructDeclaration)
        self.assertEqual(node.name.name, "Point")
        self.assertEqual(len(node.fields), 2)

    def test_record(self):
        node = self.first(
            """
            record User {
                let id: Number;
                let name: String;
            }
            """
        )
        self.assertEqual(node.name.name, "User")
        self.assertEqual(len(node.fields), 2)


class ParserStatementTests(ParserTestCase):
    """Tests for statements."""

    def test_block(self):
        node = self.first(
            """
            {
                let a = 1;
                let b = 2;
            }
            """
        )
        self.assertEqual(len(node.items), 2)

    def test_expression_statement(self):
        node = self.first("value;")
        self.assertIsInstance(node, ExpressionStatement)
        self.assertIsInstance(node.expression, IdentifierExpression)

    def test_empty_statement(self):
        node = self.first(";")
        self.assertEqual(type(node).__name__, "EmptyStatement")

    def test_return_without_value(self):
        node = self.first(
            """
            function stop() {
                return;
            }
            """
        )
        self.assertIsInstance(node.body.items[0], ReturnStatement)
        self.assertIsNone(node.body.items[0].expression)

    def test_return_with_value(self):
        node = self.first(
            """
            function get() {
                return 123;
            }
            """
        )
        statement = node.body.items[0]
        self.assertIsInstance(statement, ReturnStatement)
        self.assertIsNotNone(statement.expression)

    def test_if(self):
        node = self.first(
            """
            if (value) {
                return;
            } else {
                return;
            }
            """
        )
        self.assertIsInstance(node, IfStatement)
        self.assertIsNotNone(node.else_branch)

    def test_if_without_else(self):
        node = self.first(
            """
            if (value) {
                return;
            }
            """
        )
        self.assertIsInstance(node, IfStatement)
        self.assertIsNone(node.else_branch)

    def test_while(self):
        node = self.first(
            """
            while (ready) {
                value;
            }
            """
        )
        self.assertIsInstance(node, WhileStatement)

    def test_for(self):
        node = self.first(
            """
            for (let i = 0; i < 10; i++) {
                value;
            }
            """
        )
        self.assertIsInstance(node, ForStatement)
        self.assertIsNotNone(node.initializer)
        self.assertIsNotNone(node.condition)
        self.assertIsNotNone(node.update)

    def test_try_catch(self):
        node = self.first(
            """
            try {
                value;
            } catch (error) {
                value;
            }
            """
        )
        self.assertIsInstance(node, TryStatement)
        self.assertEqual(node.catch_name.name, "error")

    def test_import(self):
        node = self.first('import "core";')
        self.assertIsInstance(node, ImportDeclaration)
        self.assertEqual(node.path, '"core"')


class ParserExpressionTests(ParserTestCase):
    """Tests for expressions."""

    def test_integer_literal(self):
        node = self.first("42;")
        self.assertIsInstance(node.expression, LiteralExpression)
        self.assertEqual(node.expression.kind, "INTEGER")

    def test_float_literal(self):
        node = self.first("3.14;")
        self.assertIsInstance(node.expression, LiteralExpression)
        self.assertEqual(node.expression.kind, "FLOAT")

    def test_string_literal(self):
        node = self.first('"hello";')
        self.assertIsInstance(node.expression, LiteralExpression)
        self.assertEqual(node.expression.kind, "STRING")

    def test_boolean_literal(self):
        node = self.first("true;")
        self.assertIsInstance(node.expression, LiteralExpression)
        self.assertEqual(node.expression.value, "true")

    def test_null_literal(self):
        node = self.first("null;")
        self.assertIsInstance(node.expression, LiteralExpression)
        self.assertEqual(node.expression.value, "null")

    def test_identifier(self):
        node = self.first("value;")
        self.assertIsInstance(node.expression, IdentifierExpression)
        self.assertEqual(node.expression.identifier.name, "value")

    def test_this(self):
        node = self.first("this;")
        self.assertIsInstance(node.expression, ThisExpression)

    def test_super(self):
        node = self.first("super;")
        self.assertIsInstance(node.expression, SuperExpression)

    def test_new(self):
        node = self.first("new Person();")
        self.assertIsInstance(node.expression, NewExpression)
        self.assertEqual(node.expression.type_reference.parts[0].name, "Person")

    def test_array(self):
        node = self.first("[1, 2, 3];")
        self.assertIsInstance(node.expression, ArrayExpression)
        self.assertEqual(len(node.expression.elements), 3)

    def test_parenthesized(self):
        node = self.first("(value);")
        self.assertIsInstance(node.expression, ParenthesizedExpression)

    def test_unary(self):
        node = self.first("!ready;")
        self.assertIsInstance(node.expression, UnaryExpression)
        self.assertEqual(node.expression.operator, "!")

    def test_await(self):
        node = self.first("await task;")
        self.assertIsInstance(node.expression, UnaryExpression)
        self.assertEqual(node.expression.operator, "await")

    def test_binary_precedence(self):
        node = self.first("1 + 2 * 3;")
        expression = node.expression
        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")
        self.assertIsInstance(expression.right, BinaryExpression)
        self.assertEqual(expression.right.operator, "*")

    def test_logical_expression(self):
        node = self.first("a || b && c;")
        expression = node.expression
        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "||")
        self.assertEqual(expression.right.operator, "&&")

    def test_null_coalescing(self):
        node = self.first("a ?? b;")
        self.assertIsInstance(node.expression, BinaryExpression)
        self.assertEqual(node.expression.operator, "??")

    def test_assignment(self):
        node = self.first("value = 10;")
        self.assertIsInstance(node.expression, AssignmentExpression)
        self.assertIsInstance(node.expression.target, IdentifierExpression)

    def test_conditional(self):
        node = self.first("ready ? yes : no;")
        self.assertIsInstance(node.expression, ConditionalExpression)

    def test_call(self):
        node = self.first("print(value);")
        self.assertIsInstance(node.expression, CallExpression)
        self.assertEqual(len(node.expression.arguments), 1)

    def test_member_access(self):
        node = self.first("user.name;")
        self.assertIsInstance(node.expression, MemberAccessExpression)
        self.assertEqual(node.expression.member.name, "name")

    def test_index_access(self):
        node = self.first("items[index];")
        self.assertIsInstance(node.expression, IndexExpression)

    def test_chained_postfix(self):
        node = self.first("user.getName().value;")
        expression = node.expression
        self.assertIsInstance(expression, MemberAccessExpression)
        self.assertIsInstance(expression.object, CallExpression)

    def test_postfix_increment(self):
        node = self.first("counter++;")
        expression = node.expression
        self.assertEqual(expression.operator, "++")


class ParserSyntaxErrorTests(ParserTestCase):
    """Tests for invalid syntax."""

    def assertSyntaxError(self, source: str):
        with self.assertRaises(ParserError):
            parse(source)

    def test_missing_semicolon(self):
        self.assertSyntaxError("let value")

    def test_missing_expression(self):
        self.assertSyntaxError("let value = ;")

    def test_missing_closing_parenthesis(self):
        self.assertSyntaxError(
            """
            if (value {
                return;
            }
            """
        )

    def test_missing_block(self):
        self.assertSyntaxError("function test()")

    def test_missing_catch_name(self):
        self.assertSyntaxError(
            """
            try {
                value;
            } catch {
                value;
            }
            """
        )

    def test_invalid_for_syntax(self):
        self.assertSyntaxError(
            """
            for (let i = 0; i < 10) {
                value;
            }
            """
        )


class ParserIntegrationTests(ParserTestCase):
    """Tests combining multiple syntax features."""

    def test_complete_small_program(self):
        tree = parse(
            """
            import "core";

            public function main(): Number {
                let value: Number = 10;

                if (value > 0) {
                    return value;
                } else {
                    return 0;
                }
            }
            """
        )

        self.assertEqual(len(tree.items), 2)
        self.assertIsInstance(tree.items[0], ImportDeclaration)
        self.assertIsInstance(tree.items[1], FunctionDeclaration)

    def test_unicode_identifiers(self):
        tree = parse(
            """
            let قيمة = 10;
            قيمة;
            """
        )
        self.assertEqual(len(tree.items), 2)
        self.assertEqual(tree.items[0].name.name, "قيمة")

    def test_comments_are_ignored(self):
        tree = parse(
            """
            // comment
            let value = 1;
            /* comment */
            value;
            """
        )
        self.assertEqual(len(tree.items), 2)

    def test_multiple_top_level_items(self):
        tree = parse(
            """
            let a = 1;
            let b = 2;

            function sum() {
                return a + b;
            }

            class Box {
                let value;
            }
            """
        )
        self.assertEqual(len(tree.items), 4)

    def test_nested_expression(self):
        tree = parse(
            """
            result = (a + b) * (c - d);
            """
        )
        expression = tree.items[0].expression
        self.assertIsInstance(expression, AssignmentExpression)
        self.assertIsInstance(expression.value, BinaryExpression)

    def test_async_await_program(self):
        tree = parse(
            """
            async function load() {
                let result = await request();
                return result;
            }
            """
        )
        function = tree.items[0]
        self.assertTrue(function.async_modifier)
        statement = function.body.items[0]
        self.assertIsInstance(statement, VariableDeclaration)
        self.assertIsInstance(statement.initializer, UnaryExpression)
        self.assertEqual(statement.initializer.operator, "await")


if __name__ == "__main__":
    unittest.main()
