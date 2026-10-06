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
    """Common parser test helpers."""

    def assertSyntaxError(self, source: str) -> None:
        with self.assertRaises(ParserError):
            parse(source)


class ParserBasicTests(ParserTestCase):
    """Basic compilation-unit and declaration tests."""

    def test_empty_source(self) -> None:
        tree = parse("")
        self.assertEqual(len(tree.items), 0)

    def test_comments_only(self) -> None:
        tree = parse("// comment\n/* comment */")
        self.assertEqual(len(tree.items), 0)

    def test_multiple_items(self) -> None:
        tree = parse(
            """
            let a = 1;
            let b = 2;
            function main() {
                return a;
            }
            """
        )

        self.assertEqual(len(tree.items), 3)
        self.assertIsInstance(tree.items[0], VariableDeclaration)
        self.assertIsInstance(tree.items[1], VariableDeclaration)
        self.assertIsInstance(tree.items[2], FunctionDeclaration)

    def test_import(self) -> None:
        tree = parse('import "core.io";')

        item = tree.items[0]

        self.assertIsInstance(item, ImportDeclaration)
        self.assertEqual(item.path, '"core.io"')

    def test_let_declaration(self) -> None:
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
        self.assertIsNotNone(declaration.initializer)

    def test_typed_variable(self) -> None:
        tree = parse("let value: Int = 10;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertIsNotNone(declaration.type_annotation)
        self.assertEqual(
            declaration.type_annotation.parts[0].name,
            "Int",
        )

    def test_qualified_type(self) -> None:
        tree = parse("let value: Core.Types.Value;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertIsInstance(
            declaration.type_annotation,
            TypeReference,
        )

        self.assertEqual(
            tuple(
                part.name
                for part in declaration.type_annotation.parts
            ),
            ("Core", "Types", "Value"),
        )

    def test_variable_modifiers(self) -> None:
        tree = parse("public static let value = 1;")

        declaration = tree.items[0]

        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertEqual(
            declaration.modifiers,
            ("public", "static"),
        )


class ParserFunctionTests(ParserTestCase):
    """Function declaration tests."""

    def test_empty_function(self) -> None:
        tree = parse(
            """
            function main() {
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(function.name.name, "main")
        self.assertEqual(len(function.parameters), 0)
        self.assertIsInstance(function.body, Block)

    def test_function_parameters(self) -> None:
        tree = parse(
            """
            function add(a: Int, b: Int) {
                return a + b;
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(len(function.parameters), 2)
        self.assertEqual(function.parameters[0].name.name, "a")
        self.assertEqual(function.parameters[1].name.name, "b")

    def test_function_return_type(self) -> None:
        tree = parse(
            """
            function getValue(): Int {
                return 1;
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertIsNotNone(function.return_type)
        self.assertEqual(
            function.return_type.parts[0].name,
            "Int",
        )

    def test_async_function(self) -> None:
        tree = parse(
            """
            async function load() {
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertTrue(function.async_modifier)

    def test_function_modifiers(self) -> None:
        tree = parse(
            """
            public static function main() {
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(
            function.modifiers,
            ("public", "static"),
        )

    def test_function_body(self) -> None:
        tree = parse(
            """
            function main() {
                let value = 1;
                return value;
            }
            """
        )

        function = tree.items[0]

        self.assertIsInstance(function, FunctionDeclaration)
        self.assertEqual(len(function.body.items), 2)
        self.assertIsInstance(
            function.body.items[0],
            VariableDeclaration,
        )
        self.assertIsInstance(
            function.body.items[1],
            ReturnStatement,
        )


class ParserStatementTests(ParserTestCase):
    """Statement tests."""

    def test_expression_statement(self) -> None:
        tree = parse("value;")

        statement = tree.items[0]

        self.assertIsInstance(statement, ExpressionStatement)
        self.assertIsInstance(
            statement.expression,
            IdentifierExpression,
        )

    def test_return_statement(self) -> None:
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

    def test_return_without_expression(self) -> None:
        tree = parse(
            """
            function main() {
                return;
            }
            """
        )

        function = tree.items[0]
        statement = function.body.items[0]

        self.assertIsInstance(statement, ReturnStatement)
        self.assertIsNone(statement.expression)

    def test_if_else(self) -> None:
        tree = parse(
            """
            if (value) {
                return;
            } else {
                return;
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, IfStatement)
        self.assertIsNotNone(statement.else_branch)

    def test_while(self) -> None:
        tree = parse(
            """
            while (running) {
                work();
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, WhileStatement)
        self.assertIsInstance(statement.body, Block)

    def test_for(self) -> None:
        tree = parse(
            """
            for (let i = 0; i < 10; i++) {
                work(i);
            }
            """
        )

        statement = tree.items[0]

        self.assertIsInstance(statement, ForStatement)
        self.assertIsNotNone(statement.initializer)
        self.assertIsNotNone(statement.condition)
        self.assertIsNotNone(statement.update)

    def test_try_catch(self) -> None:
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
        class ParserDeclarationTests(ParserTestCase):
    """Class, interface, struct, and record tests."""

    def test_class(self) -> None:
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
        self.assertEqual(len(declaration.members), 1)

    def test_class_extends(self) -> None:
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

    def test_class_implements(self) -> None:
        tree = parse(
            """
            class Child implements Printable, Serializable {
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(len(declaration.implements), 2)

    def test_class_members(self) -> None:
        tree = parse(
            """
            class Person {
                let age: Int = 18;

                function greet() {
                    return;
                }
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(declaration, ClassDeclaration)
        self.assertEqual(len(declaration.members), 2)
        self.assertIsInstance(
            declaration.members[0],
            VariableDeclaration,
        )
        self.assertIsInstance(
            declaration.members[1],
            FunctionDeclaration,
        )

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

    def test_interface(self) -> None:
        tree = parse(
            """
            interface Printable {
                function print(value: String);
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(
            declaration,
            InterfaceDeclaration,
        )
        self.assertEqual(declaration.name.name, "Printable")
        self.assertEqual(len(declaration.members), 1)

    def test_interface_extends(self) -> None:
        tree = parse(
            """
            interface Child extends Parent {
                function run();
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(
            declaration,
            InterfaceDeclaration,
        )
        self.assertIsNotNone(declaration.extends)

    def test_struct(self) -> None:
        tree = parse(
            """
            struct Point {
                let x: Int;
                let y: Int;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(
            declaration,
            StructDeclaration,
        )
        self.assertEqual(len(declaration.fields), 2)

    def test_record(self) -> None:
        tree = parse(
            """
            record User {
                let id: Int;
                let name: String;
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(
            declaration,
            RecordDeclaration,
        )
        self.assertEqual(len(declaration.fields), 2)


class ParserExpressionTests(ParserTestCase):
    """Expression and precedence tests."""

    def test_integer(self) -> None:
        tree = parse("42;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            LiteralExpression,
        )
        self.assertEqual(expression.kind, "INTEGER")
        self.assertEqual(expression.value, "42")

    def test_float(self) -> None:
        tree = parse("3.14;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            LiteralExpression,
        )
        self.assertEqual(expression.kind, "FLOAT")

    def test_string(self) -> None:
        tree = parse('"hello";')

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            LiteralExpression,
        )
        self.assertEqual(expression.kind, "STRING")

    def test_character(self) -> None:
        tree = parse("'A';")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            LiteralExpression,
        )
        self.assertEqual(expression.kind, "CHAR")

    def test_boolean(self) -> None:
        tree = parse("true;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            LiteralExpression,
        )
        self.assertEqual(expression.value, "true")

    def test_null(self) -> None:
        tree = parse("null;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            LiteralExpression,
        )
        self.assertEqual(expression.value, "null")

    def test_identifier(self) -> None:
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

    def test_this(self) -> None:
        tree = parse("this;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ThisExpression,
        )

    def test_super(self) -> None:
        tree = parse("super;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            SuperExpression,
        )

    def test_new(self) -> None:
        tree = parse("new Person();")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            NewExpression,
        )
        self.assertEqual(
            expression.type_reference.parts[0].name,
            "Person",
        )

    def test_new_with_arguments(self) -> None:
        tree = parse("new Person(1, name);")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            NewExpression,
        )
        self.assertEqual(len(expression.arguments), 2)

    def test_array(self) -> None:
        tree = parse("[1, 2, 3];")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ArrayExpression,
        )
        self.assertEqual(len(expression.elements), 3)

    def test_empty_array(self) -> None:
        tree = parse("[];")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ArrayExpression,
        )
        self.assertEqual(len(expression.elements), 0)

    def test_parenthesized(self) -> None:
        tree = parse("(value);")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ParenthesizedExpression,
        )

    def test_unary(self) -> None:
        tree = parse("-value;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            UnaryExpression,
        )
        self.assertEqual(expression.operator, "-")

    def test_await(self) -> None:
        tree = parse("await load();")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            UnaryExpression,
        )
        self.assertEqual(expression.operator, "await")

    def test_binary(self) -> None:
        tree = parse("a + b;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            BinaryExpression,
        )
        self.assertEqual(expression.operator, "+")

    def test_assignment(self) -> None:
        tree = parse("value = 10;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            AssignmentExpression,
        )

    def test_conditional(self) -> None:
        tree = parse("condition ? a : b;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            ConditionalExpression,
        )

    def test_call(self) -> None:
        tree = parse("print(value);")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            CallExpression,
        )
        self.assertEqual(len(expression.arguments), 1)

    def test_member_access(self) -> None:
        tree = parse("object.value;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            MemberAccessExpression,
        )
        self.assertEqual(
            expression.member.name,
            "value",
        )

    def test_index_access(self) -> None:
        tree = parse("items[index];")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            IndexExpression,
        )

    def test_postfix(self) -> None:
        tree = parse("value++;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            PostfixExpression,
        )
        self.assertEqual(
            expression.operator,
            "++",
        )

    def test_multiplication_precedence(self) -> None:
        tree = parse("a + b * c;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            BinaryExpression,
        )
        self.assertEqual(
            expression.operator,
            "+",
        )
        self.assertIsInstance(
            expression.right,
            BinaryExpression,
        )
        self.assertEqual(
            expression.right.operator,
            "*",
        )

    def test_logical_precedence(self) -> None:
        tree = parse("a || b && c;")

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            BinaryExpression,
        )
        self.assertEqual(
            expression.operator,
            "||",
        )
        self.assertIsInstance(
            expression.right,
            BinaryExpression,
        )
        self.assertEqual(
            expression.right.operator,
            "&&",
        )

    def test_assignment_right_associative(self) -> None:
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

    def test_complex_chain(self) -> None:
        tree = parse(
            """
            object.items[index].value++;
            """
        )

        expression = tree.items[0].expression

        self.assertIsInstance(
            expression,
            PostfixExpression,
        )
        self.assertIsInstance(
            expression.operand,
            MemberAccessExpression,
)
        class ParserErrorTests(ParserTestCase):
    """Syntax error tests."""

    def test_missing_variable_semicolon(self) -> None:
        self.assertSyntaxError("let value = 1")

    def test_missing_variable_name(self) -> None:
        self.assertSyntaxError("let = 1;")

    def test_missing_initializer(self) -> None:
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

    def test_invalid_parameter(self) -> None:
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

    def test_missing_for_semicolon(self) -> None:
        self.assertSyntaxError(
            """
            for (let i = 0 i < 10; i++) {
            }
            """
        )

    def test_missing_catch(self) -> None:
        self.assertSyntaxError(
            """
            try {
            }
            """
        )

    def test_import_requires_string(self) -> None:
        self.assertSyntaxError("import core;")

    def test_class_requires_name(self) -> None:
        self.assertSyntaxError(
            """
            class {
            }
            """
        )

    def test_class_requires_body(self) -> None:
        self.assertSyntaxError("class Person;")

    def test_struct_requires_body(self) -> None:
        self.assertSyntaxError("struct Point;")

    def test_record_requires_body(self) -> None:
        self.assertSyntaxError("record User;")

    def test_missing_closing_parenthesis(self) -> None:
        self.assertSyntaxError("(value;")

    def test_missing_array_bracket(self) -> None:
        self.assertSyntaxError("[1, 2;")

    def test_missing_binary_operand(self) -> None:
        self.assertSyntaxError("value + ;")

    def test_missing_conditional_expression(self) -> None:
        self.assertSyntaxError("value ? first : ;")

    def test_missing_member_name(self) -> None:
        self.assertSyntaxError("object.;")

    def test_missing_index_expression(self) -> None:
        self.assertSyntaxError("items[];")


class ParserIntegrationTests(ParserTestCase):
    """Small end-to-end parser tests."""

    def test_small_program(self) -> None:
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

        self.assertIsInstance(
            tree.items[0],
            ImportDeclaration,
        )
        self.assertIsInstance(
            tree.items[1],
            FunctionDeclaration,
        )

    def test_class_program(self) -> None:
        tree = parse(
            """
            class Calculator {
                let value: Int = 0;

                function add(amount: Int): Int {
                    value = value + amount;
                    return value;
                }
            }
            """
        )

        declaration = tree.items[0]

        self.assertIsInstance(
            declaration,
            ClassDeclaration,
        )
        self.assertEqual(
            len(declaration.members),
            2,
        )

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

        self.assertIsInstance(
            function,
            FunctionDeclaration,
        )
        self.assertEqual(
            len(function.body.items),
            1,
        )
        self.assertIsInstance(
            function.body.items[0],
            WhileStatement,
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


if __name__ == "__main__":
    unittest.main()
