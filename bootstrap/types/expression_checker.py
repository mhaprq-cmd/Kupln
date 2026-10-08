"""Kupln Bootstrap Expression Type Checker.

Expression type inference and validation for the bootstrap type checker.
"""

from __future__ import annotations

from bootstrap.parser.ast import (
    ArrayExpression,
    AssignmentExpression,
    BinaryExpression,
    CallExpression,
    ConditionalExpression,
    Expression,
    IdentifierExpression,
    IndexExpression,
    LiteralExpression,
    MemberAccessExpression,
    NewExpression,
    ParenthesizedExpression,
    PostfixExpression,
    SuperExpression,
    ThisExpression,
    UnaryExpression,
)

from bootstrap.types.declaration_checker import (
    InvalidAssignmentError,
    InvalidCallError,
    InvalidIndexError,
    InvalidMemberAccessError,
    InvalidTypeOperationError,
)

from bootstrap.types.type_system import (
    ANY,
    BOOL,
    CHAR,
    FLOAT,
    INT,
    NULL,
    STRING,
    ArrayType,
    FunctionType,
    NamedType,
    Type,
    TypeKind,
    array_type,
    is_boolean,
    is_nullable,
    is_numeric,
)


class ExpressionCheckerMixin:
    """Mixin containing expression checking responsibilities."""

    def _check_expression(self, expression: Expression) -> Type:
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
            return self._check_expression(expression.expression)

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

        raise self._error_at(
            expression.position,
            "Unsupported expression.",
        )

    def _literal_type(
        self,
        expression: LiteralExpression,
    ) -> Type:
        kind = expression.kind.upper()

        if kind == "INTEGER":
            return INT

        if kind == "FLOAT":
            return FLOAT

        if kind == "STRING":
            return STRING

        if kind == "CHAR":
            return CHAR

        if kind == "BOOL":
            return BOOL

        if kind == "NULL":
            return NULL

        raise self._error_at(
            expression.position,
            f"Unsupported literal kind '{expression.kind}'.",
        )

    def _identifier_type(
        self,
        expression: IdentifierExpression,
    ) -> Type:
        name = expression.identifier.name

        try:
            symbol = self._environment.resolve(name)
        except Exception:
            raise self._error_at(
                expression.position,
                f"Unknown identifier '{name}'.",
            )

        return symbol.type

    def _this_type(
        self,
        expression: ThisExpression,
    ) -> Type:
        try:
            return self._environment.resolve("this").type
        except Exception:
            raise self._error_at(
                expression.position,
                "'this' is only valid inside a class.",
            )

    def _super_type(
        self,
        expression: SuperExpression,
    ) -> Type:
        try:
            return self._environment.resolve("super").type
        except Exception:
            raise self._error_at(
                expression.position,
                "'super' is not available in this context.",
        )
        try:
            return self._environment.lookup("super").type
        except Exception:
            raise self._error_at(
                expression.position,
                "'super' is not available in this context.",
            )

    def _new_expression_type(
        self,
        expression: NewExpression,
    ) -> Type:
        target_type = self.resolve_type(
            expression.type_reference
        )

        if target_type.kind not in {
            TypeKind.CLASS,
            TypeKind.STRUCT,
            TypeKind.RECORD,
        }:
            raise self._error_at(
                expression.position,
                (
                    f"Type '{target_type.name}' cannot be "
                    "constructed with 'new'."
                ),
            )

        for argument in expression.arguments:
            self._check_expression(argument)

        return target_type

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

        result_type = element_types[0]

        for element_type in element_types[1:]:
            common = self._common_type(
                result_type,
                element_type,
            )

            if common is None:
                raise self._error_at(
                    expression.position,
                    (
                        "Array elements do not have a "
                        "compatible common type."
                    ),
                    InvalidTypeOperationError,
                )

            result_type = common

        return array_type(result_type)

    def _unary_type(
        self,
        expression: UnaryExpression,
    ) -> Type:
        operand_type = self._check_expression(
            expression.operand
        )
        operator = expression.operator

        if operator in {"+", "-"}:
            if not is_numeric(operand_type):
                raise self._error_at(
                    expression.position,
                    (
                        f"Unary '{operator}' requires a numeric "
                        f"operand, got '{operand_type.name}'."
                    ),
                    InvalidTypeOperationError,
                )
            return operand_type

        if operator == "!":
            if not is_boolean(operand_type):
                raise self._error_at(
                    expression.position,
                    "Unary '!' requires a Bool operand.",
                    InvalidTypeOperationError,
                )
            return BOOL

        if operator in {"++", "--"}:
            if not is_numeric(operand_type):
                raise self._error_at(
                    expression.position,
                    (
                        f"Unary '{operator}' requires a numeric "
                        f"operand."
                    ),
                    InvalidTypeOperationError,
                )

            self._require_assignable_target(
                expression.operand
            )
            return operand_type

        if operator == "await":
            if not self._current_function_async:
                raise self._error_at(
                    expression.position,
                    "'await' is only valid inside an async function.",
                    InvalidTypeOperationError,
                )

            return operand_type

        raise self._error_at(
            expression.position,
            f"Unsupported unary operator '{operator}'.",
            InvalidTypeOperationError,
        )

    def _binary_type(
        self,
        expression: BinaryExpression,
    ) -> Type:
        left_type = self._check_expression(expression.left)
        right_type = self._check_expression(expression.right)
        operator = expression.operator

        if operator in {"+", "-", "*", "/", "%"}:
            return self._arithmetic_type(
                expression,
                left_type,
                right_type,
            )

        if operator in {"<", ">", "<=", ">="}:
            if not is_numeric(left_type) or not is_numeric(right_type):
                raise self._error_at(
                    expression.position,
                    (
                        f"Operator '{operator}' requires "
                        "numeric operands."
                    ),
                    InvalidTypeOperationError,
                )
            return BOOL

        if operator in {"==", "!="}:
            if (
                self._common_type(left_type, right_type) is None
                and self._common_type(right_type, left_type) is None
            ):
                raise self._error_at(
                    expression.position,
                    (
                        f"Cannot compare '{left_type.name}' "
                        f"with '{right_type.name}'."
                    ),
                    InvalidTypeOperationError,
                )
            return BOOL

        if operator in {"&&", "||"}:
            if not is_boolean(left_type) or not is_boolean(right_type):
                raise self._error_at(
                    expression.position,
                    (
                        f"Operator '{operator}' requires "
                        "Bool operands."
                    ),
                    InvalidTypeOperationError,
                )
            return BOOL

        if operator == "??":
            return self._null_coalescing_type(
                expression,
                left_type,
                right_type,
            )

        raise self._error_at(
            expression.position,
            f"Unsupported binary operator '{operator}'.",
            InvalidTypeOperationError,
        )

        def _arithmetic_type(
        self,
        expression: BinaryExpression,
        left_type: Type,
        right_type: Type,
    ) -> Type:
        operator = expression.operator

        if operator == "+" and (
            left_type == STRING and right_type == STRING
        ):
            return STRING

        if not is_numeric(left_type) or not is_numeric(right_type):
            raise self._error_at(
                expression.position,
                (
                    f"Operator '{operator}' requires numeric "
                    "operands."
                ),
                InvalidTypeOperationError,
            )

        if left_type != right_type:
            raise self._error_at(
                expression.position,
                (
                    f"Operator '{operator}' requires operands "
                    "of the same numeric type."
                ),
                InvalidTypeOperationError,
            )

        return left_type

    def _null_coalescing_type(
        self,
        expression: BinaryExpression,
        left_type: Type,
        right_type: Type,
    ) -> Type:
        if not is_nullable(left_type):
            raise self._error_at(
                expression.position,
                (
                    f"Left operand of '??' must be nullable, "
                    f"got '{left_type.name}'."
                ),
                InvalidTypeOperationError,
            )

        if not self.is_assignable(
            right_type,
            left_type,
        ) and left_type != NULL:
            common = self._common_type(
                left_type,
                right_type,
            )

            if common is None:
                raise self._error_at(
                    expression.position,
                    (
                        f"Operands of '??' are incompatible: "
                        f"'{left_type.name}' and "
                        f"'{right_type.name}'."
                    ),
                    InvalidTypeOperationError,
                )

            return common

        return left_type
    def _assignment_type(
        self,
        expression: AssignmentExpression,
    ) -> Type:
        self._require_assignable_target(
            expression.target
        )

        target_type = self._check_expression(
            expression.target
        )
        value_type = self._check_expression(
            expression.value
        )

        if not self.is_assignable(
            value_type,
            target_type,
        ):
            raise self._error_at(
                expression.position,
                (
                    f"Cannot assign '{value_type.name}' "
                    f"to '{target_type.name}'."
                ),
                InvalidAssignmentError,
            )

        return target_type

    def _conditional_type(
        self,
        expression: ConditionalExpression,
    ) -> Type:
        condition_type = self._check_expression(
            expression.condition
        )

        if condition_type != BOOL:
            raise self._error_at(
                expression.condition.position,
                "Conditional condition must have type 'Bool'.",
                InvalidTypeOperationError,
            )

        true_type = self._check_expression(
            expression.when_true
        )
        false_type = self._check_expression(
            expression.when_false
        )

        common = self._common_type(
            true_type,
            false_type,
        )

        if common is None:
            common = self._common_type(
                false_type,
                true_type,
            )

        if common is None:
            raise self._error_at(
                expression.position,
                (
                    f"Conditional branches have incompatible "
                    f"types '{true_type.name}' and "
                    f"'{false_type.name}'."
                ),
                InvalidTypeOperationError,
            )

        return common

    def _call_type(
        self,
        expression: CallExpression,
    ) -> Type:
        callee_type = self._check_expression(
            expression.callee
        )

        if callee_type.kind != TypeKind.FUNCTION:
            raise self._error_at(
                expression.position,
                (
                    f"Type '{callee_type.name}' is not callable."
                ),
                InvalidCallError,
            )

        function_type = callee_type

        if not isinstance(function_type, FunctionType):
            raise self._error_at(
                expression.position,
                "Invalid function type representation.",
                InvalidCallError,
            )

        if len(expression.arguments) != len(
            function_type.parameter_types
        ):
            raise self._error_at(
                expression.position,
                (
                    f"Expected {len(function_type.parameter_types)} "
                    f"arguments but got "
                    f"{len(expression.arguments)}."
                ),
                InvalidCallError,
            )

        for argument, parameter_type in zip(
            expression.arguments,
            function_type.parameter_types,
        ):
            argument_type = self._check_expression(argument)

            if not self.is_assignable(
                argument_type,
                parameter_type,
            ):
                raise self._error_at(
                    argument.position,
                    (
                        f"Argument of type '{argument_type.name}' "
                        f"is not compatible with parameter type "
                        f"'{parameter_type.name}'."
                    ),
                    InvalidCallError,
                )

        return function_type.return_type

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
            raise self._error_at(
                expression.position,
                (
                    f"Type '{object_type.name}' has no member "
                    f"'{expression.member.name}'."
                ),
                InvalidMemberAccessError,
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

        if index_type != INT:
            raise self._error_at(
                expression.index.position,
                "Array index must have type 'Int'.",
                InvalidIndexError,
            )

        if not isinstance(object_type, ArrayType):
            raise self._error_at(
                expression.position,
                (
                    f"Type '{object_type.name}' is not "
                    "indexable."
                ),
                InvalidIndexError,
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
            raise self._error_at(
                expression.position,
                (
                    f"Unsupported postfix operator "
                    f"'{expression.operator}'."
                ),
                InvalidTypeOperationError,
            )

        if not is_numeric(operand_type):
            raise self._error_at(
                expression.position,
                (
                    f"Postfix '{expression.operator}' requires "
                    "a numeric operand."
                ),
                InvalidTypeOperationError,
            )

        self._require_assignable_target(
            expression.operand
        )

        return operand_type

    def _require_assignable_target(
        self,
        expression: Expression,
    ) -> None:
        if isinstance(
            expression,
            (
                IdentifierExpression,
                MemberAccessExpression,
                IndexExpression,
            ),
        ):
            return

        raise self._error_at(
            expression.position,
            "Expression is not an assignable target.",
            InvalidAssignmentError,
        )

    def is_assignable(
        self,
        source: Type,
        target: Type,
    ) -> bool:
        if source == target:
            return True

        if target == ANY:
            return True

        if source == NULL:
            return is_nullable(target)

        if source.kind == TypeKind.ANY:
            return True

        if (
            source.kind == TypeKind.ARRAY
            and target.kind == TypeKind.ARRAY
        ):
            if not isinstance(source, ArrayType):
                return False

            if not isinstance(target, ArrayType):
                return False

            return self.is_assignable(
                source.element_type,
                target.element_type,
            )

        if (
            source.kind == TypeKind.FUNCTION
            and target.kind == TypeKind.FUNCTION
        ):
            if not isinstance(source, FunctionType):
                return False

            if not isinstance(target, FunctionType):
                return False

            if len(source.parameter_types) != len(
                target.parameter_types
            ):
                return False

            for source_parameter, target_parameter in zip(
                source.parameter_types,
                target.parameter_types,
            ):
                if not self.is_assignable(
                    target_parameter,
                    source_parameter,
                ):
                    return False

            return self.is_assignable(
                source.return_type,
                target.return_type,
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

        current = source

        visited: set[str] = set()

        while current is not None:
            if current.name in visited:
                break

            visited.add(current.name)

            info = self._type_infos.get(current.name)

            if info is None:
                break

            if info.extends == target:
                return True

            for interface in info.interfaces:
                if interface == target:
                    return True

            if info.extends is None:
                break

            if not isinstance(info.extends, NamedType):
                break

            current = info.extends

        return False

    def _common_type(
        self,
        left: Type,
        right: Type,
    ) -> Type | None:
        if left == right:
            return left

        if self.is_assignable(left, right):
            return right

        if self.is_assignable(right, left):
            return left

        if is_numeric(left) and is_numeric(right):
            if left == FLOAT or right == FLOAT:
                return FLOAT

            return INT

        return None

    def _find_member(
        self,
        object_type: Type,
        member_name: str,
    ):
        if object_type.kind == TypeKind.ARRAY:
            if member_name == "length":
                return self._member_info(
                    "length",
                    INT,
                )

        if not isinstance(object_type, NamedType):
            return None

        info = self._type_infos.get(object_type.name)

        if info is None:
            return None

        for member in info.members:
            if member.name == member_name:
                return member

        if info.extends is not None:
            inherited = self._find_member(
                info.extends,
                member_name,
            )

            if inherited is not None:
                return inherited

        for interface in info.interfaces:
            inherited = self._find_member(
                interface,
                member_name,
            )

            if inherited is not None:
                return inherited

        return None

    def _member_info(
        self,
        name: str,
        member_type: Type,
    ):
        from bootstrap.types.checker import MemberInfo

        return MemberInfo(
            name=name,
            type=member_type,
        )
