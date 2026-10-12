"""Lower supported Kupln AST constructs into platform-independent IR."""

from __future__ import annotations

from bootstrap.ir.model import (
    IRBasicBlock,
    IRConstant,
    IRFunction,
    IRInstruction,
    IRModule,
    IROpcode,
    IRParameter,
    IRSourceLocation,
    IRValue,
)
from bootstrap.parser.ast import (
    AssignmentExpression,
    BinaryExpression,
    Block,
    CallExpression,
    CompilationUnit,
    EmptyStatement,
    Expression,
    ExpressionStatement,
    ExportDeclaration,
    FunctionDeclaration,
    IdentifierExpression,
    LiteralExpression,
    ParenthesizedExpression,
    ReturnStatement,
    UnaryExpression,
    VariableDeclaration,
)


class IRLoweringError(Exception):
    """Raised when an AST construct cannot be represented correctly in IR."""

    def __init__(self, message: str, position) -> None:
        self.message = message
        self.position = position
        super().__init__(
            f"{message} at line {position.line}, "
            f"column {position.column}"
        )


def _source_location(node) -> IRSourceLocation:
    """Convert an AST source position into an IR source location."""
    position = node.position
    return IRSourceLocation(
        line=position.line,
        column=position.column,
        offset=position.offset,
    )


def _type_name(reference) -> str | None:
    """Return a normalized source-level type name."""
    if reference is None:
        return None
    return ".".join(part.name for part in reference.parts)


