"""Kupln Bootstrap Type Checker.

Coordinator for declaration and expression type checking.
"""

from __future__ import annotations

from bootstrap.parser.ast import (
    ClassDeclaration,
    CompilationUnit,
    FieldDeclaration,
    FunctionDeclaration,
    InterfaceDeclaration,
    RecordDeclaration,
    StructDeclaration,
    TypeReference,
)

from bootstrap.types.declaration_checker import (
    DeclarationCheckerMixin,
    InvalidAssignmentError,
    InvalidCallError,
    InvalidIndexError,
    InvalidMemberAccessError,
    InvalidReturnError,
    InvalidTypeOperationError,
    MemberInfo,
    TypeCheckError,
    TypeInfo,
    UnknownTypeError,
)

from bootstrap.types.environment import (
    TypeEnvironment,
    create_root_environment,
)

from bootstrap.types.expression_checker import (
    ExpressionCheckerMixin,
)

from bootstrap.types.type_system import (
    BUILTIN_TYPES,
    FunctionType,
    Type,
    TypeKind,
    function_type,
    named_type,
)


class TypeChecker(
    DeclarationCheckerMixin,
    ExpressionCheckerMixin,
):
    """Bootstrap Type System checker."""

    def __init__(self) -> None:
        self._environment = create_root_environment()
        self._type_infos: dict[str, TypeInfo] = {}

        self._current_function_return_type: Type | None = None
        self._current_function_async = False

        self._register_builtin_types()

    def _register_builtin_types(self) -> None:
        """Register built-in types for name resolution."""
        for name, type_ in BUILTIN_TYPES.items():
            self._type_infos[name] = TypeInfo(
                type=type_,
            )

    def check(self, compilation_unit: CompilationUnit) -> None:
        """Check a complete compilation unit."""

        self._register_declarations(
            compilation_unit
        )

        self._register_top_level_symbols(
            compilation_unit
        )

        for item in compilation_unit.items:
            self._check_top_level_item(item)

    def resolve_type(
        self,
        type_reference: TypeReference,
    ) -> Type:
        """Resolve a syntax type reference to a Type."""

        if not type_reference.parts:
            raise self._error_at(
                type_reference.position,
                "Empty type reference.",
                UnknownTypeError,
            )

        if len(type_reference.parts) != 1:
            raise self._error_at(
                type_reference.position,
                "Qualified type names are not supported yet.",
                UnknownTypeError,
            )

        name = type_reference.parts[0].name

        builtin = BUILTIN_TYPES.get(name)

        if builtin is not None:
            return builtin

        info = self._type_infos.get(name)

        if info is None:
            raise self._error_at(
                type_reference.position,
                f"Unknown type '{name}'.",
                UnknownTypeError,
            )

        return info.type

    def _register_declarations(
        self,
        compilation_unit: CompilationUnit,
    ) -> None:
        """Register all user-defined types before checking bodies."""

        for item in compilation_unit.items:
            declaration = item

            if hasattr(item, "declaration"):
                declaration = item.declaration

            if isinstance(declaration, ClassDeclaration):
                self._register_class_type(declaration)

            elif isinstance(declaration, InterfaceDeclaration):
                self._register_interface_type(declaration)

            elif isinstance(declaration, StructDeclaration):
                self._register_struct_type(declaration)

            elif isinstance(declaration, RecordDeclaration):
                self._register_record_type(declaration)

    def _register_class_type(
        self,
        declaration: ClassDeclaration,
    ) -> Type:
        name = declaration.name.name

        existing = self._type_infos.get(name)

        if existing is not None:
            if existing.type.kind in {
                TypeKind.CLASS,
                TypeKind.INTERFACE,
                TypeKind.STRUCT,
                TypeKind.RECORD,
            }:
                return existing.type

        type_ = named_type(
            name,
            TypeKind.CLASS,
        )

        self._type_infos[name] = TypeInfo(
            type=type_,
        )

        return type_

    def _register_interface_type(
        self,
        declaration: InterfaceDeclaration,
    ) -> Type:
        name = declaration.name.name

        existing = self._type_infos.get(name)

        if existing is not None:
            return existing.type

        type_ = named_type(
            name,
            TypeKind.INTERFACE,
        )

        self._type_infos[name] = TypeInfo(
            type=type_,
        )

        return type_

    def _register_struct_type(
        self,
        declaration: StructDeclaration,
    ) -> Type:
        name = declaration.name.name

        existing = self._type_infos.get(name)

        if existing is not None:
            return existing.type

        type_ = named_type(
            name,
            TypeKind.STRUCT,
        )

        self._type_infos[name] = TypeInfo(
            type=type_,
        )

        return type_

    def _register_record_type(
        self,
        declaration: RecordDeclaration,
    ) -> Type:
        name = declaration.name.name

        existing = self._type_infos.get(name)

        if existing is not None:
            return existing.type

        type_ = named_type(
            name,
            TypeKind.RECORD,
        )

        self._type_infos[name] = TypeInfo(
            type=type_,
        )

        return type_

    def _register_top_level_symbols(
        self,
        compilation_unit: CompilationUnit,
    ) -> None:
        """Register top-level callable and type names."""

        for item in compilation_unit.items:
            declaration = item

            if hasattr(item, "declaration"):
                declaration = item.declaration

            if isinstance(
                declaration,
                (
                    ClassDeclaration,
                    InterfaceDeclaration,
                    StructDeclaration,
                    RecordDeclaration,
                ),
            ):
                info = self._type_infos.get(
                    declaration.name.name
                )

                if info is not None:
                    self._define_symbol_if_missing(
                        declaration.name.name,
                        info.type,
                    )

            elif isinstance(
                declaration,
                FunctionDeclaration,
            ):
                function_type = self._function_type(
                    declaration
                )

                self._define_symbol_if_missing(
                    declaration.name.name,
                    function_type,
                )

    def _define_symbol_if_missing(
        self,
        name: str,
        symbol_type: Type,
    ) -> None:
        if self._environment.contains_local(name):
            return

        self._environment.define(
            name,
            symbol_type,
        )

    def _complete_class_type(
        self,
        declaration: ClassDeclaration,
    ) -> Type:
        class_type = self._type_infos[
            declaration.name.name
        ].type

        extends = None

        if declaration.extends is not None:
            extends = self.resolve_type(
                declaration.extends
            )

            if extends.kind is not TypeKind.CLASS:
                raise self._error_at(
                    declaration.extends.position,
                    "A class can only extend another class.",
                    InvalidTypeOperationError,
                )

        interfaces: list[Type] = []

        for interface_reference in declaration.implements:
            interface_type = self.resolve_type(
                interface_reference
            )

            if interface_type.kind is not TypeKind.INTERFACE:
                raise self._error_at(
                    interface_reference.position,
                    "A class can only implement interfaces.",
                    InvalidTypeOperationError,
                )

            interfaces.append(interface_type)

        members = self._collect_class_members(
            declaration
        )

        self._type_infos[
            declaration.name.name
        ] = TypeInfo(
            type=class_type,
            members=members,
            extends=extends,
            interfaces=tuple(interfaces),
        )

        return class_type

    def _complete_interface_type(
        self,
        declaration: InterfaceDeclaration,
    ) -> Type:
        interface_type = self._type_infos[
            declaration.name.name
        ].type

        extends = None

        if declaration.extends is not None:
            extends = self.resolve_type(
                declaration.extends
            )

            if extends.kind is not TypeKind.INTERFACE:
                raise self._error_at(
                    declaration.extends.position,
                    "An interface can only extend another interface.",
                    InvalidTypeOperationError,
                )

        members: list[MemberInfo] = []

        for member in declaration.members:
            if isinstance(member, FunctionDeclaration):
                members.append(
                    MemberInfo(
                        name=member.name.name,
                        type=self._function_type(member),
                    )
                )

        self._type_infos[
            declaration.name.name
        ] = TypeInfo(
            type=interface_type,
            members=tuple(members),
            extends=extends,
        )

        return interface_type

    def _complete_struct_type(
        self,
        declaration: StructDeclaration,
    ) -> Type:
        struct_type = self._type_infos[
            declaration.name.name
        ].type

        members = self._collect_field_members(
            declaration.fields
        )

        self._type_infos[
            declaration.name.name
        ] = TypeInfo(
            type=struct_type,
            members=members,
        )

        return struct_type

    def _complete_record_type(
        self,
        declaration: RecordDeclaration,
    ) -> Type:
        record_type = self._type_infos[
            declaration.name.name
        ].type

        members = self._collect_field_members(
            declaration.fields
        )

        self._type_infos[
            declaration.name.name
        ] = TypeInfo(
            type=record_type,
            members=members,
        )

        return record_type

    def _collect_class_members(
        self,
        declaration: ClassDeclaration,
    ) -> tuple[MemberInfo, ...]:
        members: list[MemberInfo] = []

        for member in declaration.members:
            if isinstance(member, FieldDeclaration):
                members.append(
                    MemberInfo(
                        name=member.name.name,
                        type=self._field_type(member),
                    )
                )

            elif isinstance(member, FunctionDeclaration):
                members.append(
                    MemberInfo(
                        name=member.name.name,
                        type=self._function_type(member),
                    )
                )

        return tuple(members)

    def _collect_field_members(
        self,
        fields: tuple[FieldDeclaration, ...],
    ) -> tuple[MemberInfo, ...]:
        members: list[MemberInfo] = []

        for field in fields:
            members.append(
                MemberInfo(
                    name=field.name.name,
                    type=self._field_type(field),
                )
            )

        return tuple(members)

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

        raise self._error_at(
            field.position,
            (
                f"Field '{field.name.name}' requires "
                "a type annotation or initializer."
            ),
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

        return error_type(
            message + location
        )


def check_compilation_unit(
    compilation_unit: CompilationUnit,
) -> None:
    """Check a compilation unit using a fresh TypeChecker."""
    TypeChecker().check(
        compilation_unit
    )


__all__ = [
    "TypeChecker",
    "check_compilation_unit",
    "TypeCheckError",
    "UnknownTypeError",
    "InvalidTypeOperationError",
    "InvalidAssignmentError",
    "InvalidCallError",
    "InvalidReturnError",
    "InvalidMemberAccessError",
    "InvalidIndexError",
    "MemberInfo",
    "TypeInfo",
]
