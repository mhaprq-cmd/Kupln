# Phase 8 — Intermediate Representation (IR)

## 1. Phase Overview

Phase 8 introduces the initial Intermediate Representation (IR)
for the Kupln bootstrap compiler.

The purpose of this phase is to establish a structured,
platform-independent representation of Kupln programs that can
be consumed by future compiler stages.

The IR must provide a clear boundary between the existing
source-analysis infrastructure and future compiler operations.

This phase builds on the lexer, parser, AST, type-checking
infrastructure, semantic analyzer, and compilation pipeline.

The implementation must reflect the actual capabilities of
the existing repository and must not assume that unsupported
language features are already implemented.

## 2. Objectives

The objectives of Phase 8 are:

- Define the purpose and architectural boundary of Kupln IR.
- Establish an initial IR data model.
- Define how supported AST structures are lowered into IR.
- Preserve the meaning of supported source constructs.
- Reject invalid or unsupported input rather than silently
  generating misleading IR.
- Keep the IR independent of operating systems, device platforms,
  and native application targets.
- Integrate IR generation with the existing bootstrap pipeline
  without breaking previous stages.
- Provide focused unit tests and pipeline-level regression tests.
- Keep the implementation small, deterministic, and extensible.
- Document the actual implementation and its limitations.

## 3. Architectural Position

The intended long-term compiler architecture is:

Kupln Source (.kpl)
        |
        v
Source Loading
        |
        v
Lexer
        |
        v
Parser
        |
        v
AST
        |
        v
Type Checking and Semantic Validation
        |
        v
Kupln Intermediate Representation (IR)
        |
        v
Future Optimization
        |
        v
Future Platform Backend
        |
        v
Target Output

This diagram describes the intended architectural direction.
It does not mean that every stage shown above is already
implemented or production-ready.

Phase 8 is responsible for introducing the initial IR boundary.

It must preserve the existing responsibilities of the lexer,
parser, type checker, semantic analyzer, and compilation pipeline.

The exact integration point must be compatible with the actual
pipeline implementation and the results of the preceding stages.

## 4. Scope

Phase 8 focuses on the initial IR model and the transformation
of supported AST structures into that representation.

The scope includes:

- IR architecture and data-model definition.
- IR instruction or node representation.
- A clear boundary between AST and IR.
- Lowering supported AST constructs into IR.
- Deterministic IR generation.
- Structured errors for unsupported or invalid input.
- Integration with the bootstrap compilation pipeline.
- Unit tests for the IR model and lowering behavior.
- Regression tests for pipeline integration.
- Documentation of supported constructs and limitations.

The initial implementation must be limited to constructs that
are represented by the existing AST and sufficiently validated
by the existing analysis infrastructure.

Future language features must not be invented merely to expand
the apparent scope of this phase.

## 5. IR Design Principles

The initial IR must follow these principles:

### 5.1 Platform Independence

The IR must not depend on:

- Android
- iOS
- Windows
- Linux
- macOS
- WebAssembly
- A specific processor architecture
- A specific native ABI
- A specific device or runtime

Target-specific details belong to future backend boundaries.

### 5.2 Explicit Structure

IR data must have an explicit and inspectable structure.

The implementation must avoid representing an entire program
as an unstructured string.

IR nodes or instructions must use stable fields and clearly
defined relationships.

### 5.3 Determinism

Given equivalent validated input and equivalent compiler
configuration, IR generation must produce equivalent IR.

Generation must not depend on:

- Network access
- Random values
- Wall-clock time
- Uncontrolled filesystem state
- Undeclared environment variables

### 5.4 Separation of Responsibilities

The IR generator must not replace the lexer, parser,
type checker, or semantic analyzer.

Each component must retain a distinct responsibility.

### 5.5 Minimal Dependencies

The implementation should prefer the host language's standard
library and existing project infrastructure.

New external dependencies require a concrete technical reason.

### 5.6 Extensibility

The initial representation must permit future additions
without requiring unrelated compiler stages to be rewritten.

Extensibility must not justify introducing speculative
instructions or unsupported language semantics.

## 6. IR Data Model

The initial IR data model must be designed from the AST structures
and language constructs that actually exist in the repository.

The implementation should establish:

- A common representation boundary for IR nodes or instructions.
- Explicit operands and values where required.
- Explicit references between related IR elements.
- A representation for supported declarations and expressions.
- Stable ordering where instruction or declaration order matters.
- A clear way to associate generated IR with its source construct
  when the existing source-position information permits it.

