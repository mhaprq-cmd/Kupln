"""Kupln Bootstrap Declaration Type Checker.

Declaration, statement, scope, and control-flow checking.
"""

from __future__ import annotations

from dataclasses import dataclass

from bootstrap.parser.ast import (
    Block,
    ClassDeclaration,
    Declaration,
    EmptyStatement,
    ExportDeclaration,
    ExpressionStatement,
    FieldDeclaration,
    ForInitializer,
    ForStatement,
    FunctionDeclaration,
    IfStatement,
    ImportDeclaration,
    InterfaceDeclaration,
    RecordDeclaration,
    ReturnStatement,
    Statement,
    StructDeclaration,
    TryStatement,
    VariableDeclaration,
    WhileStatement,
)

from bootstrap.types.environment import (
    DuplicateDefinitionError,
    TypeEnvironment,
)

from bootstrap.types.type_system import (
    ANY,
    BOOL,
    VOID,
    FunctionType,
    Type,
    TypeKind,
)


class TypeCheckError(Exception):
    """Base class for bootstrap type-checking errors."""


class UnknownTypeError(TypeCheckError):
    """Raised when a type cannot be resolved."""


class InvalidTypeOperationError(TypeCheckError):
    """Raised when an operation is invalid for a type."""


class InvalidAssignmentError(TypeCheckError):
    """Raised when an assignment is incompatible."""


class InvalidCallError(TypeCheckError):
    """Raised when a function call is invalid."""


class InvalidReturnError(TypeCheckError):
    """Raised when a return statement is invalid."""


class InvalidMemberAccessError(TypeCheckError):
    """Raised when member access is invalid."""


class InvalidIndexError(TypeCheckError):
    """Raised when indexing is invalid."""


@dataclass(frozen=True)
class MemberInfo:
    """Information about a declared member."""

    name: str
    type: Type


@dataclass(frozen=True)
class TypeInfo:
    """Information about a user-defined type."""

    type: Type
    members: tuple[MemberInfo, ...] = ()
    extends: Type | None = None
    interfaces: tuple[Type, ...] = ()


