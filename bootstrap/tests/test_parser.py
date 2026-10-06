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
    ConditionalExpression,
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
    SuperExpression,
    ThisExpression,
    TryStatement,
    TypeReference,
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
    ForStatement,
)
from bootstrap.parser.parser import Parser, ParserError


def parse(source: str):
    """Parse Kupln source and return the compilation unit."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class ParserTestCase(unittest.TestCase):
    """Common helpers for parser tests."""

    def assertSyntaxError(self, source: str) -> None:
        """Assert that parsing source raises a syntax error."""
        with self.assertRaises(ParserError):
            parse(source)


class ParserCompilationTests(ParserTestCase):
    """Tests for compilation units."""

    def test_empty_source(self) -> None:
        tree = parse("")

        self.assertEqual(len(tree.items), 0)

    def test_comments_only(self) -> None:
        tree = parse(
            """
            // comment
            /* another comment */
            """
        )

        self.assertEqual(len(tree.items), 0)

    def test_multiple_top_level_items(self) -> None:
        tree = parse(
            """
            let first = 1;
            let second = 2;
            function main() {
                return first;
            }
            """
        )

        self.assertEqual(len(tree.items), 3)
        self.assertIsInstance(tree.items[0], VariableDeclaration)
        self.assertIsInstance(tree.items[1], VariableDeclaration)
        self.assertIsInstance(tree.items[2], FunctionDeclaration)

    def test_import_is_top_level_item(self) -> None:
        tree = parse('import "core.io";')

        self.assertEqual(len(tree.items), 1)
        self.assertIsInstance(tree.items[0], ImportDeclaration)
        self.assertEqual(tree.items[0].path, '"core.io"')

    def test_comments_are_ignored_between_items(self) -> None:
        tree = parse(
            """
            let a = 1;
            // comment
            let b = 2;
            /* comment */
            let c = 3;
            """
        )

        self.assertEqual(len(tree.items), 3)


class ParserVariableTests(ParserTestCase):
    """Tests for variable declarations."""

    def test_let_without_initializer(self) -> None:
        tree = parse("let value;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(declaration.keyword, "let")
        self.assertEqual(declaration.name.name, "value")
        self.assertIsNone(declaration.initializer)

    def test_var_with_initializer(self) -> None:
        tree = parse("var value = 42;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(declaration.keyword, "var")
        self.assertEqual(declaration.initializer.value, "42")

    def test_variable_with_type(self) -> None:
        tree = parse("let value: Int;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertIsNotNone(declaration.type_annotation)
        self.assertEqual(
            tuple(part.name for part in declaration.type_annotation.parts),
            ("Int",),
        )

    def test_qualified_type_reference(self) -> None:
        tree = parse("let value: Core.Types.Value;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertIsNotNone(declaration.type_annotation)

        parts = declaration.type_annotation.parts

        self.assertEqual(
            tuple(part.name for part in parts),
            ("Core", "Types", "Value"),
        )

    def test_variable_with_type_and_initializer(self) -> None:
        tree = parse("let value: Int = 10;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertIsNotNone(declaration.type_annotation)
        self.assertIsNotNone(declaration.initializer)

    def test_variable_modifiers(self) -> None:
        tree = parse("public static let value = 1;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(
            declaration.modifiers,
            ("public", "static"),
        )

    def test_var_and_let_can_be_used(self) -> None:
        tree = parse(
            """
            let immutableValue = 1;
            var mutableValue = 2;
            """
        )

        first = tree.items[0]
        second = tree.items[1]

        self.assertIsInstance(first, VariableDeclaration)
        self.assertIsInstance(second, VariableDeclaration)
        self.assertEqual(first.keyword, "let")
        self.assertEqual(second.keyword, "var")


class ParserFunctionTests(ParserTestCase):
    """Tests for function declarations."""

    def test_empty_function(self) -> None:
        tree = parse(
            """
            function main() {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, FunctionDeclaration)
        self.assertEqual(declaration.name.name, "main")
        self.assertEqual(len(declaration.parameters), 0)
        self.assertIsInstance(declaration.body, Block)
        self.assertEqual(len(declaration.body.items), 0)

    def test_function_parameters(self) -> None:
        tree = parse(
            """
            function add(a: Int, b: Int) {
                return a + b;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, FunctionDeclaration)
        self.assertEqual(len(declaration.parameters), 2)
        self.assertEqual(declaration.parameters[0].name.name, "a")
        self.assertEqual(declaration.parameters[1].name.name, "b")

    def test_function_return_type(self) -> None:
        tree = parse(
            """
            function getValue(): Int {
                return 1;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, FunctionDeclaration)
        self.assertIsNotNone(declaration.return_type)
        self.assertEqual(
            declaration.return_type.parts[0].name,
            "Int",
        )

    def test_async_function(self) -> None:
        tree = parse(
            """
            async function load() {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, FunctionDeclaration)
        self.assertTrue(declaration.async_modifier)

    def test_function_modifiers(self) -> None:
        tree = parse(
            """
            public static function main() {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, FunctionDeclaration)
        self.assertEqual(
            declaration.modifiers,
            ("public", "static"),
        )

    def test_async_function_with_modifiers(self) -> None:
        tree = parse(
            """
            public async function load() {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, FunctionDeclaration)
        self.assertTrue(declaration.async_modifier)
        self.assertEqual(declaration.modifiers, ("public",))

    def test_function_body_contains_statements(self) -> None:
        tree = parse(
            """
            function main() {
                let value = 1;
                return value;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, FunctionDeclaration)
        self.assertEqual(len(declaration.body.items), 2)
        self.assertIsInstance(
            declaration.body.items[0],
            VariableDeclaration,
        )
        self.assertIsInstance(
            declaration.body.items[1],
            ReturnStatement,
        )


class ParserStatementTests(ParserTestCase):
    """Tests for statements."""

    def test_expression_statement(self) -> None:
        tree = parse("value;")

        statement = tree.items[0]

        self.assertIsInstance(statement, ExpressionStatement)
        self.assertIsInstance(
            statement.expression,
            IdentifierExpression,
        )

    def test_empty_statement(self) -> None:
        tree = parse(";")

        self.assertEqual(len(tree.items), 1)

    def test_return_without_expression(self) -> None:
        tree = parse(
            """
            function main() {
                return;
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)

        statement = function.body.items[0]

        self.assertIsInstance(statement, ReturnStatement)
        self.assertIsNone(statement.expression)

    def test_return_with_expression(self) -> None:
        tree = parse(
            """
            function main() {
                return 42;
            }
            """
        )

        function = tree.items[0]
        statement = function.body.items[0]

        self.assertIsInstance(statement, ReturnStatement)
        self.assertIsNotNone(statement.expression)

    def test_if_statement(self) -> None:
        tree = parse(
            """
            if (value) {
                return;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, IfStatement)
        self.assertIsNotNone(statement.condition)
        self.assertIsInstance(statement.then_branch, Block)
        self.assertIsNone(statement.else_branch)

    def test_if_else_statement(self) -> None:
        tree = parse(
            """
            if (value) {
                return 1;
            } else {
                return 2;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, IfStatement)
        self.assertIsNotNone(statement.else_branch)

    def test_while_statement(self) -> None:
        tree = parse(
            """
            while (running) {
                value;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, WhileStatement)
        self.assertIsInstance(statement.body, Block)

    def test_for_statement(self) -> None:
        tree = parse(
            """
            for (let i = 0; i < 10; i++) {
                value;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsNotNone(statement.initializer)
        self.assertIsNotNone(statement.condition)
        self.assertIsNotNone(statement.update)

    def test_for_with_missing_initializer(self) -> None:
        tree = parse(
            """
            for (; i < 10; i++) {
                value;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsNone(statement.initializer)

    def test_for_with_missing_condition(self) -> None:
        tree = parse(
            """
            for (let i = 0;; i++) {
                value;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsNone(statement.condition)

    def test_for_with_missing_update(self) -> None:
        tree = parse(
            """
            for (let i = 0; i < 10;) {
                value;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsNone(statement.update)

    def test_try_catch_statement(self) -> None:
        tree = parse(
            """
            try {
                risky();
            } catch (error) {
                handle(error);
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, TryStatement)
        self.assertEqual(statement.catch_name.name, "error")
        self.assertIsInstance(statement.body, Block)
        self.assertIsInstance(statement.catch_body, Block)
        class ParserDeclarationTests(ParserTestCase):
    """Tests for class, interface, struct, and record declarations."""

    def test_class_declaration(self) -> None:
        tree = parse(
            """
            class Person {
                let name: String;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(declaration.name.name, "Person")
        self.assertIsNone(declaration.extends)
        self.assertEqual(len(declaration.implements), 0)
        self.assertEqual(len(declaration.members), 1)

    def test_class_with_extends(self) -> None:
        tree = parse(
            """
            class Child extends Parent {
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

    def test_class_with_implements(self) -> None:
        tree = parse(
            """
            class Child implements Printable, Serializable {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(len(declaration.implements), 2)
        self.assertEqual(
            declaration.implements[0].parts[0].name,
            "Printable",
        )
        self.assertEqual(
            declaration.implements[1].parts[0].name,
            "Serializable",
        )

    def test_class_with_extends_and_implements(self) -> None:
        tree = parse(
            """
            class Child extends Parent implements Printable {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertIsNotNone(declaration.extends)
        self.assertEqual(len(declaration.implements), 1)

    def test_class_modifiers(self) -> None:
        tree = parse(
            """
            public abstract class Person {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(
            declaration.modifiers,
            ("public", "abstract"),
        )

    def test_class_field_with_initializer(self) -> None:
        tree = parse(
            """
            class Person {
                private let age: Int = 20;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        field = declaration.members[0]

        self.assertIsInstance(field, VariableDeclaration)
        self.assertEqual(field.name.name, "age")
        self.assertEqual(field.modifiers, ("private",))
        self.assertIsNotNone(field.initializer)

    def test_class_function_member(self) -> None:
        tree = parse(
            """
            class Person {
                function greet() {
                    return;
                }
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        member = declaration.members[0]

        self.assertIsInstance(member, FunctionDeclaration)
        self.assertEqual(member.name.name, "greet")

    def test_class_multiple_members(self) -> None:
        tree = parse(
            """
            class Person {
                let name: String;
                let age: Int = 18;

                function greet() {
                    return;
                }
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(len(declaration.members), 3)

    def test_interface_declaration(self) -> None:
        tree = parse(
            """
            interface Printable {
                function print(value: String);
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, InterfaceDeclaration)
        self.assertEqual(declaration.name.name, "Printable")
        self.assertEqual(len(declaration.members), 1)

        member = declaration.members[0]

        self.assertIsInstance(member, FunctionDeclaration)
        self.assertEqual(member.name.name, "print")
        self.assertEqual(len(member.body.items), 0)

    def test_interface_extends(self) -> None:
        tree = parse(
            """
            interface Child extends Parent {
                function run();
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

    def test_struct_declaration(self) -> None:
        tree = parse(
            """
            struct Point {
                let x: Int;
                let y: Int;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, StructDeclaration)
        self.assertEqual(declaration.name.name, "Point")
        self.assertEqual(len(declaration.fields), 2)

    def test_record_declaration(self) -> None:
        tree = parse(
            """
            record User {
                let id: Int;
                let name: String;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, RecordDeclaration)
        self.assertEqual(declaration.name.name, "User")
        self.assertEqual(len(declaration.fields), 2)

    def test_qualified_field_type(self) -> None:
        tree = parse(
            """
            class Example {
                let value: Core.Types.Value;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)

        field = declaration.members[0]

        self.assertIsInstance(field, VariableDeclaration)
        self.assertIsNotNone(field.type_annotation)

        self.assertEqual(
            tuple(
                part.name
                for part in field.type_annotation.parts
            ),
            ("Core", "Types", "Value"),
        )

    def test_exported_function(self) -> None:
        tree = parse(
            """
            export function publicApi() {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, type(tree.items[0]))
        self.assertEqual(declaration.declaration.name.name, "publicApi")


class ParserExpressionTests(ParserTestCase):
    """Tests for expressions."""

    def test_integer_literal(self) -> None:
        tree = parse("42;")

        statement = tree.items[0]

        self.assertIsInstance(statement, ExpressionStatement)
        self.assertIsInstance(
            statement.expression,
            LiteralExpression,
        )
        self.assertEqual(statement.expression.kind, "INTEGER")
        self.assertEqual(statement.expression.value, "42")

    def test_float_literal(self) -> None:
        tree = parse("3.14;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.kind, "FLOAT")
        self.assertEqual(expression.value, "3.14")

    def test_string_literal(self) -> None:
        tree = parse('"hello";')

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.kind, "STRING")
        self.assertEqual(expression.value, '"hello"')

    def test_character_literal(self) -> None:
        tree = parse("'A';")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.kind, "CHAR")
        self.assertEqual(expression.value, "'A'")

    def test_boolean_literal(self) -> None:
        tree = parse("true;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.value, "true")

    def test_null_literal(self) -> None:
        tree = parse("null;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.value, "null")

    def test_identifier_expression(self) -> None:
        tree = parse("value;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            IdentifierExpression,
        )
        self.assertEqual(
            expression.identifier.name,
            "value",
        )

    def test_this_expression(self) -> None:
        tree = parse("this;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, ThisExpression)

    def test_super_expression(self) -> None:
        tree = parse("super;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, SuperExpression)

    def test_new_expression(self) -> None:
        tree = parse("new Person();")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, NewExpression)
        self.assertEqual(
            expression.type_reference.parts[0].name,
            "Person",
        )
        self.assertEqual(len(expression.arguments), 0)

    def test_new_expression_with_arguments(self) -> None:
        tree = parse("new Person(1, name);")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, NewExpression)
        self.assertEqual(len(expression.arguments), 2)

    def test_array_expression(self) -> None:
        tree = parse("[1, 2, 3];")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, ArrayExpression)
        self.assertEqual(len(expression.elements), 3)

    def test_empty_array_expression(self) -> None:
        tree = parse("[];")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, ArrayExpression)
        self.assertEqual(len(expression.elements), 0)

    def test_parenthesized_expression(self) -> None:
        tree = parse("(value);")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ParenthesizedExpression,
        )

    def test_unary_expression(self) -> None:
        tree = parse("-value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "-")

    def test_logical_not(self) -> None:
        tree = parse("!value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "!")

    def test_prefix_increment(self) -> None:
        tree = parse("++value;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "++")

    def test_await_expression(self) -> None:
        tree = parse("await load();")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, UnaryExpression)
        self.assertEqual(expression.operator, "await")
        self.assertIsInstance(
            expression.operand,
            CallExpression,
        )

    def test_binary_addition(self) -> None:
        tree = parse("a + b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")

    def test_binary_multiplication(self) -> None:
        tree = parse("a * b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "*")

    def test_binary_comparison(self) -> None:
        tree = parse("a < b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "<")

    def test_binary_equality(self) -> None:
        tree = parse("a == b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "==")

    def test_logical_and(self) -> None:
        tree = parse("a && b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "&&")

    def test_logical_or(self) -> None:
        tree = parse("a || b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "||")

    def test_null_coalescing(self) -> None:
        tree = parse("a ?? b;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "??")

    def test_assignment_expression(self) -> None:
        tree = parse("value = 10;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            AssignmentExpression,
        )
        self.assertEqual(
            expression.value.value,
            "10",
        )

    def test_conditional_expression(self) -> None:
        tree = parse("condition ? a : b;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ConditionalExpression,
        )

    def test_function_call(self) -> None:
        tree = parse("print(value);")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, CallExpression)
        self.assertEqual(len(expression.arguments), 1)

    def test_function_call_without_arguments(self) -> None:
        tree = parse("print();")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, CallExpression)
        self.assertEqual(len(expression.arguments), 0)

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

    def test_postfix_increment(self) -> None:
        tree = parse("value++;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, PostfixExpression)
        self.assertEqual(expression.operator, "++")

    def test_postfix_decrement(self) -> None:
        tree = parse("value--;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, PostfixExpression)
        self.assertEqual(expression.operator, "--")

    def test_chained_member_access(self) -> None:
        tree = parse("object.first.second;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            MemberAccessExpression,
        )
        self.assertEqual(expression.member.name, "second")

    def test_chained_call_and_member_access(self) -> None:
        tree = parse("factory().value;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            MemberAccessExpression,
        )
        self.assertIsInstance(
            expression.object,
            CallExpression,
        )

    def test_call_with_multiple_arguments(self) -> None:
        tree = parse("calculate(a, b, c);")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, CallExpression)
        self.assertEqual(len(expression.arguments), 3)

    def test_nested_expression(self) -> None:
        tree = parse("(a + b) * c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "*")
        self.assertIsInstance(
            expression.left,
            ParenthesizedExpression,
        )

    def test_expression_precedence(self) -> None:
        tree = parse("a + b * c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "+")
        self.assertIsInstance(
            expression.right,
            BinaryExpression,
        )
        self.assertEqual(expression.right.operator, "*")

    def test_logical_precedence(self) -> None:
        tree = parse("a || b && c;")

        expression = tree.items[0].expression

        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "||")
        self.assertIsInstance(
            expression.right,
            BinaryExpression,
        )
        self.assertEqual(expression.right.operator, "&&")

    def test_assignment_is_right_associative(self) -> None:
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

    def test_complex_expression_chain(self) -> None:
        tree = parse(
            """
            object.items[index].value++;
            """
        )

        expression = tree.items[0].expression

        self.assertIsInstance(expression, PostfixExpression)
        self.assertEqual(expression.operator, "++")
        self.assertIsInstance(
            expression.operand,
            MemberAccessExpression,
)
        class ParserErrorTests(ParserTestCase):
    """Tests for syntax error handling."""

    def test_missing_semicolon_after_variable(self) -> None:
        self.assertSyntaxError("let value = 1")

    def test_missing_variable_name(self) -> None:
        self.assertSyntaxError("let = 1;")

    def test_missing_variable_initializer(self) -> None:
        self.assertSyntaxError("let value = ;")

    def test_missing_function_name(self) -> None:
        self.assertSyntaxError(
            """
            function () {
            }
            """
        )

    def test_missing_function_body(self) -> None:
        self.assertSyntaxError(
            """
            function main();
            """
        )

    def test_missing_function_parameter_name(self) -> None:
        self.assertSyntaxError(
            """
            function main(: Int) {
            }
            """
        )

    def test_missing_if_condition(self) -> None:
        self.assertSyntaxError(
            """
            if () {
            }
            """
        )

    def test_missing_if_body(self) -> None:
        self.assertSyntaxError(
            """
            if (value)
            """
        )

    def test_missing_while_body(self) -> None:
        self.assertSyntaxError(
            """
            while (value)
            """
        )

    def test_missing_for_parenthesis(self) -> None:
        self.assertSyntaxError(
            """
            for let i = 0; i < 10; i++ {
            }
            """
        )

    def test_missing_for_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            for (let i = 0 i < 10; i++) {
            }
            """
        )

    def test_missing_try_body(self) -> None:
        self.assertSyntaxError(
            """
            try
            """
        )

    def test_missing_catch(self) -> None:
        self.assertSyntaxError(
            """
            try {
            }
            """
        )

    def test_missing_catch_name(self) -> None:
        self.assertSyntaxError(
            """
            try {
            } catch () {
            }
            """
        )

    def test_import_requires_string(self) -> None:
        self.assertSyntaxError("import core;")

    def test_import_requires_semicolon(self) -> None:
        self.assertSyntaxError('import "core"; let value = 1')

    def test_class_requires_name(self) -> None:
        self.assertSyntaxError(
            """
            class {
            }
            """
        )

    def test_class_requires_body(self) -> None:
        self.assertSyntaxError("class Person;")

    def test_interface_requires_name(self) -> None:
        self.assertSyntaxError(
            """
            interface {
            }
            """
        )

    def test_struct_requires_body(self) -> None:
        self.assertSyntaxError("struct Point;")

    def test_record_requires_body(self) -> None:
        self.assertSyntaxError("record User;")

    def test_invalid_function_parameter_separator(self) -> None:
        self.assertSyntaxError(
            """
            function test(a: Int b: Int) {
            }
            """
        )

    def test_missing_closing_block(self) -> None:
        self.assertSyntaxError(
            """
            function main() {
                let value = 1;
            """
        )

    def test_missing_closing_parenthesis(self) -> None:
        self.assertSyntaxError("(value;")

    def test_missing_closing_array_bracket(self) -> None:
        self.assertSyntaxError("[1, 2;")

    def test_missing_expression_after_binary_operator(self) -> None:
        self.assertSyntaxError("value + ;")

    def test_missing_expression_after_logical_operator(self) -> None:
        self.assertSyntaxError("value && ;")

    def test_missing_conditional_false_expression(self) -> None:
        self.assertSyntaxError("value ? first : ;")

    def test_missing_new_type(self) -> None:
        self.assertSyntaxError("new ();")

    def test_missing_call_closing_parenthesis(self) -> None:
        self.assertSyntaxError("call(value;")

    def test_missing_member_name(self) -> None:
        self.assertSyntaxError("object.;")

    def test_missing_index_expression(self) -> None:
        self.assertSyntaxError("items[];")

    def test_missing_semicolon_after_return(self) -> None:
        self.assertSyntaxError(
            """
            function main() {
                return
            }
            """
        )

    def test_interface_function_requires_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            interface Printable {
                function print()
            }
            """
        )


class ParserIntegrationTests(ParserTestCase):
    """Integration tests combining multiple grammar features."""

    def test_complete_small_program(self) -> None:
        tree = parse(
            """
            import "core.io";

            public function main(args: Core.Args): Int {
                let value: Int = 10;

                if (value > 0) {
                    return value;
                } else {
                    return 0;
                }
            }
            """
        )

        self.assertEqual(len(tree.items), 2)

        import_item = tree.items[0]
        function_item = tree.items[1]

        self.assertIsInstance(import_item, ImportDeclaration)
        self.assertIsInstance(
            function_item,
            FunctionDeclaration,
        )

        self.assertEqual(function_item.name.name, "main")
        self.assertEqual(len(function_item.parameters), 1)
        self.assertIsNotNone(function_item.return_type)
        self.assertEqual(len(function_item.body.items), 2)

    def test_class_with_methods_and_expressions(self) -> None:
        tree = parse(
            """
            class Calculator {
                let value: Int = 0;

                function add(amount: Int): Int {
                    value = value + amount;
                    return value;
                }

                function reset() {
                    value = 0;
                }
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(
            declaration,
            ClassDeclaration,
        )
        self.assertEqual(len(declaration.members), 3)

        add_method = declaration.members[1]

        self.assertIsInstance(
            add_method,
            FunctionDeclaration,
        )
        self.assertEqual(add_method.name.name, "add")
        self.assertEqual(len(add_method.parameters), 1)

    def test_nested_control_flow(self) -> None:
        tree = parse(
            """
            function process() {
                while (running) {
                    if (ready) {
                        work();
                    } else {
                        wait();
                    }
                }
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(len(function.body.items), 1)

        while_statement = function.body.items[0]

        self.assertIsInstance(
            while_statement,
            WhileStatement,
        )
        self.assertIsInstance(
            while_statement.body,
            Block,
        )

    def test_for_loop_with_call_and_assignment(self) -> None:
        tree = parse(
            """
            for (let i = 0; i < count; i++) {
                process(i);
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsInstance(
            statement.update,
            PostfixExpression,
        )
        self.assertIsInstance(
            statement.body,
            Block,
        )

    def test_try_catch_with_function_call(self) -> None:
        tree = parse(
            """
            try {
                riskyOperation();
            } catch (error) {
                log(error);
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, TryStatement)
        self.assertEqual(
            statement.catch_name.name,
            "error",
        )


class ParserTokenBoundaryTests(ParserTestCase):
    """Tests for parser token-boundary behavior."""

    def test_comments_between_tokens_do_not_change_syntax(self) -> None:
        normal = parse(
            """
            let value = 1 + 2;
            """
        )

        commented = parse(
            """
            let /* comment */ value = 1 /* comment */ + 2;
            """
        )

        normal_declaration = normal.items[0]
        commented_declaration = commented.items[0]

        self.assertIsInstance(
            normal_declaration,
            VariableDeclaration,
        )
        self.assertIsInstance(
            commented_declaration,
            VariableDeclaration,
        )

        self.assertEqual(
            normal_declaration.name.name,
            commented_declaration.name.name,
        )

    def test_multiline_comments_do_not_break_parser(self) -> None:
        tree = parse(
            """
            /*
             * Multi-line comment.
             */
            let value = 10;
            """
        )

        self.assertEqual(len(tree.items), 1)
        self.assertIsInstance(
            tree.items[0],
            VariableDeclaration,
        )

    def test_unicode_identifier(self) -> None:
        tree = parse("let قيمة = 10;")

        declaration = tree.items[0]

        self.assertIsInstance(
            declaration,
            VariableDeclaration,
        )
        self.assertEqual(
            declaration.name.name,
            "قيمة",
        )

    def test_unicode_identifier_in_expression(self) -> None:
        tree = parse(
            """
            let قيمة = 10;
            قيمة;
            """
        )

        self.assertEqual(len(tree.items), 2)

        expression_statement = tree.items[1]

        self.assertIsInstance(
            expression_statement,
            ExpressionStatement,
        )
        self.assertIsInstance(
            expression_statement.expression,
            IdentifierExpression,
        )
        self.assertEqual(
            expression_statement.expression.identifier.name,
            "قيمة",
        )

    def test_nested_qualified_type(self) -> None:
        tree = parse(
            """
            let value: One.Two.Three.Four;
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(
            declaration,
            VariableDeclaration,
        )
        self.assertIsInstance(
            declaration.type_annotation,
            TypeReference,
        )

        self.assertEqual(
            tuple(
                part.name
                for part in declaration.type_annotation.parts
            ),
            ("One", "Two", "Three", "Four"),
        )


if __name__ == "__main__":
    unittest.main()
