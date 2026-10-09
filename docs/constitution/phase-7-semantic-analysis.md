Kupln Phase 7 — Semantic Analysis

1. Purpose

Phase 7 establishes a dedicated semantic-analysis stage for the Kupln bootstrap toolchain.

Its purpose is to validate program meaning and language rules that cannot be established by lexical analysis, parsing, or type checking alone.

Semantic Analysis must build on the existing Lexer, Parser, AST, Type System, and Project Guard. It must not replace these components or duplicate their responsibilities unnecessarily.

The objective is to detect verified semantic errors before future compiler and intermediate-representation stages consume the program.

2. Current Position in the Pipeline

The intended processing pipeline is:

Source Code
-> Lexer
-> Parser
-> AST
-> Type System
-> Semantic Analysis
-> Future Compiler Stages

This phase implements the Semantic Analysis stage only.

It does not implement HIR, Kupln IR, optimization, native code generation, runtime execution, or platform backends.

3. Architectural Boundaries

3.1 Existing Components

The following components already exist and must be inspected before implementation:

- Source-loading and bootstrap host infrastructure
- Lexer and token definitions
- Parser and AST
- Type System and type representations
- Type environments and declaration checking
- Expression checking
- Existing diagnostics and source positions
- Bootstrap tests
- Project Guard and GitHub Actions

Existing behavior must not be rewritten merely to make the new stage appear independent.

3.2 Semantic Analysis Responsibilities

The implementation must establish a clear boundary for semantic rules not already completely enforced by the existing Type System.

Responsibilities may include, where supported by the current language specification and AST:

- Name binding and reference resolution across declarations
- Detection of unresolved names not already reported by the Type System
- Declaration-order and forward-reference rules, if defined by the language specification
- Visibility and accessibility rules, once specified
- Inheritance-cycle detection
- Validation of class/interface relationships and required interface members
- Control-flow rules that can be validated without executing the program
- Definite-initialization checks, if required by the language specification
- Consistent semantic diagnostics with source positions

These responsibilities must be implemented only to the extent supported by the existing language specification and AST.

A rule that has not been defined by the specification must not be invented during implementation. If a rule requires a language-design decision, document the decision needed instead of silently imposing new semantics.

3.3 Responsibilities That Remain Elsewhere

The Lexer remains responsible for lexical errors.

The Parser remains responsible for syntax errors and AST construction.

The Type System remains responsible for type representation, type inference, type compatibility, expression typing, and type-related diagnostics.

Semantic Analysis must not introduce a second independent type system or reimplement type checking under different names.

Compiler lowering, IR generation, optimization, code generation, runtime behavior, and native platform integration remain outside this phase.

4. Design Requirements

The Semantic Analysis implementation must be:

- Deterministic
- Platform-independent
- Testable without executing generated programs
- Integrated with the existing AST
- Consistent with the language specification
- Explicit about its inputs, outputs, and errors
- Compatible with the existing bootstrap architecture
- Small enough to validate independently
- Extensible for future compiler stages

The implementation must not depend on Android-specific behavior or native backend details.

5. Analysis Model

The stage must define an explicit entry point that accepts the existing parsed representation and any required results from the Type System.

Its design must clearly document:

1. Required inputs
2. Analysis order
3. Symbol and declaration information used
4. Semantic rules enforced
5. Diagnostic representation
6. Success and failure behavior
7. Integration with the existing pipeline

The implementation must reuse existing infrastructure where appropriate.

It must not create duplicate symbol tables, environments, or diagnostics systems without a demonstrated technical requirement.

If multiple semantic passes are necessary, each pass must have a defined responsibility and a documented dependency order.

6. Semantic Rules and Diagnostics

Each implemented rule must have a clear definition and at least one corresponding test.

Where the current AST preserves source positions, semantic errors must identify the relevant source position.

Diagnostics should identify the violated rule and the relevant declaration or reference when available.

The same invalid input must produce deterministic results.

The analyzer must not silently ignore a semantic error or convert it into an unrelated error.

The implementation must distinguish semantic errors from syntax errors and type errors without unnecessarily duplicating diagnostics already emitted by earlier stages.

7. Testing Requirements

Tests must cover the actual rules implemented in this phase.

The test suite should include applicable cases for:

- Valid programs that pass semantic analysis
- Unresolved references
- Duplicate or conflicting declarations where not already fully covered
- Forward references and declaration order, if specified
- Inheritance cycles
- Interface implementation requirements
- Relevant control-flow restrictions
- Definite initialization, if required
- Correct source-position reporting
- Deterministic diagnostics
- Regression cases for previously passing Lexer, Parser, and Type System behavior

Tests for unsupported or unspecified language features must not force arbitrary language rules into the implementation.

Existing tests must continue to pass.

8. Project Guard and CI

The phase must preserve the existing Project Guard and GitHub Actions workflow.

The implementation must be validated using the repository's existing test command:

"python -m unittest discover -s bootstrap/tests -p "test_*.py""

Any new files must follow the repository's existing structure and import conventions.

New validation rules must be added to Project Guard only when they are necessary, clearly defined, and supported by the actual repository requirements.

Unrelated workflow changes are outside the scope of this phase.

9. Implementation Constraints

Before modifying code, inspect the current repository and identify the exact existing behavior.

Do not assume that a responsibility is missing merely because it has not yet been documented in the new phase.

Do not rewrite working components without a verified defect or a demonstrated integration requirement.

Do not add external dependencies unless an essential requirement cannot reasonably be met with the existing infrastructure.

Do not implement future compiler, runtime, IR, or backend functionality as part of this phase.

Keep modifications focused on Semantic Analysis and the tests required to validate it.

10. Completion Criteria

Phase 7 may be considered complete only when:

1. The Semantic Analysis boundary and entry point are documented.
2. Implemented semantic rules match the current language specification.
3. Existing Type System responsibilities remain correctly separated.
4. Applicable semantic errors are detected deterministically.
5. Relevant diagnostics include source positions when available.
6. Tests cover valid cases, invalid cases, and regressions for the implemented rules.
7. The complete existing Bootstrap test suite passes.
8. Project Guard passes.
9. GitHub Actions completes successfully.
10. The repository documentation accurately describes what was implemented and what remains planned.

Passing tests alone must not be interpreted as proof that unspecified or unimplemented language features are complete.

11. Explicitly Out of Scope

Phase 7 does not include:

- Rewriting the Type System from Phase 6
- HIR or Kupln IR implementation
- Compiler optimization
- Native code generation
- Runtime implementation
- Standard Library implementation
- SDK implementation
- Package manager or Registry implementation
- Android, iOS, desktop, or Web backends
- Self-hosting
- Unrelated repository refactoring

These belong to later stages or separate specifications.

12. Phase Status

Phase: 7 — Semantic Analysis

Status: Planned

Previous phase: Phase 6 — Type System (Closed)

Completion status must be updated only after the implementation, tests, Project Guard, and GitHub Actions have been verified.

13. Governing Principle

Implement only the semantic responsibilities justified by the current Kupln specification and repository.

Inspect first. Reuse existing components. Fix verified gaps. Test the behavior. Validate the complete repository before closing the phase.