class DeclarationCheckerMixin:
    """Mixin containing declaration and statement checks."""

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

        raise self._error_at(
            declaration.position,
            "Unsupported declaration.",
        )

    def _check_variable_declaration(
        self,
        declaration: VariableDeclaration,
    ) -> None:
        variable_type = self._declared_or_inferred_variable_type(
            declaration
        )

        if declaration.initializer is not None:
            initializer_type = self._check_expression(
                declaration.initializer
            )

            if not self.is_assignable(
                initializer_type,
                variable_type,
            ):
                raise self._error_at(
                    declaration.position,
                    (
                        f"Cannot assign value of type "
                        f"'{initializer_type.name}' to variable "
                        f"'{declaration.name.name}' of type "
                        f"'{variable_type.name}'."
                    ),
                    InvalidAssignmentError,
                )

        self._define_symbol(
            declaration.name.name,
            variable_type,
            declaration.position,
        )

    def _declared_or_inferred_variable_type(
        self,
        declaration: VariableDeclaration,
    ) -> Type:
        if declaration.type_annotation is not None:
            return self.resolve_type(declaration.type_annotation)

        if declaration.initializer is None:
            raise self._error_at(
                declaration.position,
                (
                    f"Variable '{declaration.name.name}' requires "
                    "a type annotation or initializer."
                ),
                InvalidTypeOperationError,
            )

        return self._check_expression(declaration.initializer)

    def _check_function_declaration(
        self,
        declaration: FunctionDeclaration,
    ) -> None:
        function_type = self._function_type(declaration)

        self._define_symbol(
            declaration.name.name,
            function_type,
            declaration.position,
        )

        previous_environment = self._environment
        function_environment = TypeEnvironment(previous_environment)
        self._environment = function_environment

        previous_return_type = self._current_function_return_type
        previous_async = self._current_function_async

        try:
            for parameter, parameter_type in zip(
                declaration.parameters,
                function_type.parameter_types,
            ):
                self._define_symbol(
                    parameter.name.name,
                    parameter_type,
                    parameter.position,
                )

            self._current_function_return_type = (
                function_type.return_type
            )
            self._current_function_async = (
                declaration.async_modifier
            )

            self._check_block_contents(declaration.body)

        finally:
            self._current_function_return_type = previous_return_type
            self._current_function_async = previous_async
            self._environment = previous_environment

    def _function_type(
        self,
        declaration: FunctionDeclaration,
    ) -> FunctionType:
        parameter_types: list[Type] = []

        for parameter in declaration.parameters:
            if parameter.type_annotation is None:
                raise self._error_at(
                    parameter.position,
                    (
                        f"Parameter '{parameter.name.name}' "
                        "requires a type annotation."
                    ),
                    UnknownTypeError,
                )

            parameter_types.append(
                self.resolve_type(parameter.type_annotation)
            )

        if declaration.return_type is None:
            return_type = VOID
        else:
            return_type = self.resolve_type(
                declaration.return_type
            )

        return FunctionType(
            kind=TypeKind.FUNCTION,
            name="Function",
            parameter_types=tuple(parameter_types),
            return_type=return_type,
            async_function=declaration.async_modifier,
        )

    def _check_class_declaration(
        self,
        declaration: ClassDeclaration,
    ) -> None:
        class_type = self._complete_class_type(declaration)

        previous_environment = self._environment
        class_environment = TypeEnvironment(previous_environment)
        self._environment = class_environment

        try:
            self._define_symbol(
                "this",
                class_type,
                declaration.position,
            )

            if declaration.extends is not None:
                parent_type = self.resolve_type(
                    declaration.extends
                )
                self._define_symbol(
                    "super",
                    parent_type,
                    declaration.position,
                )

            for member in declaration.members:
                if isinstance(member, FieldDeclaration):
                    self._check_field_declaration(member)
                elif isinstance(member, FunctionDeclaration):
                    self._check_function_declaration(member)
                else:
                    raise self._error_at(
                        member.position,
                        "Unsupported class member.",
                    )
        finally:
            self._environment = previous_environment

    def _check_interface_declaration(
        self,
        declaration: InterfaceDeclaration,
    ) -> None:
        self._complete_interface_type(declaration)

        previous_environment = self._environment
        interface_environment = TypeEnvironment(previous_environment)
        self._environment = interface_environment

        try:
            for member in declaration.members:
                if isinstance(member, FunctionDeclaration):
                    self._check_function_declaration(member)
                else:
                    raise self._error_at(
                        member.position,
                        "Unsupported interface member.",
                    )
        finally:
            self._environment = previous_environment

    def _check_struct_declaration(
        self,
        declaration: StructDeclaration,
    ) -> None:
        self._complete_struct_type(declaration)

        previous_environment = self._environment
        struct_environment = TypeEnvironment(previous_environment)
        self._environment = struct_environment

        try:
            for field in declaration.fields:
                self._check_field_declaration(field)
        finally:
            self._environment = previous_environment

    def _check_record_declaration(
        self,
        declaration: RecordDeclaration,
    ) -> None:
        self._complete_record_type(declaration)

        previous_environment = self._environment
        record_environment = TypeEnvironment(previous_environment)
        self._environment = record_environment

        try:
            for field in declaration.fields:
                self._check_field_declaration(field)
        finally:
            self._environment = previous_environment

    def _check_field_declaration(
        self,
        declaration: FieldDeclaration,
    ) -> None:
        if declaration.type_annotation is None:
            if declaration.initializer is None:
                raise self._error_at(
                    declaration.position,
                    (
                        f"Field '{declaration.name.name}' requires "
                        "a type annotation or initializer."
                    ),
                    InvalidTypeOperationError,
                )

            field_type = self._check_expression(
                declaration.initializer
            )
        else:
            field_type = self.resolve_type(
                declaration.type_annotation
            )

            if declaration.initializer is not None:
                initializer_type = self._check_expression(
                    declaration.initializer
                )

                if not self.is_assignable(
                    initializer_type,
                    field_type,
                ):
                    raise self._error_at(
                        declaration.position,
                        (
                            f"Cannot assign value of type "
                            f"'{initializer_type.name}' to field "
                            f"'{declaration.name.name}' of type "
                            f"'{field_type.name}'."
                        ),
                        InvalidAssignmentError,
                    )

        self._define_symbol(
            declaration.name.name,
            field_type,
            declaration.position,
        )

    def _check_block_contents(self, block: Block) -> None:
        previous_environment = self._environment
        block_environment = TypeEnvironment(previous_environment)
        self._environment = block_environment

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
            self._environment = previous_environment

    def _check_statement(self, statement: Statement) -> None:
        if isinstance(statement, Block):
            self._check_block_contents(statement)
            return

        if isinstance(statement, VariableDeclaration):
            self._check_variable_declaration(statement)
            return

        if isinstance(statement, ExpressionStatement):
            self._check_expression(statement.expression)
            return

        if isinstance(statement, ReturnStatement):
            self._check_return_statement(statement)
            return

        if isinstance(statement, IfStatement):
            condition_type = self._check_expression(
                statement.condition
            )

            if condition_type != BOOL:
                raise self._error_at(
                    statement.condition.position,
                    "If condition must have type 'Bool'.",
                    InvalidTypeOperationError,
                )

            self._check_statement(statement.then_branch)

            if statement.else_branch is not None:
                self._check_statement(statement.else_branch)

            return

        if isinstance(statement, WhileStatement):
            condition_type = self._check_expression(
                statement.condition
            )

            if condition_type != BOOL:
                raise self._error_at(
                    statement.condition.position,
                    "While condition must have type 'Bool'.",
                    InvalidTypeOperationError,
                )

            self._check_statement(statement.body)
            return

        if isinstance(statement, ForStatement):
            self._check_for_statement(statement)
            return

        if isinstance(statement, TryStatement):
            self._check_try_statement(statement)
            return

        if isinstance(statement, EmptyStatement):
            return

        raise self._error_at(
            statement.position,
            "Unsupported statement.",
        )

    def _check_for_statement(
        self,
        statement: ForStatement,
    ) -> None:
        previous_environment = self._environment
        for_environment = TypeEnvironment(previous_environment)
        self._environment = for_environment

        try:
            if statement.initializer is not None:
                self._check_for_initializer(
                    statement.initializer
                )

            if statement.condition is not None:
                condition_type = self._check_expression(
                    statement.condition
                )

                if condition_type != BOOL:
                    raise self._error_at(
                        statement.condition.position,
                        "For condition must have type 'Bool'.",
                        InvalidTypeOperationError,
                    )

            if statement.update is not None:
                self._check_expression(statement.update)

            self._check_statement(statement.body)
        finally:
            self._environment = previous_environment

    def _check_for_initializer(
        self,
        initializer: ForInitializer,
    ) -> None:
        if isinstance(initializer, VariableDeclaration):
            self._check_variable_declaration(initializer)
            return

        if isinstance(initializer, ExpressionStatement):
            self._check_expression(initializer.expression)
            return

        raise self._error_at(
            initializer.position,
            "Unsupported for-loop initializer.",
        )

    def _check_try_statement(
        self,
        statement: TryStatement,
    ) -> None:
        self._check_block_contents(statement.body)

        previous_environment = self._environment
        catch_environment = TypeEnvironment(previous_environment)
        self._environment = catch_environment

        try:
            self._define_symbol(
                statement.catch_name.name,
                ANY,
                statement.catch_name.position,
            )
            self._check_block_contents(statement.catch_body)
        finally:
            self._environment = previous_environment

    def _check_return_statement(
        self,
        statement: ReturnStatement,
    ) -> None:
        return_type = self._current_function_return_type

        if return_type is None:
            raise self._error_at(
                statement.position,
                "Return statement is only valid inside a function.",
                InvalidReturnError,
            )

        if statement.expression is None:
            if return_type.kind != TypeKind.VOID:
                raise self._error_at(
                    statement.position,
                    (
                        f"Expected return value of type "
                        f"'{return_type.name}'."
                    ),
                    InvalidReturnError,
                )
            return

        expression_type = self._check_expression(
            statement.expression
        )

        if return_type.kind == TypeKind.VOID:
            raise self._error_at(
                statement.position,
                "Void functions cannot return a value.",
                InvalidReturnError,
            )

        if not self.is_assignable(
            expression_type,
            return_type,
        ):
            raise self._error_at(
                statement.position,
                (
                    f"Cannot return value of type "
                    f"'{expression_type.name}' from function "
                    f"returning '{return_type.name}'."
                ),
                InvalidReturnError,
            )

    def _define_symbol(
        self,
        name: str,
        symbol_type: Type,
        position,
    ) -> None:
        try:
            self._environment.define(name, symbol_type)
        except DuplicateDefinitionError:
            raise self._error_at(
                position,
                f"Duplicate definition of '{name}'.",
                InvalidTypeOperationError,
            )

    def _error_at(
        self,
        position,
        message: str,
        error_type: type[TypeCheckError] = TypeCheckError,
    ) -> TypeCheckError:
        location = (
            f" at line {position.line}, "
            f"column {position.column}"
        )

        return error_type(message + location)
