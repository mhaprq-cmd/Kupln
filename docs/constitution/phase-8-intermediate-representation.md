
# Phase 8 — Intermediate Representation (IR)

## 1. Phase Overview

Phase 8 introduces the initial platform-independent Intermediate
Representation (IR) for the Kupln bootstrap compiler.

The IR establishes a structured boundary between validated source
analysis and future compiler stages. It is an intermediate compiler
representation, not executable output.

This document records the implemented scope and known limitations.
The presence of an implementation or passing individual tests does
not, by itself, establish completion of the entire phase.

## 2. Objectives

Phase 8 aims to:

- Define a platform-independent IR data model.
- Lower supported AST constructs into IR.
- Preserve the structure and meaning of supported constructs.
- Reject unsupported constructs explicitly.
- Integrate IR generation with the existing compilation pipeline.
- Preserve parsing, type-checking, and semantic-analysis failures.
- Verify deterministic lowering and pipeline integration.
- Document actual capabilities, limitations, and verification status.

## 3. Compiler Architecture

The intended compiler flow is:

Kupln Source (.kpl)
        |
        v
Lexer
        |
        v
Parser
        |
        v
Abstract Syntax Tree (AST)
        |
        v
Type Checking
        |
        v
Semantic Analysis
        |
        v
AST-to-IR Lowering
        |
        v
Platform-independent IR
        |
        v
Future Optimization and Backends

The final stages shown above are architectural direction only.
IR optimization, backend generation, executable output, and runtime
execution are outside the implemented scope of Phase 8.

## 4. Implementation Boundaries

The current implementation uses these files:

- `bootstrap/ir/model.py`
  Defines the IR data model.
- `bootstrap/ir/lowering.py`
  Converts supported AST constructs into IR and raises
  `IRLoweringError` when conversion is unsupported.
- `bootstrap/pipeline.py`
  Provides the source parsing, analysis, and IR compilation entry points.
- `bootstrap/tests/test_ir.py`
  Tests IR model behavior and AST-to-IR lowering.
- `bootstrap/tests/test_pipeline.py`
  Tests existing analysis behavior and integration of IR generation.
- `docs/constitution/phase-8-intermediate-representation.md`
  Documents the design, implementation boundaries, and verification status.

These files describe the current implementation boundary. They do not
imply that every possible AST construct is supported by the IR.

## 5. IR Data Model

The current IR model is defined in `bootstrap/ir/model.py`.

It contains the following immutable data structures:

- `IRSourceLocation`: source line, column, and offset.
- `IRValue`: a named value with an optional type name.
- `IRConstant`: a literal kind and its source-level value.
- `IROpcode`: the supported instruction operation identifiers.
- `IRInstruction`: an opcode, optional result, operands, and optional
  source location.
- `IRParameter`: a function parameter and optional type name.
- `IRBasicBlock`: an ordered sequence of instructions.
- `IRFunction`: a function name, parameters, optional return type,
  and ordered basic blocks.
- `IRModule`: an ordered collection of functions.

The model uses frozen dataclasses and tuples to preserve immutable,
ordered IR structures.

### 5.1 Instruction Kinds

The initial opcode inventory is:

- `CONSTANT`
- `PARAMETER`
- `DECLARE_VARIABLE`
- `STORE`
- `LOAD`
- `UNARY`
- `BINARY`
- `CALL`
- `RETURN`

These opcodes describe the initial supported representation. Their
existence does not mean that every source-language construct, execution
semantics, or backend operation has been implemented.

### 5.2 Source Locations

Lowering preserves source coordinates for supported instructions
when the corresponding AST node provides a source position.

IR source locations are diagnostic metadata. They do not constitute
a complete debugging-information or source-mapping subsystem.

## 6. AST-to-IR Lowering

The public lowering entry point is:

`lower_compilation_unit(compilation_unit)`

It accepts a parsed `CompilationUnit` and returns an `IRModule`
when all encountered constructs are supported by the initial lowerer.

The lowerer does not execute source programs.

### 6.1 Supported Top-Level Constructs

The initial lowerer supports synchronous function declarations
without function modifiers.

A module can contain multiple supported functions. Function order
is preserved in the resulting IR module.

Top-level constructs other than supported function declarations are
rejected explicitly. Export declarations are also rejected.

### 6.2 Supported Function Components

The initial function lowerer supports:

- Function parameters.
- Optional parameter type annotations.
- Optional function return type annotations.
- Variable declarations.
- Return statements, with or without an expression.
- Expression statements.
- Empty statements.

Each lowered function currently contains one basic block named
`entry`.

The initial lowerer does not construct a control-flow graph.

### 6.3 Supported Expressions

The initial lowerer supports:

- Literal expressions.
- Identifier expressions referring to supported local variables
  or parameters.
