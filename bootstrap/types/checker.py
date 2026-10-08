"""Kupln Bootstrap Type Checker.

Coordinator for declaration and expression type checking.
"""

from __future__ import annotations

from bootstrap.parser.ast import (
    ClassDeclaration,
    CompilationUnit,
    ExportDeclaration,
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
    Type,
    TypeKind,
    named_type,
)


class TypeChecker(
    DeclarationCheckerMixin,
    ExpressionCheckerMixin,
):
    """Coordinate the Kupln Bootstrap Type System checks."""

    def __init__(
        self,
        environment: TypeEnvironment | None = None,
    ) -> None:
        self._environment = (
            environment
            if environment is not None
            else create_root_environment()
        )

        self._type_infos: dict[str, TypeInfo] = {}

        self._current_function_return_type: Type | None = None
        self._current_function_async = False

        self._register_builtin_types()

    @property
    def environment(self) -> TypeEnvironment:
        """Return the current type environment."""
        return self._environment

    @property
    def type_infos(self) -> dict[str, TypeInfo]:
        """Return registered user-defined type information."""
        return self._type_infos

    def _register_builtin_types(self) -> None:
        """Register built-in language types in the root environment."""
        for name, type_ in BUILTIN_TYPES.items():
            if not self._environment.contains_local(name):
                self._environment.define(name, type_)

    def check(
        self,
        compilation_unit: CompilationUnit,
    ) -> None:
        """Type-check a complete compilation unit."""
        self._register_declarations(compilation_unit)
        self._register_top_level_symbols(compilation_unit)

        for item in compilation_unit.items:
            self._check_top_level_item(item)

    def resolve_type(
        self,
        type_reference: TypeReference,
    ) -> Type:
        """Resolve a source-level type reference."""
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

        try:
            symbol = self._environment.resolve(name)
        except Exception:
            raise self._error_at(
                type_reference.position,
                f"Unknown type '{name}'.",
                UnknownTypeError,
            )

        type_ = symbol.type

        if type_.kind in {
            TypeKind.FUNCTION,
            TypeKind.ARRAY,
        }:
            return type_

        return type_

    def _register_declarations(
        self,
        compilation_unit: CompilationUnit,
    ) -> None:
        """Register user-defined types before checking their bodies."""
        for item in compilation_unit.items:
            declaration = self._unwrap_export(item)

            if isinstance(declaration, ClassDeclaration):
                self._register_class_type(declaration)

            elif isinstance(declaration, InterfaceDeclaration):
                self._register_interface_type(declaration)

            elif isinstance(declaration, StructDeclaration):
                self._register_struct_type(declaration)

            elif isinstance(declaration, RecordDeclaration):
                self._register_record_type(declaration)

    def _register_top_level_symbols(
        self,
        compilation_unit: CompilationUnit,
    ) -> None:
        """Register top-level functions and type names."""
        for item in compilation_unit.items:
            declaration = self._unwrap_export(item)

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


    def _unwrap_export(self, item):
        """Return the declaration wrapped by an export, if any."""
        if isinstance(item, ExportDeclaration):
            return item.declaration

        return item

    def _register_class_type(
        self,
        declaration: ClassDeclaration,
    ) -> TypeInfo:
        name = declaration.name.name

        existing = self._type_infos.get(name)
        if existing is not None:
            return existing

        class_type = named_type(
            name,
            TypeKind.CLASS,
        )

        info = TypeInfo(type=class_type)
        self._type_infos[name] = info

        return info

    def _register_interface_type(
        self,
        declaration: InterfaceDeclaration,
    ) -> TypeInfo:
        name = declaration.name.name

        existing = self._type_infos.get(name)
        if existing is not None:
            return existing

        interface_type = named_type(
            name,
            TypeKind.INTERFACE,
        )

        info = TypeInfo(type=interface_type)
        self._type_infos[name] = info

        return info

    def _register_struct_type(
        self,
        declaration: StructDeclaration,
    ) -> TypeInfo:
        name = declaration.name.name

        existing = self._type_infos.get(name)
        if existing is not None:
            return existing

        struct_type = named_type(
            name,
            TypeKind.STRUCT,
        )

        info = TypeInfo(type=struct_type)
        self._type_infos[name] = info

        return info

    def _register_record_type(
        self,
        declaration: RecordDeclaration,
    ) -> TypeInfo:
        name = declaration.name.name

        existing = self._type_infos.get(name)
        if existing is not None:
            return existing

        record_type = named_type(
            name,
            TypeKind.RECORD,
        )

        info = TypeInfo(type=record_type)
        self._type_infos[name] = info

        return info

    def _define_symbol_if_missing(
        self,
        name: str,
        type_: Type,
    ) -> None:
        if not self._environment.contains_local(name):
            self._environment.define(name, type_)

    def _complete_class_type(
        self,
        declaration: ClassDeclaration,
    ) -> Type:
        name = declaration.name.name

        info = self._type_infos.get(name)
        if info is None:
            info = self._register_class_type(declaration)

        extends = None

        if declaration.extends is not None:
            extends = self.resolve_type(
                declaration.extends
            )

        interfaces: list[Type] = []

        for interface_reference in declaration.implements:
            interfaces.append(
                self.resolve_type(interface_reference)
            )

        members = self._collect_class_members(
            declaration
        )

        completed = TypeInfo(
            type=info.type,
            members=members,
            extends=extends,
            interfaces=tuple(interfaces),
        )

        self._type_infos[name] = completed

        return completed.type

    def _complete_interface_type(
        self,
        declaration: InterfaceDeclaration,
    ) -> Type:
        name = declaration.name.name

        info = self._type_infos.get(name)
        if info is None:
            info = self._register_interface_type(
                declaration
            )

        interfaces: list[Type] = []

              if declaration.extends is not None:
            interfaces.append(
                self.resolve_type(declaration.extends)
            )

        members: list[MemberInfo] = []

        for member in declaration.members:
            if isinstance(
                member,
                FunctionDeclaration,
            ):
                members.append(
                    MemberInfo(
                        name=member.name.name,
                        type=self._function_type(member),
                    )
                )

        completed = TypeInfo(
            type=info.type,
            members=tuple(members),
            interfaces=tuple(interfaces),
        )

        self._type_infos[name] = completed

        return completed.type

    def _complete_struct_type(
        self,
        declaration: StructDeclaration,
    ) -> Type:
        name = declaration.name.name

        info = self._type_infos.get(name)
        if info is None:
            info = self._register_struct_type(
                declaration
            )

        members = tuple(
            self._collect_field_members(
                declaration.fields
            )
        )

        completed = TypeInfo(
            type=info.type,
            members=members,
        )

        self._type_infos[name] = completed

        return completed.type

    def _complete_record_type(
        self,
        declaration: RecordDeclaration,
    ) -> Type:
        name = declaration.name.name

        info = self._type_infos.get(name)
        if info is None:
            info = self._register_record_type(
                declaration
            )

        members = tuple(
            self._collect_field_members(
                declaration.fields
            )
        )

        completed = TypeInfo(
            type=info.type,
            members=members,
        )

        self._type_infos[name] = completed

        return completed.type

    def _collect_class_members(
        self,
        declaration: ClassDeclaration,
    ) -> tuple[MemberInfo, ...]:
        members: list[MemberInfo] = []

        for member in declaration.members:
            if isinstance(
                member,
                FieldDeclaration,
            ):
                members.append(
                    self._field_member(member)
                )

            elif isinstance(
                member,
                FunctionDeclaration,
            ):
                members.append(
                    MemberInfo(
                        name=member.name.name,
                        type=self._function_type(member),
                    )
                )

        return tuple(members)

    def _collect_field_members(
        self,
        fields,
    ) -> list[MemberInfo]:
        members: list[MemberInfo] = []

        for field in fields:
            members.append(
                self._field_member(field)
            )

        return members

    def _field_member(
        self,
        field: FieldDeclaration,
    ) -> MemberInfo:
        if field.type_annotation is not None:
            field_type = self.resolve_type(
                field.type_annotation
            )

        elif field.initializer is not None:
            field_type = self._check_expression(
                field.initializer
            )

        else:
            raise self._error_at(
                field.position,
                (
                    f"Field '{field.name.name}' requires "
                    "a type annotation or initializer."
                ),
                UnknownTypeError,
            )

        return MemberInfo(
            name=field.name.name,
            type=field_type,
        )


def check_compilation_unit(
    compilation_unit: CompilationUnit,
) -> None:
    """Type-check a compilation unit using a fresh checker."""
    checker = TypeChecker()
    checker.check(compilation_unit)


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
