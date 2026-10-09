# Phase 7 — Semantic Analysis

## 1. Phase Overview

Phase 7 introduces semantic analysis into the Kupln bootstrap compiler.

The purpose of this phase is to validate semantic rules that cannot be
fully enforced by lexical analysis or syntax parsing alone.

Semantic analysis operates after parsing and before later compilation
stages that depend on validated program structure.

This phase builds on the existing lexer, parser, type-related
infrastructure, and compilation pipeline.

## 2. Objectives

The objectives of Phase 7 are:

- Integrate semantic analysis into the compiler pipeline.
- Detect duplicate type declarations within the applicable scope.
- Validate supported type declaration structures.
- Report semantic errors through a consistent error mechanism.
- Preserve the separation between parsing and semantic validation.
- Provide regression tests for semantic rules.
- Verify that semantic failures propagate through the full pipeline.
- Establish a foundation for future compiler phases.

## 3. Scope

This phase focuses on semantic analysis supported by the current
Kupln bootstrap implementation.

The scope includes:

- Semantic analyzer implementation.
- Type declaration name validation.
- Duplicate declaration detection.
- Integration with the compilation pipeline.
- Unit tests for semantic analysis.
- Pipeline-level regression tests.
- Documentation of implemented behavior.

This phase does not claim that every future Kupln semantic rule
has already been implemented.

## 4. Compiler Pipeline Integration

Semantic analysis is integrated into the existing compilation flow.

The intended high-level sequence is:

1. Receive Kupln source code.
2. Perform lexical analysis.
3. Parse the source into the supported syntax representation.
4. Run semantic analysis.
5. Continue only when the preceding stages succeed.

Semantic errors must prevent the pipeline from treating an invalid
program as semantically valid.

The implementation uses the existing pipeline infrastructure rather
than introducing an unrelated compilation path.

## 5. Type Declaration Names

The current duplicate-name rule applies to the following declaration
categories:

- `class`
- `interface`
- `struct`
- `record`

These declaration categories share one type-name namespace within
the current applicable scope.

A declaration must not reuse a name already declared by another
type declaration in that scope.

The rule applies even when the declarations use different categories.

For example, declaring a class and an interface with the same name
must be rejected.

## 6. Exported Declarations

The duplicate-name rule also applies when a declaration uses `export`.

Exporting a declaration does not make a duplicate type name valid
within the same applicable scope.

For example, the following source must produce a semantic error:

```kupln
export class Shared {}
record Shared {}
```

The semantic analyzer must detect the conflict instead of accepting
both declarations as distinct valid type names.

## 7. Duplicate Declaration Example

The following source demonstrates a conflict between declaration
categories:

```kupln
class Shared {}
interface Shared {}
```

The declarations reuse the same type name.

The program must be rejected by semantic analysis.

This rule prevents ambiguous type declarations and provides a
consistent foundation for later compiler stages.

## 8. Scope Boundaries

The rules documented here apply to the scope supported by the current
implementation.

Separate namespaces and module-level name resolution remain future
work unless explicitly implemented and tested in a later phase.

This phase must not be interpreted as completing the entire Kupln
namespace or module system.

## 9. Error Handling

Semantic validation failures must be represented as semantic errors.

The compilation pipeline must propagate these errors to its caller.

A semantic failure must not be silently ignored or converted into
successful compilation.

Tests should verify both the detection of invalid declarations and
the behavior of the integrated pipeline.

## 10. Implementation Files

The current implementation is organized across the following files:

- `bootstrap/semantic/analyzer.py`
- `bootstrap/pipeline.py`
- `bootstrap/types/checker.py`

These files provide the semantic analyzer, its pipeline integration,
and the existing type-checking infrastructure.

The following test files cover the relevant behavior:

- `bootstrap/tests/test_semantic.py`
- `bootstrap/tests/test_pipeline.py`

The files should remain consistent with the actual implementation.
New behavior must be accompanied by appropriate regression tests.

## 11. Semantic Analysis Tests

The semantic test suite covers supported semantic validation behavior.

Relevant tests should ensure that duplicate type declarations are
rejected when they reuse a name within the same applicable scope.

The duplicate-name rule must not depend solely on whether the
declarations share the same declaration category.

Tests should also cover declarations that use `export`.

## 12. Pipeline Regression Tests

The pipeline test suite includes regression coverage for duplicate
type names.

The following cases are covered by the added tests:

- A class and an interface declared with the same name.
- An exported class and a record declared with the same name.
- Rejection through the full `analyze_source()` pipeline.

These tests help verify that semantic validation is connected to the
actual compilation path, rather than working only when the analyzer
is invoked independently.

## 13. Regression Requirements

Future changes must preserve the duplicate-name behavior described
in this document.

At minimum, regression testing should ensure that:

- Duplicate type names are rejected.
- Different type declaration categories share the applicable
  type-name namespace.
- The `export` modifier does not bypass duplicate-name validation.
- Semantic errors propagate through the compilation pipeline.
- Existing supported compiler behavior remains intact.

Any changes to these rules must be reflected in both implementation
and tests.

## 14. Dependencies

This phase uses the existing Kupln bootstrap infrastructure.

It does not require introducing a separate compiler framework merely
to perform the documented semantic checks.

Future dependencies must be justified by a concrete implementation
requirement.

## 15. Limitations

Phase 7 does not claim to complete every aspect of semantic analysis.

Advanced name resolution, separate namespace systems, module
visibility, overload resolution, and additional type rules may require
future implementation and dedicated tests.

Their availability must be determined from the actual source code,
not inferred from the existence of the semantic analyzer.

## 16. Verification Status

The duplicate-type-name regression tests were added to the pipeline
test suite.

The repository owner reported that the file was updated and that
GitHub testing succeeded afterward.

This documentation records that report without making an independent
claim about a specific workflow run.

Workflow run numbers alone must not be treated as proof that a
particular revision passed all required checks.

## 17. Acceptance Criteria

Phase 7 is considered implemented for its documented scope when:

- Semantic analysis is connected to the compilation pipeline.
- Duplicate type names are detected across the supported declaration
  categories.
- Exported declarations cannot bypass duplicate-name validation.
- Semantic failures are propagated through the pipeline.
- Relevant unit and integration regression tests are present.
- The documentation accurately describes the implementation.
- No unsupported future functionality is presented as completed.

## 18. Completion Boundary

The completion of this phase applies only to the functionality
documented above and implemented in the repository.

It does not mean that Kupln has a complete production compiler.

Further semantic capabilities may be introduced incrementally as
the language specification and compiler architecture evolve.

## 19. Next Phase

The next planned phase is:

**Phase 8 — Intermediate Representation (IR)**

Phase 8 should establish an explicit intermediate representation
that later compiler stages can consume.

Its design should be based on the actual syntax and semantic
structures available in the repository.

The next phase should not assume that semantic features outside
Phase 7's documented scope already exist.

## 20. Maintenance

Update this document whenever the Phase 7 implementation or its
acceptance criteria change.

Keep documentation, implementation, and regression tests aligned.

Do not mark unimplemented features as complete.

Do not infer workflow success from a run number alone.

---

**Phase:** 7 — Semantic Analysis  
**Project:** Kupln  
**Status:** Implementation and pipeline regression coverage are in place, according to the repository owner's report.  
**Next:** Phase 8 — Intermediate Representation (IR)
