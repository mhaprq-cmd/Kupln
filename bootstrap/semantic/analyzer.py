
"""Kupln Bootstrap Semantic Analyzer.

Validates semantic relationships that are not fully enforced by the
existing Type System, while preserving the separation between stages.
"""

from __future__ import annotations

from bootstrap.parser.ast import (
    ClassDeclaration,
    CompilationUnit,
    ExportDeclaration,
    FunctionDeclaration,
    InterfaceDeclaration,
    RecordDeclaration,
    StructDeclaration,
    TypeReference,
)


class SemanticAnalysisError(Exception):
    """Raised when a supported semantic rule is violated."""

    def __init__(self, message: str, position) -> None:
        self.message = message
        self.position = position
        super().__init__(
            f"{message} at line {position.line}, "
            f"column {position.column}"
        )


class SemanticAnalyzer:
    """Run semantic checks supported by the current AST and specification."""

    def analyze(self, compilation_unit: CompilationUnit) -> None:
        """Run semantic passes in a deterministic order."""
        declarations = self._collect_declarations(compilation_unit)

        self._validate_relationships(declarations)
        self._validate_inheritance_cycles(compilation_unit)
        self._validate_interface_contracts(declarations)

    @staticmethod
    def _unwrap(item):
        return (
            item.declaration
            if isinstance(item, ExportDeclaration)
            else item
        )

    def _collect_declarations(
        self,
        compilation_unit: CompilationUnit,
    ) -> dict[str, dict[str, object]]:
        """Collect top-level declarations using the existing AST model."""
        declarations: dict[str, dict[str, object]] = {
            "classes": {},
            "interfaces": {},
            "structs": {},
            "records": {},
        }

        for item in compilation_unit.items:
            declaration = self._unwrap(item)

            if isinstance(declaration, ClassDeclaration):
                declarations["classes"].setdefault(
                    declaration.name.name, declaration
                )
            elif isinstance(declaration, InterfaceDeclaration):
                declarations["interfaces"].setdefault(
                    declaration.name.name, declaration
                )
            elif isinstance(declaration, StructDeclaration):
                declarations["structs"].setdefault(
                    declaration.name.name, declaration
                )
            elif isinstance(declaration, RecordDeclaration):
                declarations["records"].setdefault(
                    declaration.name.name, declaration
                )

        return declarations

    @staticmethod
    def _simple_name(reference: TypeReference) -> str | None:
        """Return a simple type name, or None for qualified references."""
        if len(reference.parts) != 1:
            return None
        return reference.parts[0].name

    def _validate_relationships(
        self,
        declarations: dict[str, dict[str, object]],
    ) -> None:
        """Validate known class/interface inheritance relationships."""
        classes = declarations["classes"]
        interfaces = declarations["interfaces"]
        other_types = {
            **declarations["structs"],
            **declarations["records"],
        }

        for name, declaration in classes.items():
            parent = declaration.extends
            if parent is not None:
                parent_name = self._simple_name(parent)
                if parent_name is not None:
                    if parent_name in interfaces:
                        raise SemanticAnalysisError(
                            f"Class '{name}' cannot extend interface "
                            f"'{parent_name}'.",
                            parent.position,
                        )
                    if parent_name in other_types:
                        raise SemanticAnalysisError(
                            f"Class '{name}' cannot extend non-class "
                            f"type '{parent_name}'.",
                            parent.position,
                        )

            for reference in declaration.implements:
                target_name = self._simple_name(reference)
                if target_name is None:
                    continue
                if target_name in classes or target_name in other_types:
                    raise SemanticAnalysisError(
                        f"Class '{name}' can implement interfaces only; "
                        f"'{target_name}' is not an interface.",
                        reference.position,
                    )

        for name, declaration in interfaces.items():
            parent = declaration.extends
            if parent is None:
                continue

            parent_name = self._simple_name(parent)
            if parent_name is None:
                continue

            if parent_name in classes or parent_name in other_types:
                raise SemanticAnalysisError(
                    f"Interface '{name}' can extend interfaces only; "
                    f"'{parent_name}' is not an interface.",
                    parent.position,
                )

    def _validate_inheritance_cycles(
        self,
        compilation_unit: CompilationUnit,
    ) -> None:
        """Detect cycles in class inheritance and interface inheritance."""
        node_types: dict[
            tuple[str, str],
            tuple[object, TypeReference | None],
        ] = {}

        for item in compilation_unit.items:
            declaration = self._unwrap(item)

            if isinstance(declaration, ClassDeclaration):
                key = ("class", declaration.name.name)
                node_types.setdefault(
                    key, (declaration, declaration.extends)
                )
            elif isinstance(declaration, InterfaceDeclaration):
                key = ("interface", declaration.name.name)
                node_types.setdefault(
                    key, (declaration, declaration.extends)
                )

        edges: dict[
            tuple[str, str],
            tuple[tuple[str, str], TypeReference],
        ] = {}

        for key, (_, parent_reference) in node_types.items():
            if parent_reference is None:
                continue

            parent_name = self._simple_name(parent_reference)
            if parent_name is None:
                continue

            parent_key = (key[0], parent_name)
            if parent_key in node_types:
                edges[key] = (parent_key, parent_reference)

        state: dict[tuple[str, str], int] = {}
        stack: list[tuple[str, str]] = []

        def visit(node: tuple[str, str]) -> None:
            state[node] = 1
            stack.append(node)

            edge = edges.get(node)
            if edge is not None:
                parent, parent_reference = edge
                parent_state = state.get(parent, 0)

                if parent_state == 0:
                    visit(parent)
                elif parent_state == 1:
                    cycle_start = stack.index(parent)
                    cycle = stack[cycle_start:] + [parent]
                    cycle_names = [name for _, name in cycle]

                    raise SemanticAnalysisError(
                        "Inheritance cycle detected: "
                        + " -> ".join(cycle_names),
                        parent_reference.position,
                    )

            stack.pop()
            state[node] = 2

        for node in node_types:
            if state.get(node, 0) == 0:
                visit(node)

    @staticmethod
    def _function_signature(
        declaration: FunctionDeclaration,
    ) -> tuple:
        """Build a deterministic source-level function signature."""
        parameter_types = tuple(
            SemanticAnalyzer._reference_name(
                parameter.type_annotation
            )
            for parameter in declaration.parameters
        )
        return_type = SemanticAnalyzer._reference_name(
            declaration.return_type
        )
        return (
            parameter_types,
            return_type,
            declaration.async_modifier,
        )

    @staticmethod
    def _reference_name(reference: TypeReference | None) -> str:
        """Normalize a source-level type reference for signature comparison."""
        if reference is None:
            return "Void"
        return ".".join(part.name for part in reference.parts)

    def _interface_methods(
        self,
        interface_name: str,
        interfaces: dict[str, object],
        visited: set[str] | None = None,
    ) -> dict[str, FunctionDeclaration]:
        """Collect required methods, including inherited interface methods."""
        if visited is None:
            visited = set()
        if interface_name in visited:
            return {}

        visited.add(interface_name)
        declaration = interfaces.get(interface_name)
        if declaration is None:
            return {}

        methods: dict[str, FunctionDeclaration] = {}

        parent = declaration.extends
        if parent is not None:
            parent_name = self._simple_name(parent)
            if parent_name is not None:
                methods.update(
                    self._interface_methods(
                        parent_name, interfaces, visited
                    )
                )

        for member in declaration.members:
            if isinstance(member, FunctionDeclaration):
                methods[member.name.name] = member

        return methods

    def _class_methods(
        self,
        class_name: str,
        classes: dict[str, object],
        visited: set[str] | None = None,
    ) -> dict[str, FunctionDeclaration]:
        """Collect methods implemented by a class and its class ancestors."""
        if visited is None:
            visited = set()
        if class_name in visited:
            return {}

        visited.add(class_name)
        declaration = classes.get(class_name)
        if declaration is None:
            return {}

        methods: dict[str, FunctionDeclaration] = {}

        parent = declaration.extends
        if parent is not None:
            parent_name = self._simple_name(parent)
            if parent_name is not None:
                methods.update(
                    self._class_methods(parent_name, classes, visited)
                )

        for member in declaration.members:
            if isinstance(member, FunctionDeclaration):
                methods[member.name.name] = member

        return methods

    def _validate_interface_contracts(
        self,
        declarations: dict[str, dict[str, object]],
    ) -> None:
        """Require implemented interfaces' methods with matching signatures."""
        classes = declarations["classes"]
        interfaces = declarations["interfaces"]

        for class_name, declaration in classes.items():
            class_methods = self._class_methods(class_name, classes)

            for reference in declaration.implements:
                interface_name = self._simple_name(reference)
                if interface_name is None:
                    continue

                required_methods = self._interface_methods(
                    interface_name, interfaces
                )

                for method_name, required in required_methods.items():
                    implementation = class_methods.get(method_name)

                    if implementation is None:
                        raise SemanticAnalysisError(
                            f"Class '{class_name}' does not implement "
                            f"required method '{method_name}' from "
                            f"interface '{interface_name}'.",
                            declaration.position,
                        )

                    if self._function_signature(
                        implementation
                    ) != self._function_signature(required):
                        raise SemanticAnalysisError(
                            f"Method '{method_name}' in class "
                            f"'{class_name}' does not match the "
                            f"signature required by interface "
                            f"'{interface_name}'.",
                            implementation.position,
                        )


def analyze_compilation_unit(
    compilation_unit: CompilationUnit,
) -> None:
    """Analyze a compilation unit using a fresh semantic analyzer."""
    SemanticAnalyzer().analyze(compilation_unit)


__all__ = [
    "SemanticAnalysisError",
    "SemanticAnalyzer",
    "analyze_compilation_unit",
            ]
                
