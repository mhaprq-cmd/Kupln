"""Kupln Bootstrap Type Checker.

This module performs the first bootstrap type-checking pass over the
Kupln Abstract Syntax Tree.

Responsibilities:
    - resolve type references
    - register user-defined types
    - resolve identifiers
    - infer variable types
    - validate assignments
    - validate expressions
    - validate function calls and returns
    - validate control-flow conditions
    - validate arrays, member access, and indexing
    - validate class/interface/struct/record declarations
    - provide deterministic type errors

This module intentionally does not perform:
    - lexical scanning
    - parsing
    - code generation
    - backend processing
    - runtime execution
"""

from __future__ import annotations

from dataclasses import dataclass

from bootstrap.parser.ast import (
    ArrayExpression,
    AssignmentExpression,
    BinaryExpression,
    Block,
    CallExpression,
    ClassDeclaration,
    CompilationUnit,
    ConditionalExpression,
    Declaration,
    EmptyStatement,
    ExportDeclaration,
    Expression,
    ExpressionStatement,
    FieldDeclaration,
    ForInitializer,
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
from bootstrap.types.environment import (
    DuplicateDefinitionError,
    TypeEnvironment,
    TypeEnvironmentError,
    UnknownNameError,
    create_root_environment,
)
from bootstrap.types.type_system import (
    ANY,
    BOOL,
    CHAR,
    FLOAT,
    INT,
    NULL,
    STRING,
    VOID,
    ArrayType,
    FunctionType,
    NamedType,
    Type,
    TypeKind,
    array_type,
    builtin_type,
    function_type,
    is_boolean,
    is_nullable,
    is_numeric,
    named_type,
)


class TypeCheckError(Exception):
    """Base error for Type Checker failures."""


class UnknownTypeError(TypeCheckError):
    """Raised when a type reference cannot be resolved."""


class InvalidTypeOperationError(TypeCheckError):
    """Raised when an expression uses incompatible types."""


class InvalidAssignmentError(TypeCheckError):
    """Raised when an assignment is invalid."""


class InvalidCallError(TypeCheckError):
    """Raised when a function call is invalid."""


class InvalidReturnError(TypeCheckError):
    """Raised when a return statement is invalid."""


class InvalidMemberAccessError(TypeCheckError):
    """Raised when member access is invalid."""


class InvalidIndexError(TypeCheckError):
    """Raised when index access is invalid."""


@dataclass(frozen=True)
class MemberInfo:
    """Type information for a declared member."""

    name: str
    type: Type


@dataclass(frozen=True)
class TypeInfo:
    """Bootstrap metadata for a named user-defined type."""

    type: NamedType
    members: tuple[MemberInfo, ...]
    extends: NamedType | None
    interfaces: tuple[NamedType, ...]


class TypeChecker:
    """Type-check a parsed Kupln compilation unit."""

    def __init__(self):
        self.environment = create_root_environment()
        self._type_infos: dict[str, TypeInfo] = {}
        self._function_contexts: list[FunctionType] = []
        self._class_contexts: list[NamedType] = []

    def check(self, unit: CompilationUnit) -> None:
        """Type-check a complete compilation unit."""
        self._register_types(unit)
        self._register_top_level_symbols(unit)

        for item in unit.items:
            self._check_top_level_item(item)

    def resolve_type(self, reference: TypeReference) -> Type:
        """Resolve a TypeReference into a Type."""
        name = self._type_reference_name(reference)

        built_in = builtin_type(name)
        if built_in is not None:
            return built_in

        if name.endswith("[]"):
            element_name = name[:-2]
            element = builtin_type(element_name)

            if element is None:
                for type_name, info in self._type_infos.items():
                    if type_name == element_name:
                        element = info.type
                        break

            if element is None:
                raise UnknownTypeError(
                    self._error_at(
                        reference,
                        f"Unknown type '{element_name}'.",
                    )
                )

            return array_type(element)

        info = self._type_infos.get(name)

        if info is not None:
            return info.type

        raise UnknownTypeError(
            self._error_at(
                reference,
                f"Unknown type '{name}'.",
            )
        )

    def _register_types(self, unit: CompilationUnit) -> None:
        """Register all user-defined types before checking declarations."""
        for item in unit.items:
            declaration = self._unwrap_declaration(item)

            if declaration is None:
                continue

            if isinstance(
                declaration,
                (
                    ClassDeclaration,
                    InterfaceDeclaration,
                    StructDeclaration,
                    RecordDeclaration,
                ),
            ):
                name = declaration.name.name

                if name in self._type_infos:
                    raise TypeCheckError(
                        self._error_at(
                            declaration,
                            f"Type '{name}' is already defined.",
                        )
                    )

                kind = self._declaration_type_kind(declaration)
                declared_type = named_type(name, kind)

                self._type_infos[name] = TypeInfo(
                    type=declared_type,
                    members=(),
                    extends=None,
                    interfaces=(),
                )

        for item in unit.items:
            declaration = self._unwrap_declaration(item)

            if declaration is None:
                continue

            if isinstance(declaration, ClassDeclaration):
                self._complete_class_type(declaration)

            elif isinstance(declaration, InterfaceDeclaration):
                self._complete_interface_type(declaration)

            elif isinstance(declaration, StructDeclaration):
                self._complete_struct_type(declaration)

            elif isinstance(declaration, RecordDeclaration):
                self._complete_record_type(declaration)

    def _register_top_level_symbols(
        self,
        unit: CompilationUnit,
    ) -> None:
        """Register top-level variables and functions."""
        for item in unit.items:
            declaration = self._unwrap_declaration(item)

            if declaration is None:
                continue

            if isinstance(declaration, VariableDeclaration):
                type_ = self._declared_or_inferred_variable_type(
                    declaration,
                    allow_missing_initializer=False,
                )

                self._define_symbol(
                    declaration.name.name,
                    type_,
                    declaration,
                )

            elif isinstance(declaration, FunctionDeclaration):
                function_type_ = self._function_type(declaration)

                self._define_symbol(
                    declaration.name.name,
                    function_type_,
                    declaration,
                )

    def _check_top_level_item(self, item) -> None:
        if isinstance(item, ImportDeclaration):
            return

        if isinstance(item, ExportDeclaration):
            self._check_declaration(item.declaration)
            return

        if isinstance(
            item,
            (
                VariableDeclaration,
                FunctionDeclaration,
                ClassDeclaration,
                InterfaceDeclaration,
                StructDeclaration,
                RecordDeclaration,
            ),
        ):
            self._check_declaration(item)
            return

        self._check_statement(item)

    def _check_declaration(self, declaration: Declaration) -> None:
        if isinstance(declaration, VariableDeclaration):
            self._check_variable_declaration(declaration)
            return

        if isinstance(declaration, FunctionDeclaration):
            self._check_function_declaration(declaration)
            return

        if isinstance(declaration, ClassDeclaration):
            self._check_class_declaration(declaration)
            return

        if isinstance(declaration, InterfaceDeclaration):
            self._check_interface_declaration(declaration)
            return

        if isinstance(declaration, StructDeclaration):
            self._check_struct_declaration(declaration)
            return

        if isinstance(declaration, RecordDeclaration):
            self._check_record_declaration(declaration)
            return

        raise TypeCheckError(
            self._error_at(
                declaration,
                "Unsupported declaration.",
            )
        )

    def _check_variable_declaration(
        self,
        declaration: VariableDeclaration,
    ) -> Type:
        type_ = self._declared_or_inferred_variable_type(
            declaration,
            allow_missing_initializer=False,
        )

        if declaration.initializer is not None:
            initializer_type = self._check_expression(
                declaration.initializer
            )

            if not self.is_assignable(initializer_type, type_):
                raise InvalidAssignmentError(
                    self._error_at(
                        declaration,
                        (
                            f"Cannot assign value of type "
                            f"'{initializer_type.name}' to variable "
                            f"'{declaration.name.name}' of type "
                            f"'{type_.name}'."
                        ),
                    )
                )

        return type_

    def _declared_or_inferred_variable_type(
        self,
        declaration: VariableDeclaration,
        allow_missing_initializer: bool,
    ) -> Type:
        declared_type = None

        if declaration.type_annotation is not None:
            declared_type = self.resolve_type(
                declaration.type_annotation
            )

        if declaration.initializer is None:
            if declared_type is not None:
                return declared_type

            if allow_missing_initializer:
                return ANY

            raise TypeCheckError(
                self._error_at(
                    declaration,
                    (
                        f"Variable '{declaration.name.name}' "
                        "requires a type annotation or initializer."
                    ),
                )
            )

        inferred_type = self._check_expression(
            declaration.initializer
        )

        if declared_type is not None:
            if not self.is_assignable(
                inferred_type,
                declared_type,
            ):
                raise InvalidAssignmentError(
                    self._error_at(
                        declaration,
                        (
                            f"Initializer of type '{inferred_type.name}' "
                            f"is not compatible with declared type "
                            f"'{declared_type.name}'."
                        ),
                    )
                )

            return declared_type

        return inferred_type
          def _check_function_declaration(
        self,
        declaration: FunctionDeclaration,
    ) -> FunctionType:
        function_type_ = self._function_type(declaration)

        local = self.environment.child()

        for parameter, parameter_type in zip(
            declaration.parameters,
            function_type_.parameter_types,
        ):
            self._define_symbol(
                parameter.name.name,
                parameter_type,
                parameter,
                environment=local,
            )

        previous_environment = self.environment
        self.environment = local
        self._function_contexts.append(function_type_)

        try:
            self._check_block_contents(declaration.body)

            if function_type_.return_type is VOID:
                return function_type_

        finally:
            self._function_contexts.pop()
            self.environment = previous_environment

        return function_type_

    def _function_type(
        self,
        declaration: FunctionDeclaration,
    ) -> FunctionType:
        parameter_types = []

        for parameter in declaration.parameters:
            if parameter.type_annotation is None:
                raise TypeCheckError(
                    self._error_at(
                        parameter,
                        (
                            f"Parameter '{parameter.name.name}' "
                            "requires a type annotation."
                        ),
                    )
                )

            parameter_types.append(
                self.resolve_type(parameter.type_annotation)
            )

        return_type = VOID

        if declaration.return_type is not None:
            return_type = self.resolve_type(
                declaration.return_type
            )

        return function_type(
            parameter_types=tuple(parameter_types),
            return_type=return_type,
            async_function=declaration.async_modifier,
        )

    def _check_class_declaration(
        self,
        declaration: ClassDeclaration,
    ) -> None:
        class_type = self._type_infos[
            declaration.name.name
        ].type

        self._class_contexts.append(class_type)

        try:
            local = self.environment.child()

            for member in self._members_for_type(class_type):
                self._define_symbol(
                    member.name,
                    member.type,
                    declaration,
                    environment=local,
                )

            previous_environment = self.environment
            self.environment = local

            try:
                for member in declaration.members:
                    if isinstance(member, FieldDeclaration):
                        self._check_field_declaration(member)

                    elif isinstance(
                        member,
                        FunctionDeclaration,
                    ):
                        self._check_function_declaration(member)

            finally:
                self.environment = previous_environment

        finally:
            self._class_contexts.pop()

    def _check_interface_declaration(
        self,
        declaration: InterfaceDeclaration,
    ) -> None:
        for member in declaration.members:
            self._function_type(member)

    def _check_struct_declaration(
        self,
        declaration: StructDeclaration,
    ) -> None:
        for field in declaration.fields:
            self._check_field_declaration(field)

    def _check_record_declaration(
        self,
        declaration: RecordDeclaration,
    ) -> None:
        for field in declaration.fields:
            self._check_field_declaration(field)

    def _check_field_declaration(
        self,
        declaration: FieldDeclaration,
    ) -> Type:
        declared_type = None

        if declaration.type_annotation is not None:
            declared_type = self.resolve_type(
                declaration.type_annotation
            )

        if declaration.initializer is None:
            if declared_type is None:
                raise TypeCheckError(
                    self._error_at(
                        declaration,
                        (
                            f"Field '{declaration.name.name}' "
                            "requires a type annotation."
                        ),
                    )
                )

            return declared_type

        initializer_type = self._check_expression(
            declaration.initializer
        )

        if declared_type is None:
            return initializer_type

        if not self.is_assignable(
            initializer_type,
            declared_type,
        ):
            raise InvalidAssignmentError(
                self._error_at(
                    declaration,
                    (
                        f"Field initializer of type "
                        f"'{initializer_type.name}' is not compatible "
                        f"with '{declared_type.name}'."
                    ),
                )
            )

        return declared_type

    def _check_block_contents(
        self,
        block: Block,
    ) -> None:
        previous_environment = self.environment
        self.environment = self.environment.child()

        try:
            for item in block.items:
                if isinstance(
                    item,
                    (
                        VariableDeclaration,
                        FunctionDeclaration,
                        ClassDeclaration,
                        InterfaceDeclaration,
                        StructDeclaration,
                        RecordDeclaration,
                    ),
                ):
                    self._check_declaration(item)
                else:
                    self._check_statement(item)
        finally:
            self.environment = previous_environment

    def _check_statement(
        self,
        statement: Statement,
    ) -> None:
        if isinstance(statement, Block):
            self._check_block_contents(statement)
            return

        if isinstance(statement, VariableDeclaration):
            type_ = self._check_variable_declaration(statement)

            self._define_symbol(
                statement.name.name,
                type_,
                statement,
            )
            return

        if isinstance(statement, ExpressionStatement):
            self._check_expression(statement.expression)
            return

        if isinstance(statement, EmptyStatement):
            return

        if isinstance(statement, ReturnStatement):
            self._check_return_statement(statement)
            return

        if isinstance(statement, IfStatement):
            condition_type = self._check_expression(
                statement.condition
            )

            if not is_boolean(condition_type):
                raise InvalidTypeOperationError(
                    self._error_at(
                        statement.condition,
                        "If condition must have type 'Bool'.",
                    )
                )

            self._check_statement(statement.then_branch)

            if statement.else_branch is not None:
                self._check_statement(statement.else_branch)

            return

        if isinstance(statement, WhileStatement):
            condition_type = self._check_expression(
                statement.condition
            )

            if not is_boolean(condition_type):
                raise InvalidTypeOperationError(
                    self._error_at(
                        statement.condition,
                        "While condition must have type 'Bool'.",
                    )
                )

            self._check_statement(statement.body)
            return

        if isinstance(statement, ForStatement):
            self._check_for_statement(statement)
            return

        if isinstance(statement, TryStatement):
            self._check_try_statement(statement)
            return

        raise TypeCheckError(
            self._error_at(
                statement,
                "Unsupported statement.",
            )
        )

    def _check_for_statement(
        self,
        statement: ForStatement,
    ) -> None:
        previous_environment = self.environment
        self.environment = self.environment.child()

        try:
            if statement.initializer is not None:
                self._check_for_initializer(
                    statement.initializer
                )

            if statement.condition is not None:
                condition_type = self._check_expression(
                    statement.condition
                )

                if not is_boolean(condition_type):
                    raise InvalidTypeOperationError(
                        self._error_at(
                            statement.condition,
                            "For condition must have type 'Bool'.",
                        )
                    )

            if statement.update is not None:
                self._check_expression(
                    statement.update
                )

            self._check_statement(statement.body)

        finally:
            self.environment = previous_environment

    def _check_for_initializer(
        self,
        initializer: ForInitializer,
    ) -> None:
        if isinstance(
            initializer,
            VariableDeclaration,
        ):
            type_ = self._check_variable_declaration(
                initializer
            )

            self._define_symbol(
                initializer.name.name,
                type_,
                initializer,
            )
            return

        if isinstance(
            initializer,
            ExpressionStatement,
        ):
            self._check_expression(
                initializer.expression
            )
            return

        raise TypeCheckError(
            self._error_at(
                initializer,
                "Unsupported for-loop initializer.",
            )
        )

    def _check_try_statement(
        self,
        statement: TryStatement,
    ) -> None:
        self._check_block_contents(statement.body)

        previous_environment = self.environment
        catch_environment = self.environment.child()

        self._define_symbol(
            statement.catch_name.name,
            ANY,
            statement.catch_name,
            environment=catch_environment,
        )

        self.environment = catch_environment

        try:
            self._check_block_contents(
                statement.catch_body
            )
        finally:
            self.environment = previous_environment
              def _check_return_statement(
        self,
        statement: ReturnStatement,
    ) -> None:
        if not self._function_contexts:
            raise InvalidReturnError(
                self._error_at(
                    statement,
                    "Return statement is only valid inside a function.",
                )
            )

        function_type_ = self._function_contexts[-1]

        if statement.expression is None:
            if function_type_.return_type is not VOID:
                raise InvalidReturnError(
                    self._error_at(
                        statement,
                        (
                            f"Function must return "
                            f"'{function_type_.return_type.name}'."
                        ),
                    )
                )

            return

        expression_type = self._check_expression(
            statement.expression
        )

        if function_type_.return_type is VOID:
            raise InvalidReturnError(
                self._error_at(
                    statement,
                    "Void function cannot return a value.",
                )
            )

        if not self.is_assignable(
            expression_type,
            function_type_.return_type,
        ):
            raise InvalidReturnError(
                self._error_at(
                    statement,
                    (
                        f"Cannot return type "
                        f"'{expression_type.name}' from function "
                        f"returning '{function_type_.return_type.name}'."
                    ),
                )
            )

    def _check_expression(
        self,
        expression: Expression,
    ) -> Type:
        if isinstance(expression, LiteralExpression):
            return self._literal_type(expression)

        if isinstance(expression, IdentifierExpression):
            return self._identifier_type(expression)

        if isinstance(expression, ThisExpression):
            return self._this_type(expression)

        if isinstance(expression, SuperExpression):
            return self._super_type(expression)

        if isinstance(expression, NewExpression):
            return self._new_expression_type(expression)

        if isinstance(expression, ArrayExpression):
            return self._array_expression_type(expression)

        if isinstance(expression, ParenthesizedExpression):
            return self._check_expression(
                expression.expression
            )

        if isinstance(expression, UnaryExpression):
            return self._unary_type(expression)

        if isinstance(expression, BinaryExpression):
            return self._binary_type(expression)

        if isinstance(expression, AssignmentExpression):
            return self._assignment_type(expression)

        if isinstance(expression, ConditionalExpression):
            return self._conditional_type(expression)

        if isinstance(expression, CallExpression):
            return self._call_type(expression)

        if isinstance(expression, MemberAccessExpression):
            return self._member_access_type(expression)

        if isinstance(expression, IndexExpression):
            return self._index_type(expression)

        if isinstance(expression, PostfixExpression):
            return self._postfix_type(expression)

        raise TypeCheckError(
            self._error_at(
                expression,
                "Unsupported expression.",
            )
        )

    def _literal_type(
        self,
        expression: LiteralExpression,
    ) -> Type:
        if expression.kind == "INTEGER":
            return INT

        if expression.kind == "FLOAT":
            return FLOAT

        if expression.kind == "STRING":
            return STRING

        if expression.kind == "CHAR":
            return CHAR

        if expression.kind == "BOOL":
            return BOOL

        if expression.kind == "NULL":
            return NULL

        raise TypeCheckError(
            self._error_at(
                expression,
                f"Unknown literal kind '{expression.kind}'.",
            )
        )

    def _identifier_type(
        self,
        expression: IdentifierExpression,
    ) -> Type:
        try:
            return self.environment.resolve(
                expression.identifier.name
            ).type
        except UnknownNameError as error:
            raise TypeCheckError(
                self._error_at(
                    expression,
                    str(error),
                )
            ) from error

    def _this_type(
        self,
        expression: ThisExpression,
    ) -> Type:
        if not self._class_contexts:
            raise InvalidMemberAccessError(
                self._error_at(
                    expression,
                    "'this' is only valid inside a class.",
                )
            )

        return self._class_contexts[-1]

    def _super_type(
        self,
        expression: SuperExpression,
    ) -> Type:
        if not self._class_contexts:
            raise InvalidMemberAccessError(
                self._error_at(
                    expression,
                    "'super' is only valid inside a class.",
                )
            )

        current = self._class_contexts[-1]
        info = self._type_infos.get(current.name)

        if info is None or info.extends is None:
            raise InvalidMemberAccessError(
                self._error_at(
                    expression,
                    "Class does not have a superclass.",
                )
            )

        return info.extends

    def _new_expression_type(
        self,
        expression: NewExpression,
    ) -> Type:
        type_ = self.resolve_type(
            expression.type_reference
        )

        if type_.kind not in {
            TypeKind.CLASS,
            TypeKind.STRUCT,
            TypeKind.RECORD,
        }:
            raise InvalidTypeOperationError(
                self._error_at(
                    expression,
                    (
                        f"Type '{type_.name}' cannot be "
                        "constructed with 'new'."
                    ),
                )
            )

        for argument in expression.arguments:
            self._check_expression(argument)

        return type_

    def _array_expression_type(
        self,
        expression: ArrayExpression,
    ) -> Type:
        if not expression.elements:
            return array_type(ANY)

        element_types = tuple(
            self._check_expression(element)
            for element in expression.elements
        )

        common = element_types[0]

        for element_type in element_types[1:]:
            common = self._common_type(
                common,
                element_type,
            )

        return array_type(common)

    def _unary_type(
        self,
        expression: UnaryExpression,
    ) -> Type:
        operand_type = self._check_expression(
            expression.operand
        )

        operator = expression.operator

        if operator == "await":
            if not self._function_contexts:
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        "'await' is only valid inside a function.",
                    )
                )

            if not self._function_contexts[-1].async_function:
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        "'await' requires an async function.",
                    )
                )

            return operand_type

        if operator in {"+", "-"}:
            if not is_numeric(operand_type):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        (
                            f"Unary '{operator}' requires a numeric "
                            f"operand, got '{operand_type.name}'."
                        ),
                    )
                )

            return operand_type

        if operator == "!":
            if not is_boolean(operand_type):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        "Unary '!' requires a Bool operand.",
                    )
                )

            return BOOL

        if operator in {"++", "--"}:
            if not is_numeric(operand_type):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        (
                            f"Unary '{operator}' requires a numeric "
                            f"operand."
                        ),
                    )
                )

            self._require_assignable_target(
                expression.operand
            )
            return operand_type

        raise InvalidTypeOperationError(
            self._error_at(
                expression,
                f"Unsupported unary operator '{operator}'.",
            )
        )

    def _binary_type(
        self,
        expression: BinaryExpression,
    ) -> Type:
        left_type = self._check_expression(
            expression.left
        )
        right_type = self._check_expression(
            expression.right
        )

        operator = expression.operator

        if operator in {"+", "-", "*", "/", "%"}:
            if operator == "+" and (
                left_type.kind is TypeKind.STRING
                or right_type.kind is TypeKind.STRING
            ):
                return STRING

            if not is_numeric(left_type) or not is_numeric(
                right_type
            ):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        (
                            f"Operator '{operator}' requires numeric "
                            "operands."
                        ),
                    )
                )

            if (
                left_type.kind is TypeKind.FLOAT
                or right_type.kind is TypeKind.FLOAT
            ):
                return FLOAT

            return INT

        if operator in {"<", ">", "<=", ">="}:
            if not (
                is_numeric(left_type)
                and is_numeric(right_type)
            ):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        (
                            f"Operator '{operator}' requires numeric "
                            "operands."
                        ),
                    )
                )

            return BOOL

        if operator in {"==", "!="}:
            if not (
                self.is_assignable(left_type, right_type)
                or self.is_assignable(right_type, left_type)
            ):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        (
                            f"Cannot compare '{left_type.name}' "
                            f"with '{right_type.name}'."
                        ),
                    )
                )

            return BOOL

        if operator in {"&&", "||"}:
            if not (
                is_boolean(left_type)
                and is_boolean(right_type)
            ):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        (
                            f"Operator '{operator}' requires Bool "
                            "operands."
                        ),
                    )
                )

            return BOOL

        if operator == "??":
            if not is_nullable(left_type):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        (
                            f"Left operand of '??' must be nullable, "
                            f"got '{left_type.name}'."
                        ),
                    )
                )

            if not (
                self.is_assignable(
                    right_type,
                    left_type,
                )
                or self.is_assignable(
                    left_type,
                    right_type,
                )
            ):
                raise InvalidTypeOperationError(
                    self._error_at(
                        expression,
                        (
                            f"Operands of '??' are incompatible: "
                            f"'{left_type.name}' and "
                            f"'{right_type.name}'."
                        ),
                    )
                )

            return self._common_type(
                left_type,
                right_type,
            )

        raise InvalidTypeOperationError(
            self._error_at(
                expression,
                f"Unsupported binary operator '{operator}'.",
            )
        )

    def _assignment_type(
        self,
        expression: AssignmentExpression,
    ) -> Type:
        target_type = self._check_expression(
            expression.target
        )
        value_type = self._check_expression(
            expression.value
        )

        self._require_assignable_target(
            expression.target
        )

        if not self.is_assignable(
            value_type,
            target_type,
        ):
            raise InvalidAssignmentError(
                self._error_at(
                    expression,
                    (
                        f"Cannot assign '{value_type.name}' "
                        f"to '{target_type.name}'."
                    ),
                )
            )

        return target_type
          def _conditional_type(
        self,
        expression: ConditionalExpression,
    ) -> Type:
        condition_type = self._check_expression(
            expression.condition
        )

        if not is_boolean(condition_type):
            raise InvalidTypeOperationError(
                self._error_at(
                    expression.condition,
                    "Conditional condition must have type 'Bool'.",
                )
            )

        true_type = self._check_expression(
            expression.when_true
        )
        false_type = self._check_expression(
            expression.when_false
        )

        return self._common_type(
            true_type,
            false_type,
        )

    def _call_type(
        self,
        expression: CallExpression,
    ) -> Type:
        callee_type = self._check_expression(
            expression.callee
        )

        if not isinstance(callee_type, FunctionType):
            raise InvalidCallError(
                self._error_at(
                    expression,
                    (
                        f"Type '{callee_type.name}' "
                        "is not callable."
                    ),
                )
            )

        if len(expression.arguments) != len(
            callee_type.parameter_types
        ):
            raise InvalidCallError(
                self._error_at(
                    expression,
                    (
                        f"Function expects "
                        f"{len(callee_type.parameter_types)} "
                        f"arguments, got "
                        f"{len(expression.arguments)}."
                    ),
                )
            )

        for argument, parameter_type in zip(
            expression.arguments,
            callee_type.parameter_types,
        ):
            argument_type = self._check_expression(
                argument
            )

            if not self.is_assignable(
                argument_type,
                parameter_type,
            ):
                raise InvalidCallError(
                    self._error_at(
                        argument,
                        (
                            f"Argument of type "
                            f"'{argument_type.name}' is not "
                            f"compatible with parameter type "
                            f"'{parameter_type.name}'."
                        ),
                    )
                )

        return callee_type.return_type

    def _member_access_type(
        self,
        expression: MemberAccessExpression,
    ) -> Type:
        object_type = self._check_expression(
            expression.object
        )

        member = self._find_member(
            object_type,
            expression.member.name,
        )

        if member is None:
            raise InvalidMemberAccessError(
                self._error_at(
                    expression,
                    (
                        f"Type '{object_type.name}' has no member "
                        f"'{expression.member.name}'."
                    ),
                )
            )

        return member.type

    def _index_type(
        self,
        expression: IndexExpression,
    ) -> Type:
        object_type = self._check_expression(
            expression.object
        )
        index_type = self._check_expression(
            expression.index
        )

        if index_type.kind is not TypeKind.INT:
            raise InvalidIndexError(
                self._error_at(
                    expression.index,
                    "Array index must have type 'Int'.",
                )
            )

        if not isinstance(object_type, ArrayType):
            raise InvalidIndexError(
                self._error_at(
                    expression,
                    (
                        f"Type '{object_type.name}' "
                        "is not indexable."
                    ),
                )
            )

        return object_type.element_type

    def _postfix_type(
        self,
        expression: PostfixExpression,
    ) -> Type:
        operand_type = self._check_expression(
            expression.operand
        )

        if expression.operator not in {"++", "--"}:
            raise InvalidTypeOperationError(
                self._error_at(
                    expression,
                    (
                        f"Unsupported postfix operator "
                        f"'{expression.operator}'."
                    ),
                )
            )

        if not is_numeric(operand_type):
            raise InvalidTypeOperationError(
                self._error_at(
                    expression,
                    "Postfix increment/decrement requires a numeric operand.",
                )
            )

        self._require_assignable_target(
            expression.operand
        )

        return operand_type

    def is_assignable(
        self,
        source: Type,
        target: Type,
    ) -> bool:
        """Return whether source can be assigned to target."""
        if source == target:
            return True

        if target.kind is TypeKind.ANY:
            return True

        if source.kind is TypeKind.NULL:
            return is_nullable(target)

        if isinstance(source, ArrayType) and isinstance(
            target,
            ArrayType,
        ):
            return self.is_assignable(
                source.element_type,
                target.element_type,
            )

        if (
            isinstance(source, NamedType)
            and isinstance(target, NamedType)
        ):
            return self._is_named_assignable(
                source,
                target,
            )

        return False

    def _is_named_assignable(
        self,
        source: NamedType,
        target: NamedType,
    ) -> bool:
        if source == target:
            return True

        source_info = self._type_infos.get(source.name)

        if source_info is None:
            return False

        if source_info.extends is not None:
            if self._is_named_assignable(
                source_info.extends,
                target,
            ):
                return True

        for interface in source_info.interfaces:
            if interface == target:
                return True

        return False

    def _common_type(
        self,
        left: Type,
        right: Type,
    ) -> Type:
        if left == right:
            return left

        if self.is_assignable(left, right):
            return right

        if self.is_assignable(right, left):
            return left

        if left.kind is TypeKind.NULL and is_nullable(right):
            return right

        if right.kind is TypeKind.NULL and is_nullable(left):
            return left

        raise InvalidTypeOperationError(
            f"No common type exists for '{left.name}' and '{right.name}'."
        )

    def _require_assignable_target(
        self,
        expression: Expression,
    ) -> None:
        if isinstance(expression, IdentifierExpression):
            try:
                self.environment.resolve(
                    expression.identifier.name
                )
            except UnknownNameError as error:
                raise InvalidAssignmentError(
                    self._error_at(
                        expression,
                        str(error),
                    )
                ) from error

            return

        if isinstance(expression, MemberAccessExpression):
            self._check_expression(expression)
            return

        if isinstance(expression, IndexExpression):
            self._check_expression(expression)
            return

        raise InvalidAssignmentError(
            self._error_at(
                expression,
                "Expression is not an assignable target.",
            )
        )

    def _find_member(
        self,
        type_: Type,
        name: str,
    ) -> MemberInfo | None:
        if not isinstance(type_, NamedType):
            return None

        info = self._type_infos.get(type_.name)

        if info is None:
            return None

        for member in info.members:
            if member.name == name:
                return member

        if info.extends is not None:
            return self._find_member(
                info.extends,
                name,
            )

        for interface in info.interfaces:
            member = self._find_member(
                interface,
                name,
            )

            if member is not None:
                return member

        return None
          def _complete_class_type(
        self,
        declaration: ClassDeclaration,
    ) -> None:
        type_ = self._type_infos[
            declaration.name.name
        ].type

        extends = None

        if declaration.extends is not None:
            resolved = self.resolve_type(
                declaration.extends
            )

            if not isinstance(resolved, NamedType):
                raise TypeCheckError(
                    self._error_at(
                        declaration.extends,
                        "Class superclass must be a named type.",
                    )
                )

            if resolved.kind is not TypeKind.CLASS:
                raise TypeCheckError(
                    self._error_at(
                        declaration.extends,
                        "Class can only extend another class.",
                    )
                )

            extends = resolved

        interfaces = []

        for interface_reference in declaration.implements:
            resolved = self.resolve_type(
                interface_reference
            )

            if not isinstance(resolved, NamedType):
                raise TypeCheckError(
                    self._error_at(
                        interface_reference,
                        "Implemented type must be named.",
                    )
                )

            if resolved.kind is not TypeKind.INTERFACE:
                raise TypeCheckError(
                    self._error_at(
                        interface_reference,
                        "Class can only implement interfaces.",
                    )
                )

            interfaces.append(resolved)

        members = []

        for member in declaration.members:
            if isinstance(member, FieldDeclaration):
                member_type = self._field_type(member)

                members.append(
                    MemberInfo(
                        name=member.name.name,
                        type=member_type,
                    )
                )

            elif isinstance(member, FunctionDeclaration):
                members.append(
                    MemberInfo(
                        name=member.name.name,
                        type=self._function_type(member),
                    )
                )

        self._type_infos[type_.name] = TypeInfo(
            type=type_,
            members=tuple(members),
            extends=extends,
            interfaces=tuple(interfaces),
        )

    def _complete_interface_type(
        self,
        declaration: InterfaceDeclaration,
    ) -> None:
        type_ = self._type_infos[
            declaration.name.name
        ].type

        extends = None

        if declaration.extends is not None:
            resolved = self.resolve_type(
                declaration.extends
            )

            if not isinstance(resolved, NamedType):
                raise TypeCheckError(
                    self._error_at(
                        declaration.extends,
                        "Interface parent must be a named type.",
                    )
                )

            if resolved.kind is not TypeKind.INTERFACE:
                raise TypeCheckError(
                    self._error_at(
                        declaration.extends,
                        "Interface can only extend an interface.",
                    )
                )

            extends = resolved

        members = []

        for member in declaration.members:
            members.append(
                MemberInfo(
                    name=member.name.name,
                    type=self._function_type(member),
                )
            )

        self._type_infos[type_.name] = TypeInfo(
            type=type_,
            members=tuple(members),
            extends=extends,
            interfaces=(),
        )

    def _complete_struct_type(
        self,
        declaration: StructDeclaration,
    ) -> None:
        type_ = self._type_infos[
            declaration.name.name
        ].type

        members = tuple(
            MemberInfo(
                name=field.name.name,
                type=self._field_type(field),
            )
            for field in declaration.fields
        )

        self._type_infos[type_.name] = TypeInfo(
            type=type_,
            members=members,
            extends=None,
            interfaces=(),
        )

    def _complete_record_type(
        self,
        declaration: RecordDeclaration,
    ) -> None:
        type_ = self._type_infos[
            declaration.name.name
        ].type

        members = tuple(
            MemberInfo(
                name=field.name.name,
                type=self._field_type(field),
            )
            for field in declaration.fields
        )

        self._type_infos[type_.name] = TypeInfo(
            type=type_,
            members=members,
            extends=None,
            interfaces=(),
        )

    def _field_type(
        self,
        field: FieldDeclaration,
    ) -> Type:
        if field.type_annotation is not None:
            return self.resolve_type(
                field.type_annotation
            )

        if field.initializer is not None:
            return self._check_expression(
                field.initializer
            )

        raise TypeCheckError(
            self._error_at(
                field,
                (
                    f"Field '{field.name.name}' "
                    "requires a type annotation or initializer."
                ),
            )
        )

    def _members_for_type(
        self,
        type_: NamedType,
    ) -> tuple[MemberInfo, ...]:
        info = self._type_infos.get(type_.name)

        if info is None:
            return ()

        return info.members

    def _declaration_type_kind(
        self,
        declaration: Declaration,
    ) -> TypeKind:
        if isinstance(declaration, ClassDeclaration):
            return TypeKind.CLASS

        if isinstance(declaration, InterfaceDeclaration):
            return TypeKind.INTERFACE

        if isinstance(declaration, StructDeclaration):
            return TypeKind.STRUCT

        if isinstance(declaration, RecordDeclaration):
            return TypeKind.RECORD

        raise TypeCheckError(
            self._error_at(
                declaration,
                "Declaration is not a user-defined type.",
            )
        )

    def _unwrap_declaration(
        self,
        item,
    ) -> Declaration | None:
        if isinstance(item, ExportDeclaration):
            return item.declaration

        if isinstance(
            item,
            (
                VariableDeclaration,
                FunctionDeclaration,
                ClassDeclaration,
                InterfaceDeclaration,
                StructDeclaration,
                RecordDeclaration,
            ),
        ):
            return item

        return None

    def _type_reference_name(
        self,
        reference: TypeReference,
    ) -> str:
        return ".".join(
            identifier.name
            for identifier in reference.parts
        )

    def _define_symbol(
        self,
        name: str,
        type_: Type,
        node,
        environment: TypeEnvironment | None = None,
    ) -> None:
        target_environment = (
            environment
            if environment is not None
            else self.environment
        )

        try:
            target_environment.define(
                name,
                type_,
            )
        except DuplicateDefinitionError as error:
            raise TypeCheckError(
                self._error_at(
                    node,
                    str(error),
                )
            ) from error

    def _error_at(
        self,
        node,
        message: str,
    ) -> str:
        position = getattr(
            node,
            "position",
            None,
        )

        if position is None:
            return message

        return (
            f"{message} "
            f"(line {position.line}, "
            f"column {position.column}, "
            f"offset {position.offset})"
        )


def check_compilation_unit(
    unit: CompilationUnit,
) -> None:
    """Type-check a Kupln compilation unit."""
    TypeChecker().check(unit)
