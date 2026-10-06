"""Kupln Bootstrap Abstract Syntax Tree.

This module defines the syntax representation produced by the
Kupln bootstrap parser.

Responsibilities:
    - define syntax tree node types
    - preserve source positions
    - represent declarations, statements, and expressions

This module intentionally does not perform:
    - lexical scanning
    - semantic analysis
    - type checking
    - name resolution
    - code generation
    - backend processing
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from bootstrap.lexer.token import SourcePosition


@dataclass(frozen=True)
class Node:
    """Base class for all Kupln syntax tree nodes."""

    position: SourcePosition


@dataclass(frozen=True)
class CompilationUnit(Node):
    """Complete parsed Kupln source unit."""

    items: tuple["TopLevelItem", ...]


@dataclass(frozen=True)
class Identifier(Node):
    """Identifier syntax node."""

    name: str


@dataclass(frozen=True)
class TypeReference(Node):
    """A possibly qualified type reference."""

    parts: tuple[Identifier, ...]


@dataclass(frozen=True)
class Parameter(Node):
    """Function parameter."""

    name: Identifier
    type_annotation: TypeReference | None


@dataclass(frozen=True)
class Block(Node):
    """A brace-delimited block."""

    items: tuple["BlockItem", ...]


@dataclass(frozen=True)
class VariableDeclaration(Node):
    """let/var declaration."""

    modifiers: tuple[str, ...]
    keyword: str
    name: Identifier
    type_annotation: TypeReference | None
    initializer: "Expression | None"


@dataclass(frozen=True)
class FunctionDeclaration(Node):
    """Function declaration."""

    async_modifier: bool
    modifiers: tuple[str, ...]
    name: Identifier
    parameters: tuple[Parameter, ...]
    return_type: TypeReference | None
    body: Block


@dataclass(frozen=True)
class FieldDeclaration(Node):
    """Class field declaration."""

    modifiers: tuple[str, ...]
    name: Identifier
    type_annotation: TypeReference | None
    initializer: "Expression | None"


@dataclass(frozen=True)
class ClassDeclaration(Node):
    """Class declaration."""

    modifiers: tuple[str, ...]
    name: Identifier
    extends: TypeReference | None
    implements: tuple[TypeReference, ...]
    members: tuple["ClassMember", ...]


@dataclass(frozen=True)
class InterfaceDeclaration(Node):
    """Interface declaration."""

    modifiers: tuple[str, ...]
    name: Identifier
    extends: TypeReference | None
    members: tuple["InterfaceMember", ...]


@dataclass(frozen=True)
class StructDeclaration(Node):
    """Struct declaration."""

    modifiers: tuple[str, ...]
    name: Identifier
    fields: tuple[FieldDeclaration, ...]


@dataclass(frozen=True)
class RecordDeclaration(Node):
    """Record declaration."""

    modifiers: tuple[str, ...]
    name: Identifier
    fields: tuple[FieldDeclaration, ...]


@dataclass(frozen=True)
class ImportDeclaration(Node):
    """Import declaration."""

    path: str


@dataclass(frozen=True)
class ExportDeclaration(Node):
    """Exported declaration."""

    declaration: "Declaration"


@dataclass(frozen=True)
class EmptyStatement(Node):
    """Empty statement."""

    pass


@dataclass(frozen=True)
class ExpressionStatement(Node):
    """Expression followed by a statement terminator."""

    expression: "Expression"


@dataclass(frozen=True)
class ReturnStatement(Node):
    """Return statement."""

    expression: "Expression | None"


@dataclass(frozen=True)
class IfStatement(Node):
    """Conditional statement."""

    condition: "Expression"
    then_branch: "Statement"
    else_branch: "Statement | None"


@dataclass(frozen=True)
class WhileStatement(Node):
    """While loop."""

    condition: "Expression"
    body: "Statement"


@dataclass(frozen=True)
class ForStatement(Node):
    """Three-part for loop."""

    initializer: "ForInitializer | None"
    condition: "Expression | None"
    update: "Expression | None"
    body: "Statement"


@dataclass(frozen=True)
class TryStatement(Node):
    """Try/catch statement."""

    body: Block
    catch_name: Identifier
    catch_body: Block


@dataclass(frozen=True)
class LiteralExpression(Node):
    """Literal expression preserving its lexical value."""

    kind: str
    value: str


@dataclass(frozen=True)
class IdentifierExpression(Node):
    """Identifier expression."""

    identifier: Identifier


@dataclass(frozen=True)
class ThisExpression(Node):
    """this expression."""

    pass


@dataclass(frozen=True)
class SuperExpression(Node):
    """super expression."""

    pass


@dataclass(frozen=True)
class NewExpression(Node):
    """new expression."""

    type_reference: TypeReference
    arguments: tuple["Expression", ...]


@dataclass(frozen=True)
class ArrayExpression(Node):
    """Array literal expression."""

    elements: tuple["Expression", ...]


@dataclass(frozen=True)
class ParenthesizedExpression(Node):
    """Parenthesized expression."""

    expression: "Expression"


@dataclass(frozen=True)
class UnaryExpression(Node):
    """Unary expression."""

    operator: str
    operand: "Expression"


@dataclass(frozen=True)
class BinaryExpression(Node):
    """Binary expression."""

    left: "Expression"
    operator: str
    right: "Expression"


@dataclass(frozen=True)
class AssignmentExpression(Node):
    """Assignment expression."""

    target: "Expression"
    value: "Expression"


@dataclass(frozen=True)
class ConditionalExpression(Node):
    """Conditional expression."""

    condition: "Expression"
    when_true: "Expression"
    when_false: "Expression"


@dataclass(frozen=True)
class CallExpression(Node):
    """Function call expression."""

    callee: "Expression"
    arguments: tuple["Expression", ...]


@dataclass(frozen=True)
class MemberAccessExpression(Node):
    """Member access expression."""

    object: "Expression"
    member: Identifier


@dataclass(frozen=True)
class IndexExpression(Node):
    """Index access expression."""

    object: "Expression"
    index: "Expression"


@dataclass(frozen=True)
class PostfixExpression(Node):
    """Postfix increment/decrement expression."""

    operand: "Expression"
    operator: str


Declaration = Union[
    VariableDeclaration,
    FunctionDeclaration,
    ClassDeclaration,
    InterfaceDeclaration,
    StructDeclaration,
    RecordDeclaration,
]

Statement = Union[
    Block,
    VariableDeclaration,
    ExpressionStatement,
    ReturnStatement,
    IfStatement,
    WhileStatement,
    ForStatement,
    TryStatement,
    EmptyStatement,
]

Expression = Union[
    LiteralExpression,
    IdentifierExpression,
    ThisExpression,
    SuperExpression,
    NewExpression,
    ArrayExpression,
    ParenthesizedExpression,
    UnaryExpression,
    BinaryExpression,
    AssignmentExpression,
    ConditionalExpression,
    CallExpression,
    MemberAccessExpression,
    IndexExpression,
    PostfixExpression,
]

ForInitializer = Union[
    VariableDeclaration,
    ExpressionStatement,
]

ClassMember = Union[
    FieldDeclaration,
    FunctionDeclaration,
]

InterfaceMember = FunctionDeclaration

BlockItem = Union[
    Declaration,
    Statement,
]

TopLevelItem = Union[
    ImportDeclaration,
    ExportDeclaration,
    Declaration,
    Statement,
]
