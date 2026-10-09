Kupln Phase 7 — Semantic Analysis

Status

Implementation and integration are in place. Final verification of the expanded duplicate-type-name regression tests is pending.

Phase 7 must not be considered fully verified against the latest changes until the updated semantic tests and the existing bootstrap tests pass, and Project Guard succeeds without weakening existing protections.

Objective

Implement the semantic-analysis stage of the Kupln bootstrap compiler so that parsed programs can be checked for semantic correctness beyond lexical and syntactic validity.

Semantic analysis operates on the parsed Abstract Syntax Tree (AST) and provides a foundation for subsequent compiler stages.

Implementation

The principal files involved in this phase are:

- "bootstrap/semantic/analyzer.py"
- "bootstrap/tests/test_semantic.py"
- "bootstrap/pipeline.py"
- "docs/specification/types.md"

The implementation must remain consistent with the language features represented by the current AST and the semantic rules defined by the Kupln specifications.

Semantic Analyzer

The semantic analyzer checks language-level constraints that cannot be fully validated by the lexer or parser.

Its responsibilities include detecting duplicate type names within the applicable scope and reporting semantic errors with useful diagnostic information.

The analyzer must operate on the compilation unit and preserve compatibility with the existing bootstrap compiler architecture.

Shared Type-Name Namespace

The following declaration kinds share one type-name namespace within the same applicable scope:

- "class"
- "interface"
- "struct"
- "record"

A type name must be unique across all four declaration kinds within that scope.

For example, the following declarations must be rejected because they define the same type name more than once:

class Account {}
interface Account {}

The same restriction applies to duplicate declarations of the same kind:

struct Account {}
struct Account {}

It also applies across different declaration kinds, including:

record Account {}
class Account {}

Export Does Not Bypass Uniqueness

Wrapping a declaration in "export" does not create a separate type-name namespace and does not exempt the declaration from duplicate-name validation.

The semantic analyzer must reject conflicting type names regardless of whether neither, one, or both declarations are wrapped in "export".

For example, this must be rejected:

class Account {}
export interface Account {}

The same rule applies when both declarations are exported.

Scope Boundaries

The uniqueness rule applies within the same applicable scope.

Supporting independent namespaces or modules that permit identical type names in different scopes is deferred until Kupln has an implemented and specified namespace/module system.

The implementation must not assume that this future functionality already exists.

Diagnostics

When a duplicate type name is detected, the semantic analyzer must raise "SemanticAnalysisError".

The diagnostic should:

- Identify the duplicated type name.
- Identify the conflicting declaration kinds when available.
- Report the source position of the conflicting declaration.
- Remain consistent with the existing semantic-error reporting conventions.

Pipeline Integration

The existing compilation pipeline in "bootstrap/pipeline.py" connects type checking and semantic analysis through the compilation-unit analysis flow.

The relevant entry points include:

- "analyze_compilation_unit()"
- "analyze_source()"

Type checking and semantic analysis must retain distinct responsibilities while working together as part of the compilation process.

Duplicate-type-name validation must not be bypassed when the program is processed through the normal compilation pipeline.

If the existing type checker registers duplicate declarations before semantic analysis runs, its behavior must be reviewed to ensure that registration does not prevent the semantic analyzer from detecting and reporting the duplicate.

Any change to the type checker must be supported by a failing regression test demonstrating the need for that change.

Tests

Semantic-analysis tests are maintained in:

"bootstrap/tests/test_semantic.py"

The test suite must preserve existing semantic-analysis coverage and verify the shared type-name namespace rule.

At minimum, the tests must cover:

1. Duplicate "class" declarations.
2. Duplicate "interface" declarations.
3. Duplicate "struct" declarations.
4. Duplicate "record" declarations.
5. Duplicate names across different declaration kinds.
6. Duplicate names when the first declaration is exported.
7. Duplicate names when the second declaration is exported.
8. Duplicate names when both declarations are exported.
9. Error diagnostics identifying the duplicated name and conflicting declaration kinds.
10. Useful source-position information in duplicate-name diagnostics.
11. Existing inheritance, interface-contract, and other semantic-analysis behavior.
12. The normal compilation pipeline, to ensure duplicate-name errors are not bypassed.

The tests must verify the actual behavior of the implementation rather than merely checking that helper functions or internal methods exist.

Tests for duplicate names must not replace or remove unrelated existing regression tests.

Verification

The previously reported GitHub Actions workflow run was successful:

https://github.com/mhaprq-cmd/Kupln/actions/runs/37994370129

That run reported successful results for:

- Project Guard
- Bootstrap Tests

However, a successful run that predates the latest test-file changes does not verify those new changes.

After the updated test file and this document are committed, GitHub Actions must run again. The latest run must confirm that:

- Project Guard passes.
- The expanded semantic-analysis tests pass.
- Existing bootstrap tests pass.
- No unrelated protections or tests have been weakened or removed.

The final verification status must be based on the actual latest workflow result.

Scope Boundaries

Phase 7 covers semantic analysis and its integration with the existing bootstrap pipeline.

It does not claim completion of:

- Intermediate Representation (IR).
- Code generation or machine-code generation.
- Native compilation backends.
- Runtime implementation.
- Standard Library or SDK implementation.
- Compiler self-hosting.
- Optimization passes.
- A complete namespace or module system.

These capabilities remain outside the scope of Phase 7 unless separately specified and implemented.

Acceptance Criteria

Phase 7 may be considered fully verified only when all of the following conditions are satisfied:

1. The semantic analyzer exists at "bootstrap/semantic/analyzer.py".
2. Semantic-analysis tests exist at "bootstrap/tests/test_semantic.py".
3. The analyzer is integrated into the existing compilation pipeline.
4. The four supported declaration kinds share the specified type-name namespace.
5. Duplicate type names are rejected regardless of declaration kind or "export" wrapping.
6. Duplicate-name diagnostics provide useful information.
7. The normal compilation pipeline does not bypass duplicate-name validation.
8. Existing semantic-analysis behavior remains covered by regression tests.
9. All relevant bootstrap tests pass.
10. Project Guard passes without weakening existing protections.
11. The latest GitHub Actions run succeeds after the final changes.
12. This document accurately reflects the implementation, tests, and verification available in the repository.

Maintenance Rule

Whenever the implementation, tests, or CI status changes, update this document to reflect the actual repository state.

Do not claim that a semantic rule, test case, or feature is implemented unless the source code and tests support that claim.

Do not mark the phase fully verified based only on an older successful workflow run when newer changes have not yet been tested.

Completion Summary

Phase 7 establishes the semantic-analysis stage of the Kupln bootstrap compiler and integrates it into the existing compilation pipeline.

The shared type-name namespace rule ensures that "class", "interface", "struct", and "record" declarations cannot define duplicate names within the same applicable scope. The rule remains effective when declarations are wrapped in "export".

Completion requires passing regression tests, successful integration with the normal compilation pipeline, and a successful GitHub Actions run covering the final changes.