class _FunctionLowerer:
    """Lower the explicitly supported constructs of one function."""

    def __init__(self, function_names: set[str]) -> None:
        self._function_names = function_names
        self._instructions: list[IRInstruction] = []
        self._variable_types: dict[str, str | None] = {}
        self._temporary_index = 0

    def lower(self, declaration: FunctionDeclaration) -> IRFunction:
        """Lower one synchronous function with an entry basic block."""
        if declaration.async_modifier:
            raise IRLoweringError(
                "Async functions are not supported by the initial IR lowering.",
                declaration.position,
            )

        if declaration.modifiers:
            raise IRLoweringError(
                "Function modifiers are not supported by the initial IR lowering.",
                declaration.position,
            )

        parameters: list[IRParameter] = []

        for parameter in declaration.parameters:
            name = parameter.name.name
            if name in self._variable_types:
                raise IRLoweringError(
                    f"Duplicate parameter name '{name}'.",
                    parameter.position,
                )

            parameter_type = _type_name(parameter.type_annotation)
            parameters.append(
                IRParameter(name=name, type_name=parameter_type)
            )
            self._variable_types[name] = parameter_type

            parameter_value = IRValue(
                name=f"%arg_{name}",
                type_name=parameter_type,
            )
            self._instructions.append(
                IRInstruction(
                    opcode=IROpcode.PARAMETER,
                    result=parameter_value,
                    operands=(name,),
                    source_location=_source_location(parameter),
                )
            )

        self._lower_function_body(declaration.body)

        block = IRBasicBlock(
            name="entry",
            instructions=tuple(self._instructions),
        )

        return IRFunction(
            name=declaration.name.name,
            parameters=tuple(parameters),
            return_type=_type_name(declaration.return_type),
            blocks=(block,),
        )

    def _lower_function_body(self, body: Block) -> None:
        for item in body.items:
            if isinstance(item, VariableDeclaration):
                self._lower_variable_declaration(item)
            elif isinstance(item, ReturnStatement):
                self._lower_return(item)
            elif isinstance(item, ExpressionStatement):
                self._lower_expression(item.expression)
            elif isinstance(item, EmptyStatement):
                continue
            else:
                raise IRLoweringError(
                    f"Unsupported function-body construct: "
                    f"{type(item).__name__}.",
                    item.position,
                )

    def _lower_variable_declaration(
        self,
        declaration: VariableDeclaration,
    ) -> None:
        name = declaration.name.name

        if name in self._variable_types:
            raise IRLoweringError(
                f"Duplicate variable name '{name}' in the supported IR scope.",
                declaration.position,
            )

        declared_type = _type_name(declaration.type_annotation)
        self._variable_types[name] = declared_type

        variable = IRValue(name=name, type_name=declared_type)
        self._instructions.append(
            IRInstruction(
                opcode=IROpcode.DECLARE_VARIABLE,
                result=variable,
                source_location=_source_location(declaration),
            )
        )

        if declaration.initializer is not None:
            value = self._lower_expression(declaration.initializer)
            self._instructions.append(
                IRInstruction(
                    opcode=IROpcode.STORE,
                    operands=(name, value),
                    source_location=_source_location(declaration),
                )
            )

    def _lower_return(self, statement: ReturnStatement) -> None:
        operands: tuple[IRValue | IRConstant | str, ...] = ()

        if statement.expression is not None:
            value = self._lower_expression(statement.expression)
            operands = (value,)

        self._instructions.append(
            IRInstruction(
                opcode=IROpcode.RETURN,
                operands=operands,
                source_location=_source_location(statement),
            )
        )

    def _new_temporary(self, type_name: str | None = None) -> IRValue:
        value = IRValue(
            name=f"%t{self._temporary_index}",
            type_name=type_name,
        )
        self._temporary_index += 1
        return value

    def _lower_expression(self, expression: Expression) -> IRValue:
        if isinstance(expression, LiteralExpression):
            result = self._new_temporary()
            self._instructions.append(
                IRInstruction(
                    opcode=IROpcode.CONSTANT,
                    result=result,
                    operands=(
                        IRConstant(
                            kind=expression.kind,
                            value=expression.value,
                        ),
                    ),
                    source_location=_source_location(expression),
                )
            )
            return result

        if isinstance(expression, IdentifierExpression):
            name = expression.identifier.name
            if name not in self._variable_types:
                raise IRLoweringError(
                    f"Identifier '{name}' is outside the supported local scope.",
                    expression.position,
                )

            result = self._new_temporary(self._variable_types[name])
            self._instructions.append(
                IRInstruction(
                    opcode=IROpcode.LOAD,
                    result=result,
                    operands=(name,),
                    source_location=_source_location(expression),
                )
            )
            return result

        if isinstance(expression, ParenthesizedExpression):
            return self._lower_expression(expression.expression)

        if isinstance(expression, UnaryExpression):
            operand = self._lower_expression(expression.operand)
            result = self._new_temporary()
            self._instructions.append(
                IRInstruction(
                    opcode=IROpcode.UNARY,
                    result=result,
                    operands=(expression.operator, operand),
                    source_location=_source_location(expression),
                )
            )
            return result

        if isinstance(expression, BinaryExpression):
            left = self._lower_expression(expression.left)
            right = self._lower_expression(expression.right)
            result = self._new_temporary()
            self._instructions.append(
                IRInstruction(
                    opcode=IROpcode.BINARY,
                    result=result,
                    operands=(expression.operator, left, right),
                    source_location=_source_location(expression),
                )
            )
            return result

        if isinstance(expression, AssignmentExpression):
            if not isinstance(expression.target, IdentifierExpression):
                raise IRLoweringError(
                    "Only assignment to a local identifier is supported.",
                    expression.target.position,
                )

            name = expression.target.identifier.name
            if name not in self._variable_types:
                raise IRLoweringError(
                    f"Assignment target '{name}' is outside the supported local scope.",
                    expression.target.position,
                )

            value = self._lower_expression(expression.value)
            self._instructions.append(
                IRInstruction(
                    opcode=IROpcode.STORE,
                    operands=(name, value),
                    source_location=_source_location(expression),
                )
            )
            return value

        if isinstance(expression, CallExpression):
            if isinstance(expression.callee, IdentifierExpression):
                callee_name = expression.callee.identifier.name

                if callee_name in self._variable_types:
                    callee: IRValue | str = self._lower_expression(
                        expression.callee
                    )
                elif callee_name in self._function_names:
                    callee = callee_name
                else:
                    raise IRLoweringError(
                        f"Call target '{callee_name}' is not a known "
                        "function in the compilation unit.",
                        expression.callee.position,
                    )
            else:
                raise IRLoweringError(
                    "Only calls to named functions or local callable values "
                    "are supported.",
                    expression.callee.position,
                )

            arguments = tuple(
                self._lower_expression(argument)
                for argument in expression.arguments
            )
            result = self._new_temporary()
            self._instructions.append(
                IRInstruction(
                    opcode=IROpcode.CALL,
                    result=result,
                    operands=(callee, *arguments),
                    source_location=_source_location(expression),
                )
            )
            return result

        raise IRLoweringError(
            f"Unsupported expression construct: {type(expression).__name__}.",
            expression.position,
        )


def lower_compilation_unit(
    compilation_unit: CompilationUnit,
) -> IRModule:
    """Lower supported top-level function declarations into an IR module.

    This function transforms an AST; callers must run the existing
    type-checking and semantic-analysis stages before lowering.
    """
    declarations: list[FunctionDeclaration] = []

    for item in compilation_unit.items:
        if isinstance(item, FunctionDeclaration):
            declarations.append(item)
        elif isinstance(item, ExportDeclaration):
            raise IRLoweringError(
                "Export declarations are not supported by the initial IR.",
                item.position,
            )
        else:
            raise IRLoweringError(
                f"Unsupported top-level construct: {type(item).__name__}.",
                item.position,
            )

    function_names = {declaration.name.name for declaration in declarations}

    if len(function_names) != len(declarations):
        for index, declaration in enumerate(declarations):
            if declaration.name.name in {
                earlier.name.name for earlier in declarations[:index]
            }:
                raise IRLoweringError(
                    f"Duplicate function name '{declaration.name.name}'.",
                    declaration.name.position,
                )

    functions = tuple(
        _FunctionLowerer(function_names).lower(declaration)
        for declaration in declarations
    )
    return IRModule(functions=functions)


__all__ = [
    "IRLoweringError",
    "lower_compilation_unit",
]
