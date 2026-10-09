"""Kupln Bootstrap Parser.

This module parses the token stream produced by the Kupln lexer and
constructs the Kupln bootstrap abstract syntax tree.

Responsibilities:
    - consume lexical tokens
    - ignore comments as syntax trivia
    - validate the current Kupln grammar
    - apply expression precedence
    - construct AST nodes
    - report syntax errors with source positions

This module intentionally does not perform:
    - semantic analysis
    - type checking
    - name resolution
    - ownership analysis
    - code generation
    - optimization
    - backend processing
"""

from __future__ import annotations

from typing import Sequence

from bootstrap.lexer.token import SourcePosition, Token, TokenKind

from .ast import (
    ArrayExpression,
    AssignmentExpression,
    BinaryExpression,
    Block,
    ClassDeclaration,
    CompilationUnit,
    ConditionalExpression,
    EmptyStatement,
    ExportDeclaration,
    Expression,
    ExpressionStatement,
    FieldDeclaration,
    ForInitializer,
    ForStatement,
    FunctionDeclaration,
    Identifier,
    IdentifierExpression,
    IfStatement,
    ImportDeclaration,
    IndexExpression,
    InterfaceDeclaration,
    LiteralExpression,
    MemberAccessExpression,
    NewExpression,
    Parameter,
    ParenthesizedExpression,
    PostfixExpression,
    RecordDeclaration,
    ReturnStatement,
    Statement,
    StructDeclaration,
    SuperExpression,
    ThisExpression,
    TryStatement,
    TypeReference,
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
)


class ParserError(Exception):
    """Base class for parser errors."""


class UnexpectedTokenError(ParserError):
    """Raised when a token cannot occur at the current grammar position."""