The design must distinguish between source syntax and the
compiler's intermediate representation.

The IR must not simply duplicate the AST without defining
a meaningful purpose for the transformation.

The phase must document which constructs are supported and
which remain unsupported.

The exact node and instruction inventory must be based on the
existing AST and must be finalized before implementation expands.

## 7. AST-to-IR Lowering

Lowering converts supported AST structures into the IR model.

The lowering implementation must:

- Accept the existing AST representation.
- Process only supported AST structures.
- Preserve the semantics of supported constructs.
- Produce deterministic IR.
- Reject unsupported constructs explicitly.
- Avoid silently dropping source constructs that affect meaning.
- Avoid executing the program during lowering.
- Avoid generating platform-specific machine instructions.

If a source construct cannot yet be represented correctly,
the lowering process must report a clear failure rather than
pretend that conversion succeeded.

The implementation must not add new language syntax merely
to make lowering easier.

## 8. Type and Semantic Validation Boundary

IR generation must operate on input that has passed the required
preceding analysis stages.

The existing type checker and semantic analyzer remain responsible
for their own validation rules.

Phase 8 must not bypass errors from those stages.

For example, duplicate type declarations such as:

```kupln
class User {}
class User {}
must continue to be rejected by the existing semantic-validation infrastructure within the applicable scope.
IR generation must not treat this invalid program as a successful, validated compilation unit.
The same principle applies to other errors detected by existing type checking or semantic analysis.
Phase 8 must not claim that all possible type or semantic errors are detected unless those rules are implemented and tested.
9. Error Handling
IR generation must provide a clear failure mechanism for problems encountered while constructing the representation.
Expected failure categories may include:
Unsupported AST construct.
Invalid or inconsistent input to the IR generator.
An IR construction invariant being violated.
A lowering operation that cannot preserve the source meaning.
Error handling must remain consistent with the repository's existing error conventions wherever practical.
Failures must not be silently ignored.
The pipeline must not report successful IR generation when the generated representation is incomplete or invalid.
The implementation should preserve source-location information when the available AST and source models make this possible.
10. Pipeline Integration
The IR stage must integrate with the existing bootstrap pipeline.
The integration must preserve the public behavior of existing source parsing and analysis functions unless an explicitly documented change is required.
The phase must establish a clear entry point for lowering an analyzed compilation unit into IR.
Pipeline integration must ensure that:
Parsing errors prevent subsequent stages from proceeding.
Type-checking failures prevent invalid input from proceeding.
Semantic-analysis failures prevent invalid input from proceeding.
Lowering failures are propagated to the caller.
Successful lowering returns the defined IR representation.
Existing parsing, type-checking, and semantic tests continue to pass.
The implementation must not introduce an unrelated parallel compilation pipeline.
11. Suggested Implementation Boundaries
The following paths are proposed for the initial implementation. They must be created only when required by the approved design.
Potential IR implementation directory:
bootstrap/ir/
Potential implementation responsibilities:
IR model and node definitions.
AST-to-IR lowering.
IR-specific validation where required.
Potential test file:
bootstrap/tests/test_ir.py
Potential pipeline regression tests:
bootstrap/tests/test_pipeline.py
The existing pipeline file is:
bootstrap/pipeline.py
These paths describe intended boundaries, not a claim that the proposed IR files already exist.
The final file layout must be checked against the actual repository before implementation.
Avoid creating empty directories or placeholder files merely to make the project structure look more complete.
12. Testing Requirements
The IR implementation must have focused tests.
Tests should verify:
Construction of valid IR elements.
Correct lowering of supported AST constructs.
Preservation of relevant source semantics.
Deterministic output for equivalent input.
Explicit rejection of unsupported constructs.
Correct handling of invalid IR construction.
Propagation of lowering errors through the pipeline.
Preservation of existing compiler-stage behavior.
Tests must use the syntax and AST structures supported by the actual repository.
They must not assume that unimplemented syntax is valid.
13. Pipeline Regression Requirements
Pipeline tests must verify the complete supported path from source analysis to IR generation.
At minimum, the tests should establish that:
Valid supported source can produce IR.
Invalid syntax does not produce successful IR.
Type-checking errors prevent successful IR generation.
Semantic errors prevent successful IR generation.
Duplicate type declarations remain rejected.
Unsupported constructs produce explicit failures.
Existing parsing and analysis tests remain compatible.
Tests must distinguish between a successful analysis result, a successful IR result, and a future executable output.
Generating IR does not mean that the source program can already be executed or compiled into a native application.
14. What Phase 8 Does Not Include
Phase 8 does not implement or claim completion of:
IR optimization.
Native code generation.
Platform backends.
Machine-code generation.
Executable or application packaging.
Runtime execution.
Memory-management implementation.
Ownership and borrowing analysis beyond existing support.
A production ABI.
A complete HIR subsystem unless separately specified and approved.
A complete production compiler.
Kupln self-hosting.
These components remain future work unless their implementation is separately defined, implemented, and validated.
15. HIR and Kupln IR Boundary
The long-term Kupln architecture may distinguish between High-Level Intermediate Representation (HIR) and a lower-level Kupln IR.
Phase 8 must not create two overlapping representations without a clear architectural need.
The initial implementation must define the purpose of the representation it introduces and document its abstraction level.
If a separate HIR and Kupln IR are required later, their responsibilities and conversion boundaries must be specified before both are implemented.
The distinction must not be determined solely by naming.
16. Optimization Boundary
Optimization is outside the implementation scope of Phase 8.
The initial IR should be structured so that future optimization can be introduced without making optimization a prerequisite for generating valid IR.
The IR generator must not silently modify program behavior under the label of optimization.
Any future optimization pass must define its own correctness requirements and regression tests.
17. Platform Backend Boundary
The IR must remain independent of specific target platforms.
Future backends may consume the IR and transform it into target-specific representations.
Phase 8 must not select a permanent target platform or encode Android-specific, operating-system-specific, or processor-specific assumptions into the language-level IR.
Backend implementation remains outside this phase.
18. Dependency and Security Requirements
The IR implementation must preserve the bootstrap project's dependency and security boundaries.
It must not:
Execute source programs during lowering.
Download or resolve external packages implicitly.
Modify source files during IR generation.
Modify repository state unexpectedly.
Bypass Project Guard.
Hide compilation errors.
Introduce unnecessary external dependencies.
IR generation must remain inspectable and testable.
19. Documentation Requirements
The implementation must be documented accurately.
Documentation must identify:
The purpose of the initial IR.
The supported IR elements.
The supported AST-to-IR conversions.
The pipeline integration point.
Error behavior.
Known limitations.
Test coverage.
Future work that remains out of scope.
The documentation must not claim that unsupported instructions, optimizations, backends, or runtime capabilities exist.
The actual implementation and tests take precedence over assumptions based on planned architecture.
20. Acceptance Criteria
Phase 8 may be considered complete for its documented scope when all of the following are satisfied:
The initial IR design is explicit and documented.
The IR model is implemented.
Supported AST constructs can be lowered correctly.
Unsupported constructs fail explicitly.
IR generation is deterministic for equivalent inputs.
The IR remains platform-independent.
The stage is integrated with the existing pipeline.
Existing type-checking and semantic validation remain active.
Duplicate type declarations remain rejected.
Unit and pipeline regression tests cover the implementation.
Existing tests continue to pass.
Project Guard passes without weakening existing protections.
The documentation reflects the actual repository state.
No future functionality is incorrectly described as complete.
Completion must be determined from the actual implementation and validation results, not from the presence of files alone.
21. Verification Status
Initial status:
Planned — Documentation and implementation have not yet been declared complete by this document.
When implementation begins, record the actual files and tests that were added or changed.
When implementation is completed, update this section with verified results.
Do not invent test counts, workflow run identifiers, or successful validation claims.
A successful workflow validates only the checks that it actually executed for the corresponding revision.
22. Completion Boundary
Completing Phase 8 means that the documented initial IR capability has been implemented and validated.
It does not mean that Kupln has a complete production compiler.
It does not imply that IR optimization, code generation, runtime execution, platform backends, or self-hosting are complete.
Future phases must build on the verified IR boundary without silently expanding its responsibilities.
23. Next Phase
The next phase must be determined from the actual state of the repository and the remaining compiler architecture.
Potential future work includes IR validation, additional lowering support, optimization, or backend preparation.
No subsequent phase should be declared complete merely because its architectural direction has been discussed.
24. Maintenance
Update this document whenever the approved Phase 8 scope, implementation, or acceptance criteria change.
Keep documentation, implementation, tests, and pipeline behavior aligned.
Do not modify existing GitHub workflow procedures as part of Phase 8 documentation.
Any future change to workflow procedures must be handled separately and explicitly approved.
Phase: 8 — Intermediate Representation (IR)
Project: Kupln
Status: Planned — Documentation baseline
Previous Phase: Phase 7 — Semantic Analysis
Next: To be determined after Phase 8 implementation and review