- Parenthesized expressions.
- Unary expressions.
- Binary expressions.
- Assignments to local identifiers.
- Calls to named functions declared in the compilation unit.
- Calls through supported local callable values.

Temporary values use deterministic names within each function.
The lowerer emits explicit instructions for supported operations.

The current representation preserves literal values as strings,
matching the lexical-value representation in the AST.

### 6.4 Unsupported Constructs

The initial lowerer explicitly rejects unsupported constructs,
including:

- Asynchronous functions.
- Function modifiers.
- Export declarations.
- Classes, interfaces, structs, records, imports, and other
  unsupported top-level items.
- Conditional statements and loops.
- Try/catch statements.
- Nested blocks not handled by the current function-body lowering.
- Unsupported expressions, including member access, indexing,
  object construction, array expressions, conditional expressions,
  and postfix expressions.
- Assignments whose target is not a supported local identifier.
- Identifiers or call targets outside the supported scope.

This list describes the current initial lowering boundary, not a
permanent restriction on the Kupln language.

Unsupported input must fail rather than be silently omitted.

## 7. Platform Independence

The IR data model does not encode a particular operating system,
processor architecture, device ABI, or application packaging format.

No Android-, iOS-, desktop-, or web-specific backend is implemented
as part of this phase.

Future backends must define their own target-specific responsibilities
without making target details prerequisites for constructing the
platform-independent IR.

## 8. Analysis and Validation Boundary

The pipeline entry point for producing IR is:

`compile_to_ir(source: str) -> IRModule`

The current pipeline performs these steps in order:

1. Tokenize and parse the source.
2. Run the existing type checker.
3. Run the existing semantic analyzer.
4. Lower the analyzed AST into IR.

The existing public functions remain available:

- `parse_source(source)`
- `analyze_compilation_unit(compilation_unit)`
- `analyze_source(source)`
- `compile_to_ir(source)`

Parsing, type-checking, and semantic-analysis errors are propagated
to the caller. Lowering errors are also propagated.

Successful parsing or analysis alone does not guarantee that the
program belongs to the supported IR subset. A program may pass the
existing analysis stages and still be rejected during lowering.

The existing analysis infrastructure remains responsible for the
rules it currently implements. Phase 8 does not claim complete
type safety or complete semantic validation for every language feature.

## 9. Error Handling

`IRLoweringError` represents failures encountered when the lowerer
cannot represent a construct within the supported IR subset.

The error includes a descriptive message and the source position
where the unsupported construct was encountered.

The pipeline does not convert lowering failures into successful
IR results.

Existing parser, type-checker, and semantic-analysis exceptions
remain distinct and are not intentionally swallowed by IR generation.

The lowerer is designed to reject unsupported constructs explicitly.
It is not yet a complete IR verifier and does not establish every
possible IR invariant or prove semantic equivalence for all Kupln
programs.

## 10. Determinism

The initial lowering implementation uses ordered collections,
deterministic traversal, and sequential temporary-value names.

The existing IR tests include a determinism check that compares the
IR produced by repeated lowering of equivalent parsed source.

This establishes a focused regression check for the tested input.
It is not a formal proof of determinism for every possible AST.

## 11. Scope Limitations

The current IR is an initial compiler representation, not a complete
production IR.

Known limitations include:

- One basic block per function.
- No control-flow graph construction.
- No optimization passes.
- No machine-code or bytecode generation.
- No platform backend.
- No runtime execution.
- No executable or application packaging.
- No complete symbol-resolution or callable-type system in the IR.
- No comprehensive IR verification pass.
- No guarantee of complete lowering coverage for the Kupln AST.
- No claim of complete source-language semantic preservation beyond
  the constructs currently represented and tested.

The current lowerer also has limited scope handling. It tracks
parameters and local variables in a function-level name table rather
than implementing a complete lexical-scope model.

Future work must address control flow, scope rules, value typing,
and IR validation before the representation can support broader
compiler guarantees.

## 12. Testing Requirements

The following test files cover the initial implementation:

### 12.1 IR Unit Tests

`bootstrap/tests/test_ir.py`

The existing tests cover:

- IR source-location fields.
- IR value and constant fields.
- Instruction structure and operands.
- Ordered function, block, and module structure.
- Immutability of IR model objects.
- Lowering a supported function with a binary return expression.
- Deterministic lowering for a supported example.
- Explicit rejection of unsupported top-level constructs.
- Explicit rejection of unsupported control flow.

### 12.2 Pipeline Integration Tests

`bootstrap/tests/test_pipeline.py`

The existing tests cover analysis behavior, including syntax errors,
type-checking errors, inheritance cycles, and duplicate type names.

The IR integration tests additionally cover:

- Successful IR generation for a supported function.
- Propagation of syntax errors.
- Rejection of unknown types by the existing type checker.
- Rejection of duplicate type names by semantic analysis.
- Propagation of lowering errors for unsupported constructs.

These tests cover representative paths. They do not establish complete
coverage of every AST node or every invalid program.

## 13. Regression and Project Guard

Phase 8 must preserve the existing test and workflow protections.

No GitHub Actions workflow should be weakened, bypassed, or modified
merely to make the IR implementation pass.

The complete repository test suite and the existing Project Guard
must pass before Phase 8 is declared complete.

A successful workflow run validates only the checks actually executed
for that revision. It must not be interpreted as proof of features
that the tests do not exercise.

## 14. Out of Scope

Phase 8 does not implement:

- IR optimization.
- Native code generation.
- Machine-code generation.
- Platform backends.
- Runtime execution.
- Executable or application packaging.
- Production ABI support.
- A complete memory-management subsystem.
- New ownership or borrowing analysis.
- Kupln self-hosting.
- A complete production compiler.
- A separate HIR subsystem without an approved architectural need.

These capabilities must be scoped, implemented, and verified in
their appropriate future work.

## 15. HIR and IR Boundary

The long-term architecture may distinguish between High-Level
Intermediate Representation (HIR) and a lower-level Kupln IR.

Phase 8 establishes only the initial IR representation defined in
this document.

A second intermediate representation must not be introduced merely
to create additional layers. If future requirements justify HIR and
a lower-level IR, their responsibilities and conversion boundaries
must be specified before implementation.

## 16. Dependency and Security Requirements

The IR implementation must continue to:

- Avoid executing source programs during lowering.
- Avoid implicit network access or external package resolution.
- Avoid modifying source files during IR generation.
- Avoid unexpected repository-state changes.
- Avoid bypassing existing validation or Project Guard.
- Avoid hiding parser, type-checker, semantic-analysis, or lowering
  failures.
- Prefer existing project infrastructure and standard-library tools.

Any future dependency must have a concrete technical justification.

## 17. Acceptance Criteria

Phase 8 may be declared complete for its approved initial scope only
when the following criteria have been verified:

- The IR model is explicit, immutable where designed, and documented.
- Supported AST constructs lower into the documented IR structures.
- Unsupported constructs fail explicitly.
- Repeated lowering of equivalent supported input is deterministic
  for the tested cases.
- The IR remains platform-independent.
- IR generation is integrated with the existing pipeline.
- Existing type-checking and semantic-analysis stages run before
  lowering.
- Parsing, type-checking, semantic-analysis, and lowering errors
  propagate to the caller.
- Duplicate type declarations remain rejected.
- IR unit tests and pipeline integration tests pass.
- The complete existing test suite passes.
- Project Guard passes without weakened protections.
- Documentation matches the actual code and test results.
- Remaining limitations are clearly documented.

Completion must be based on implementation and verification results,
not merely on the presence of files or on a single successful test.


## 18. Verification Status

**Status: Verified — completed for the approved initial scope.**

The IR model, AST-to-IR lowerer, pipeline entry point, unit tests,
pipeline integration tests, and documentation are present.

GitHub Actions Project Guard run 116 completed successfully for the
documentation revision. Both the `Run Project Guard` and
`Run Bootstrap tests` steps passed.

The workflow runs:

- `python tools/project-guard/guard.py`
- `python -m unittest discover -s bootstrap/tests -p "test_*.py"`

This verifies the checks executed by that workflow for the tested
revision. It does not establish complete lowering coverage for every
AST construct, a production-ready compiler, or features outside the
approved initial scope.

The phase is accepted within the limitations documented above.
Future work must preserve the existing validation and workflow
protections.



## 19. Completion Boundary

Completing Phase 8 means that the documented initial IR capability
has been implemented and validated within its stated limitations.

It does not mean that Kupln has a complete production compiler, an
executable runtime, native application output, optimization, or
platform backends.

Future phases must build on the verified IR boundary without
silently expanding the responsibilities of this phase.

## 20. Next Phase

The next phase must be selected after the Phase 8 implementation,
tests, documentation, and acceptance criteria have been reviewed.

Potential future work may include stronger IR validation, broader
lowering coverage, control-flow representation, optimization, or
backend preparation. Such work requires explicit scope and tests.

## 21. Maintenance

Update this document when the approved scope, implementation,
supported constructs, limitations, or verification status changes.

Keep the documentation, implementation, tests, and pipeline behavior
aligned.

Do not modify GitHub workflow procedures as part of this documentation
update. Any future workflow change requires separate review and
explicit approval.

---

Project: Kupln  
Phase: 8 — Intermediate Representation (IR)  
Previous Phase: Phase 7 — Semantic Analysis  
Status: Completed — approved initial IR scope verified
Next Phase: To be determined after Phase 8 review