class Parser:
    """Recursive-descent parser for the Kupln bootstrap grammar."""

    _DECLARATION_MODIFIERS = frozenset(
        {
            "abstract",
            "final",
            "public",
            "private",
            "protected",
            "static",
        }
    )

    _UNARY_OPERATORS = frozenset(
        {
            "+",
            "-",
            "!",
            "++",
            "--",
        }
    )

    _BINARY_PRECEDENCE = {
        "||": 1,
        "&&": 2,
        "==": 3,
        "!=": 3,
        "<": 4,
        ">": 4,
        "<=": 4,
        ">=": 4,
        "+": 5,
        "-": 5,
        "*": 6,
        "/": 6,
        "%": 6,
        "??": 0,
    }

    def __init__(self, tokens: Sequence[Token]) -> None:
        """Create a parser for a token sequence."""

        self.tokens = tuple(
            token for token in tokens if token.kind != TokenKind.COMMENT
        )
        self.index = 0

    def parse(self) -> CompilationUnit:
        """Parse a complete compilation unit."""

        items = []

        while not self._check(TokenKind.EOF):
            items.append(self._parse_top_level_item())

        eof = self._current()

        return CompilationUnit(
            position=eof.position,
            items=tuple(items),
        )

    def _parse_top_level_item(self):
        if self._check_lexeme("import"):
            return self._parse_import()

        if self._check_lexeme("export"):
            return self._parse_export()

        if self._starts_declaration():
            return self._parse_declaration()

        return self._parse_statement()

    def _parse_declaration(self):
        modifiers = self._parse_modifiers()

        if self._check_lexeme("let") or self._check_lexeme("var"):
            return self._parse_variable_declaration(modifiers)

        if self._check_lexeme("async") or self._check_lexeme("function"):
            return self._parse_function_declaration(modifiers)

        if self._check_lexeme("class"):
            return self._parse_class_declaration(modifiers)

        if self._check_lexeme("interface"):
            return self._parse_interface_declaration(modifiers)

        if self._check_lexeme("struct"):
            return self._parse_struct_declaration(modifiers)

        if self._check_lexeme("record"):
            return self._parse_record_declaration(modifiers)

        self._error("Expected a declaration.")

    def _parse_modifiers(self) -> tuple[str, ...]:
        modifiers = []

        while self._current().lexeme in self._DECLARATION_MODIFIERS:
            modifiers.append(self._advance().lexeme)

        return tuple(modifiers)

    def _parse_variable_declaration(
        self,
        modifiers: tuple[str, ...],
        require_semicolon: bool = True,
    ) -> VariableDeclaration:
        start = self._current().position
        keyword = self._advance().lexeme

        name = self._parse_identifier()

        type_annotation = None
        if self._match_lexeme(":"):
            type_annotation = self._parse_type_reference()

        initializer = None
        if self._match_lexeme("="):
            initializer = self._parse_expression()

        if require_semicolon:
            self._expect_lexeme(
                ";",
                "Expected ';' after variable declaration.",
            )

        return VariableDeclaration(
            position=start,
            modifiers=modifiers,
            keyword=keyword,
            name=name,
            type_annotation=type_annotation,
            initializer=initializer,
        )

    def _parse_function_declaration(
        self,
        modifiers: tuple[str, ...],
    ) -> FunctionDeclaration:
        start = self._current().position

        async_modifier = self._match_lexeme("async")

        self._expect_lexeme(
            "function",
            "Expected 'function' in function declaration.",
        )

        name = self._parse_identifier()

        self._expect_lexeme(
            "(",
            "Expected '(' after function name.",
        )

        parameters = []

        if not self._check_lexeme(")"):
            parameters.append(self._parse_parameter())

            while self._match_lexeme(","):
                parameters.append(self._parse_parameter())

        self._expect_lexeme(
            ")",
            "Expected ')' after function parameters.",
        )

        return_type = None
        if self._match_lexeme(":"):
            return_type = self._parse_type_reference()

        body = self._parse_block()

        return FunctionDeclaration(
            position=start,
            async_modifier=async_modifier,
            modifiers=modifiers,
            name=name,
            parameters=tuple(parameters),
            return_type=return_type,
            body=body,
        )

    def _parse_parameter(self) -> Parameter:
        start = self._current().position
        name = self._parse_identifier()

        type_annotation = None
        if self._match_lexeme(":"):
            type_annotation = self._parse_type_reference()

        return Parameter(
            position=start,
            name=name,
            type_annotation=type_annotation,
        )

    def _parse_class_declaration(
        self,
        modifiers: tuple[str, ...],
    ) -> ClassDeclaration:
        start = self._current().position

        self._expect_lexeme("class", "Expected 'class'.")

        name = self._parse_identifier()

        extends = None
        if self._match_lexeme("extends"):
            extends = self._parse_type_reference()

        implements = []
        if self._match_lexeme("implements"):
            implements.append(self._parse_type_reference())

            while self._match_lexeme(","):
                implements.append(self._parse_type_reference())

        self._expect_lexeme(
            "{",
            "Expected '{' to begin class body.",
        )

        members = []

        while not self._check_lexeme("}") and not self._check(TokenKind.EOF):
            members.append(self._parse_class_member())

        self._expect_lexeme(
            "}",
            "Expected '}' after class body.",
        )

        return ClassDeclaration(
            position=start,
            modifiers=modifiers,
            name=name,
            extends=extends,
            implements=tuple(implements),
            members=tuple(members),
        )

    def _parse_class_member(self):
        modifiers = self._parse_modifiers()

        if self._check_lexeme("async") or self._check_lexeme("function"):
            return self._parse_function_declaration(modifiers)

        if self._check(TokenKind.IDENTIFIER):
            return self._parse_field_declaration(modifiers)

        self._error("Expected a class member.")

    def _parse_field_declaration(
        self,
        modifiers: tuple[str, ...],
    ) -> FieldDeclaration:
        start = self._current().position
        name = self._parse_identifier()

        type_annotation = None
        if self._match_lexeme(":"):
            type_annotation = self._parse_type_reference()

        initializer = None
        if self._match_lexeme("="):
            initializer = self._parse_expression()

        self._expect_lexeme(
            ";",
            "Expected ';' after field declaration.",
        )

        return FieldDeclaration(
            position=start,
            modifiers=modifiers,
            name=name,
            type_annotation=type_annotation,
            initializer=initializer,
        )

    def _parse_interface_declaration(
        self,
        modifiers: tuple[str, ...],
    ) -> InterfaceDeclaration:
        start = self._current().position

        self._expect_lexeme("interface", "Expected 'interface'.")

        name = self._parse_identifier()

        extends = None
        if self._match_lexeme("extends"):
            extends = self._parse_type_reference()

        self._expect_lexeme(
            "{",
            "Expected '{' to begin interface body.",
        )

        members = []

        while not self._check_lexeme("}") and not self._check(TokenKind.EOF):
            member_start = self._current().position
            member_modifiers = self._parse_modifiers()

            self._expect_lexeme(
                "function",
                "Expected 'function' in interface member.",
            )

            member_name = self._parse_identifier()

            self._expect_lexeme(
                "(",
                "Expected '(' after interface function name.",
            )

            parameters = []

            if not self._check_lexeme(")"):
                parameters.append(self._parse_parameter())

                while self._match_lexeme(","):
                    parameters.append(self._parse_parameter())

            self._expect_lexeme(
                ")",
                "Expected ')' after interface parameters.",
            )

            return_type = None
            if self._match_lexeme(":"):
                return_type = self._parse_type_reference()

            self._expect_lexeme(
                ";",
                "Expected ';' after interface function signature.",
            )

            members.append(
                FunctionDeclaration(
                    position=member_start,
                    async_modifier=False,
                    modifiers=member_modifiers,
                    name=member_name,
                    parameters=tuple(parameters),
                    return_type=return_type,
                    body=Block(
                        position=member_start,
                        items=(),
                    ),
                )
            )

        self._expect_lexeme(
            "}",
            "Expected '}' after interface body.",
        )

        return InterfaceDeclaration(
            position=start,
            modifiers=modifiers,
            name=name,
            extends=extends,
            members=tuple(members),
        )

    def _parse_struct_declaration(
        self,
        modifiers: tuple[str, ...],
    ) -> StructDeclaration:
        start = self._current().position

        self._expect_lexeme("struct", "Expected 'struct'.")

        name = self._parse_identifier()

        self._expect_lexeme(
            "{",
            "Expected '{' to begin struct body.",
        )

        fields = self._parse_fields_until_close_brace()

        return StructDeclaration(
            position=start,
            modifiers=modifiers,
            name=name,
            fields=fields,
        )

    def _parse_record_declaration(
        self,
        modifiers: tuple[str, ...],
    ) -> RecordDeclaration:
        start = self._current().position

        self._expect_lexeme("record", "Expected 'record'.")

        name = self._parse_identifier()

        self._expect_lexeme(
            "{",
            "Expected '{' to begin record body.",
        )

        fields = self._parse_fields_until_close_brace()

        return RecordDeclaration(
            position=start,
            modifiers=modifiers,
            name=name,
            fields=fields,
        )

       def _parse_fields_until_close_brace(
        self,
    ) -> tuple[FieldDeclaration, ...]:
        fields = []

        while not self._check_lexeme("}") and not self._check(TokenKind.EOF):
            modifiers = self._parse_modifiers()
            fields.append(self._parse_field_declaration(modifiers))

        self._expect_lexeme(
            "}",
            "Expected '}' after declaration body.",
        )

        return tuple(fields) 

    def _parse_import(self) -> ImportDeclaration:
        start = self._current().position

        self._expect_lexeme("import", "Expected 'import'.")

        path = self._expect_kind(
            TokenKind.STRING,
            "Expected a string literal after 'import'.",
        ).lexeme

        self._expect_lexeme(
            ";",
            "Expected ';' after import declaration.",
        )

        return ImportDeclaration(
            position=start,
            path=path,
        )

    def _parse_export(self) -> ExportDeclaration:
        start = self._current().position

        self._expect_lexeme("export", "Expected 'export'.")

        declaration = self._parse_declaration()

        return ExportDeclaration(
            position=start,
            declaration=declaration,
        )

    def _parse_statement(self) -> Statement:
        if self._check_lexeme("{"):
            return self._parse_block()

        if self._check_lexeme("let") or self._check_lexeme("var"):
            return self._parse_variable_declaration(())

        if self._check_lexeme("return"):
            return self._parse_return_statement()

        if self._check_lexeme("if"):
            return self._parse_if_statement()

        if self._check_lexeme("while"):
            return self._parse_while_statement()

        if self._check_lexeme("for"):
            return self._parse_for_statement()

        if self._check_lexeme("try"):
            return self._parse_try_statement()

        if self._match_lexeme(";"):
            token = self._previous()
            return EmptyStatement(position=token.position)

        expression = self._parse_expression()

        self._expect_lexeme(
            ";",
            "Expected ';' after expression.",
        )

        return ExpressionStatement(
            position=expression.position,
            expression=expression,
        )

    def _parse_block(self) -> Block:
        start = self._current().position

        self._expect_lexeme("{", "Expected '{'.")

        items = []

        while not self._check_lexeme("}") and not self._check(TokenKind.EOF):
            if self._starts_declaration():
                items.append(self._parse_declaration())
            else:
                items.append(self._parse_statement())

        self._expect_lexeme(
            "}",
            "Expected '}' after block.",
        )

        return Block(
            position=start,
            items=tuple(items),
        )

    def _parse_return_statement(self) -> ReturnStatement:
        start = self._advance().position

        expression = None

        if not self._check_lexeme(";"):
            expression = self._parse_expression()

        self._expect_lexeme(
            ";",
            "Expected ';' after return statement.",
        )

        return ReturnStatement(
            position=start,
            expression=expression,
        )

    def _parse_if_statement(self) -> IfStatement:
        start = self._advance().position

        self._expect_lexeme(
            "(",
            "Expected '(' after 'if'.",
        )

        condition = self._parse_expression()

        self._expect_lexeme(
            ")",
            "Expected ')' after if condition.",
        )

        then_branch = self._parse_statement()

        else_branch = None
        if self._match_lexeme("else"):
            else_branch = self._parse_statement()

        return IfStatement(
            position=start,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _parse_while_statement(self) -> WhileStatement:
        start = self._advance().position

        self._expect_lexeme(
            "(",
            "Expected '(' after 'while'.",
        )

        condition = self._parse_expression()

        self._expect_lexeme(
            ")",
            "Expected ')' after while condition.",
        )

        body = self._parse_statement()

        return WhileStatement(
            position=start,
            condition=condition,
            body=body,
        )

    def _parse_for_statement(self) -> ForStatement:
        start = self._advance().position

        self._expect_lexeme(
            "(",
            "Expected '(' after 'for'.",
        )

        initializer = None

        if not self._check_lexeme(";"):
            if self._check_lexeme("let") or self._check_lexeme("var"):
                initializer = self._parse_variable_declaration(
                    (),
                    require_semicolon=False,
                )
            else:
                expression = self._parse_expression()
                initializer = ExpressionStatement(
                    position=expression.position,
                    expression=expression,
                )

        self._expect_lexeme(
            ";",
            "Expected ';' after for initializer.",
        )

        condition = None
        if not self._check_lexeme(";"):
            condition = self._parse_expression()

        self._expect_lexeme(
            ";",
            "Expected ';' after for condition.",
        )

        update = None
        if not self._check_lexeme(")"):
            update = self._parse_expression()

        self._expect_lexeme(
            ")",
            "Expected ')' after for clauses.",
        )

        body = self._parse_statement()

        return ForStatement(
            position=start,
            initializer=initializer,
            condition=condition,
            update=update,
            body=body,
        )

    def _parse_try_statement(self) -> TryStatement:
        start = self._advance().position

        body = self._parse_block()

        self._expect_lexeme(
            "catch",
            "Expected 'catch' after try block.",
        )

        self._expect_lexeme(
            "(",
            "Expected '(' after 'catch'.",
        )

        catch_name = self._parse_identifier()

        self._expect_lexeme(
            ")",
            "Expected ')' after catch parameter.",
        )

        catch_body = self._parse_block()

        return TryStatement(
            position=start,
            body=body,
            catch_name=catch_name,
            catch_body=catch_body,
        )

    def _parse_type_reference(self) -> TypeReference:
        start = self._current().position
        parts = [self._parse_identifier()]

        while self._match_lexeme("."):
            parts.append(self._parse_identifier())

        return TypeReference(
            position=start,
            parts=tuple(parts),
        )

    def _parse_identifier(self) -> Identifier:
        token = self._expect_kind(
            TokenKind.IDENTIFIER,
            "Expected an identifier.",
        )

        return Identifier(
            position=token.position,
            name=token.lexeme,
        )

    def _parse_expression(self) -> Expression:
        return self._parse_assignment()

    def _parse_assignment(self) -> Expression:
        expression = self._parse_conditional()

        if self._match_lexeme("="):
            value = self._parse_assignment()

            return AssignmentExpression(
                position=expression.position,
                target=expression,
                value=value,
            )

        return expression

    def _parse_conditional(self) -> Expression:
        expression = self._parse_binary(0)

        if self._match_lexeme("?"):
            when_true = self._parse_expression()

            self._expect_lexeme(
                ":",
                "Expected ':' in conditional expression.",
            )

            when_false = self._parse_conditional()

            return ConditionalExpression(
                position=expression.position,
                condition=expression,
                when_true=when_true,
                when_false=when_false,
            )

        return expression

    def _parse_binary(self, minimum_precedence: int) -> Expression:
        left = self._parse_unary()

        while self._current().lexeme in self._BINARY_PRECEDENCE:
            operator = self._current().lexeme
            precedence = self._BINARY_PRECEDENCE[operator]

            if precedence < minimum_precedence:
                break

            self._advance()

            right = self._parse_binary(precedence + 1)

            left = BinaryExpression(
                position=left.position,
                left=left,
                operator=operator,
                right=right,
            )

        return left

    def _parse_unary(self) -> Expression:
        if self._check_lexeme("await"):
            token = self._advance()

            return UnaryExpression(
                position=token.position,
                operator="await",
                operand=self._parse_unary(),
            )

        if self._current().lexeme in self._UNARY_OPERATORS:
            token = self._advance()

            return UnaryExpression(
                position=token.position,
                operator=token.lexeme,
                operand=self._parse_unary(),
            )

        return self._parse_postfix()

    def _parse_postfix(self) -> Expression:
        expression = self._parse_primary()

        while True:
            if self._match_lexeme("("):
                arguments = []

                if not self._check_lexeme(")"):
                    arguments.append(self._parse_expression())

                    while self._match_lexeme(","):
                        arguments.append(self._parse_expression())

                self._expect_lexeme(
                    ")",
                    "Expected ')' after arguments.",
                )

                expression = CallExpression(
                    position=expression.position,
                    callee=expression,
                    arguments=tuple(arguments),
                )
                continue

            if self._match_lexeme("."):
                member = self._parse_identifier()

                expression = MemberAccessExpression(
                    position=expression.position,
                    object=expression,
                    member=member,
                )
                continue

            if self._match_lexeme("["):
                index = self._parse_expression()

                self._expect_lexeme(
                    "]",
                    "Expected ']' after index expression.",
                )

                expression = IndexExpression(
                    position=expression.position,
                    object=expression,
                    index=index,
                )
                continue

            if self._check_lexeme("++") or self._check_lexeme("--"):
                operator = self._advance()

                expression = PostfixExpression(
                    position=expression.position,
                    operand=expression,
                    operator=operator.lexeme,
                )
                continue

            break

        return expression

    def _parse_primary(self) -> Expression:
        token = self._current()

        if token.kind in {
            TokenKind.INTEGER,
            TokenKind.FLOAT,
            TokenKind.STRING,
            TokenKind.CHAR,
        }:
            self._advance()

            return LiteralExpression(
                position=token.position,
                kind=token.kind.name.lower(),
                value=token.lexeme,
            )

        if token.lexeme in {"true", "false", "null"}:
            self._advance()

            return LiteralExpression(
                position=token.position,
                kind=token.lexeme,
                value=token.lexeme,
            )

        if token.kind == TokenKind.IDENTIFIER:
            self._advance()

            identifier = Identifier(
                position=token.position,
                name=token.lexeme,
            )

            return IdentifierExpression(
                position=token.position,
                identifier=identifier,
            )

        if token.lexeme == "this":
            self._advance()
            return ThisExpression(position=token.position)

        if token.lexeme == "super":
            self._advance()
            return SuperExpression(position=token.position)

        if token.lexeme == "new":
            return self._parse_new_expression()

        if self._match_lexeme("("):
            start = self._previous().position
            expression = self._parse_expression()

            self._expect_lexeme(
                ")",
                "Expected ')' after expression.",
            )

            return ParenthesizedExpression(
                position=start,
                expression=expression,
            )

        if self._match_lexeme("["):
            start = self._previous().position
            elements = []

            if not self._check_lexeme("]"):
                elements.append(self._parse_expression())

                while self._match_lexeme(","):
                    elements.append(self._parse_expression())

            self._expect_lexeme(
                "]",
                "Expected ']' after array expression.",
            )

            return ArrayExpression(
                position=start,
                elements=tuple(elements),
            )

        self._error("Expected an expression.")

    def _parse_new_expression(self) -> NewExpression:
        start = self._advance().position

        type_reference = self._parse_type_reference()

        self._expect_lexeme(
            "(",
            "Expected '(' after type name in new expression.",
        )

        arguments = []

        if not self._check_lexeme(")"):
            arguments.append(self._parse_expression())

            while self._match_lexeme(","):
                arguments.append(self._parse_expression())

        self._expect_lexeme(
            ")",
            "Expected ')' after constructor arguments.",
        )

        return NewExpression(
            position=start,
            type_reference=type_reference,
            arguments=tuple(arguments),
        )

    def _starts_declaration(self) -> bool:
        token = self._current()

        if token.lexeme in self._DECLARATION_MODIFIERS:
            return True

        return token.lexeme in {
            "let",
            "var",
            "function",
            "async",
            "class",
            "interface",
            "struct",
            "record",
        }

    def _current(self) -> Token:
        return self.tokens[self.index]

    def _previous(self) -> Token:
        return self.tokens[self.index - 1]

    def _advance(self) -> Token:
        token = self._current()

        if token.kind != TokenKind.EOF:
            self.index += 1

        return token

    def _check(self, kind: TokenKind) -> bool:
        return self._current().kind == kind

    def _check_lexeme(self, lexeme: str) -> bool:
        return self._current().lexeme == lexeme

    def _match_lexeme(self, lexeme: str) -> bool:
        if not self._check_lexeme(lexeme):
            return False

        self._advance()
        return True

    def _expect_lexeme(self, lexeme: str, message: str) -> Token:
        if self._check_lexeme(lexeme):
            return self._advance()

        self._error(message)

    def _expect_kind(self, kind: TokenKind, message: str) -> Token:
        if self._check(kind):
            return self._advance()

        self._error(message)

    def _error(self, message: str) -> None:
        token = self._current()
        position = token.position

        raise UnexpectedTokenError(
            f"{message} "
            f"Found {token.lexeme!r} at "
            f"{position.line}:{position.column} "
            f"(offset {position.offset})."
    )
