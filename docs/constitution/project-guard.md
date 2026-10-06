# Kupln Project Guard Constitution

## 1. Purpose

The Kupln Project Guard is the project's structural and integrity protection system.

Its purpose is to detect problems that can be identified automatically before they become part of the project's foundation.

The Project Guard must protect:

- repository structure
- project identity
- required documentation
- required project files
- forbidden artifacts
- architectural consistency
- implementation integrity
- dependency integrity
- build integrity
- security and repository hygiene

The Guard is not the compiler and is not the Kupln language parser.

It is a project-level validation system that evolves together with the Kupln project.

---

## 2. Core Principle

The Project Guard follows this principle:

> If a detectable problem can invalidate the current project state, the project must not silently continue as if the state were valid.

A detectable violation should produce a clear failure.

The Guard must prefer:

- explicit failure over silent acceptance
- deterministic checks over assumptions
- repository evidence over claims
- small independent checks over hidden behavior
- progressive expansion over premature complexity

---

## 3. Scope

The Project Guard operates at the repository level.

It may inspect:

- files
- directories
- file names
- file extensions
- required project structures
- documentation
- configuration files
- source files
- generated artifacts
- dependencies
- build configuration
- tests
- security-related repository conditions

The Guard must not require the complete Kupln compiler or runtime to exist before it can operate.

It must work during the bootstrap stage and become stronger as the project develops.

---

## 4. Validation Levels

The Project Guard evolves through validation levels.

### Level 0 — Repository Integrity

Checks that the repository itself is structurally valid.

Examples:

- repository root exists
- required root files exist
- required directories exist
- forbidden generated artifacts are absent
- project identity is consistent

### Level 1 — Documentation Integrity

Checks that required documentation exists and does not contradict the repository state.

Examples:

- README exists
- project name is correct
- documented project scope is consistent
- incomplete features are not falsely presented as completed

### Level 2 — Project Structure

Checks that source, tooling, tests, documentation, and configuration follow the approved project structure.

### Level 3 — Language Foundation

When the Kupln language implementation exists, the Guard may validate:

- lexical components
- source file structure
- reserved words
- token definitions
- syntax-related project structures

### Level 4 — Compiler Integrity

When the compiler exists, the Guard may validate:

- compiler modules
- intermediate representation
- compilation stages
- target configuration
- backend structure
- compiler tests

### Level 5 — Runtime and Memory Integrity

When the runtime exists, the Guard may validate:

- runtime modules
- memory model components
- safety mechanisms
- concurrency components
- runtime tests

### Level 6 — Toolchain Integrity

When developer tools exist, the Guard may validate:

- CLI
- formatter
- linter
- LSP
- debugger
- test runner
- build tools
- package manager

### Level 7 — Platform Integrity

When platform support exists, the Guard may validate:

- SDK structure
- native backends
- platform adapters
- FFI boundaries
- platform-specific build configuration

### Level 8 — Self-Hosting Integrity

When Kupln becomes capable of progressively building its own toolchain, the Guard may validate:

- self-hosted components
- bootstrap stages
- reproducible builds
- bootstrap consistency
- host/toolchain independence

The levels are cumulative.

A higher level must not silently disable lower-level checks.

---

## 5. PASS and FAIL

Every Guard execution must result in one of two states:

- `PASS`
- `FAIL`

### PASS

`PASS` means that all currently enabled and applicable Guard checks succeeded.

PASS does not mean that Kupln is complete.

It only means that the repository satisfies the checks currently enforced by the Guard.

### FAIL

`FAIL` means that one or more required checks failed.

A failure must:

1. identify the failed check
2. explain the reason
3. identify the affected path or component when possible
4. return a non-zero process exit code

The Guard must never report PASS when a required check has failed.

---

## 6. Repository Structure Rules

The repository structure must remain intentional.

Required files and directories must have clearly defined purposes.

The Guard may enforce:

- required root files
- required documentation directories
- required tooling directories
- required source directories
- required test directories
- required configuration locations

A file must not be added to an arbitrary location when an approved project location exists.

Structural rules may become stricter as the project grows.

---

## 7. File Rules

The Guard may validate file-level conditions including:

- required files
- forbidden files
- forbidden extensions
- unexpected generated artifacts
- temporary files
- build outputs
- local environment artifacts
- accidental binaries
- logs
- cache files

The repository must not contain generated or temporary artifacts unless they are explicitly allowed by the project architecture.

Examples of artifacts that may be forbidden include:

- `.apk`
- `.aab`
- `.class`
- `.jar`
- `.exe`
- `.dll`
- `.so`
- `.o`
- `.obj`
- temporary files
- local logs
- local build output

The exact forbidden list is implementation-controlled and may evolve.

---

## 8. Documentation Integrity

Documentation is part of the project's integrity.

The Guard must prevent a situation where documentation claims that an incomplete system component is already implemented.

For example, documentation must not present the following as completed merely because they are planned:

- compiler
- runtime
- SDK
- package manager
- Registry
- platform backend
- self-hosting
- Kupln Cloud
- native application support

A feature may be documented as:

- planned
- designed
- in progress
- partially implemented
- implemented
- tested
- production-ready

The wording must correspond to the actual repository state.

---

## 9. Project Identity

The Guard must protect the identity of the project.

The following must remain consistent unless an intentional architectural change is approved:

- project name
- language name
- source file extension
- repository identity
- major project structure
- core terminology

Current project identity:

- Project: `Kupln`
- Language: `Kupln`
- Source extension: `.kpl`

Unexpected identity changes must be treated as potential integrity violations.

---

## 10. Dependency Integrity

As dependencies are introduced, the Guard may validate:

- declared dependencies
- dependency versions
- lock files
- transitive dependency consistency
- platform requirements
- integrity metadata
- dependency duplication
- unauthorized dependencies
- known unsafe dependency configurations

Dependencies must be explicit.

Hidden or undocumented dependencies are not acceptable.

The dependency system must remain compatible with the long-term Kupln Package Manager and Registry architecture.

---

## 11. Architecture Integrity

The Guard must evolve to detect architectural contradictions.

Examples include:

- platform-specific logic incorrectly placed inside platform-independent compiler core
- backend logic leaking into language frontend components
- runtime responsibilities mixed into unrelated compiler layers
- Registry logic incorrectly coupled to GitHub
- storage implementation treated as Registry architecture
- cloud services becoming mandatory for local development
- platform implementations bypassing official Kupln abstraction layers

The Guard should detect violations of established architectural boundaries whenever such violations can be checked automatically.

---

## 12. Implementation Truth

The repository is the primary evidence of implementation state.

The Guard must not consider a feature implemented merely because:

- it is mentioned in README
- it is mentioned in a plan
- it has a placeholder name
- a directory exists
- a configuration entry exists
- a comment says it is implemented

Implementation status should be based on verifiable repository evidence.

---

## 13. No Silent Structural Drift

Structural drift must be treated as a project integrity problem.

Examples:

- required files moved without updating architecture
- important components duplicated
- obsolete components left active
- temporary bootstrap code becoming permanent accidentally
- incompatible implementations existing simultaneously
- undocumented alternate implementations

When the Guard can detect such drift reliably, it should fail the project.

---

## 14. Progressive Enforcement

The Guard must not require future components before those components are part of the current implementation stage.

For example:

- before the compiler exists, compiler-specific validation may be inactive
- before the runtime exists, runtime-specific validation may be inactive
- before platform backends exist, backend-specific validation may be inactive
- before self-hosting exists, self-hosting validation may be inactive

However, once a component becomes an official implementation stage, its corresponding Guard checks should be introduced.

This allows the Guard to grow with the project without blocking legitimate bootstrap work.

---

## 15. Detectable Problems Must Be Stopped

A central rule of the Project Guard is:

> A problem that can be reliably detected should not be allowed to silently propagate into later stages.

This rule applies especially to:

- broken structure
- invalid configuration
- missing required files
- contradictory project identity
- forbidden artifacts
- invalid dependencies
- architecture violations
- invalid build state
- security and integrity violations

The earlier a problem can be detected, the earlier it should be rejected.

---

## 16. Build Integrity

As the build system becomes available, the Guard may validate:

- build configuration
- source discovery
- required tools
- target configuration
- reproducibility requirements
- generated output locations
- build/test separation
- build artifact hygiene

The Guard must not confuse repository validation with compilation itself.

Compilation remains the responsibility of the compiler/build system.

The Guard verifies that the conditions required for a valid project/build state are satisfied.

---

## 17. Security and Integrity

The Guard may progressively validate:

- accidental secrets
- unsafe repository configuration
- suspicious executable artifacts
- unauthorized generated files
- dependency integrity
- configuration integrity
- release integrity
- package integrity
- build integrity

Security checks must be deterministic whenever possible.

The Guard must not claim complete security merely because its checks pass.

PASS means only that the implemented security checks passed.

---

## 18. Test Integrity

As tests are introduced, the Guard may verify:

- required test directories
- required test categories
- test configuration
- test discovery
- presence of mandatory tests
- consistency between implemented components and their tests

The Guard itself must remain independently testable.

---

## 19. Guard Evolution

The Project Guard is itself part of the Kupln project.

Its architecture must therefore evolve without becoming a single unmaintainable script.

As complexity increases, the Guard may be separated into modules such as:

- repository checks
- documentation checks
- structure checks
- lexical checks
- syntax checks
- semantic checks
- type checks
- dependency checks
- compiler checks
- runtime checks
- toolchain checks
- platform checks
- security checks
- build checks

The exact module structure may evolve according to implementation needs.

---

## 20. Determinism

For the same repository state and the same Guard configuration, the Guard should produce the same result.

The Guard must avoid checks that depend unnecessarily on:

- current time
- random values
- machine-specific state
- local user configuration
- undeclared external state

External checks may be introduced later when explicitly required, but their behavior must remain controlled and reproducible.

---

## 21. Independence

The Project Guard should remain as independent as practical from the Kupln compiler during bootstrap.

The initial Guard may use a host language and standard tooling.

The long-term architecture may progressively move selected Guard capabilities into Kupln itself as part of self-hosting.

The Guard must not create a permanent architectural dependency that prevents Kupln from becoming self-hosting.

---

## 22. Failure Policy

A Guard failure is a development blocker for the affected state.

The correct response is:

1. identify the failure
2. determine its root cause
3. fix the underlying problem
4. rerun the Guard
5. continue only after PASS

The project must not intentionally bypass a Guard failure merely to continue development.

If a rule is incorrect, the rule itself must be corrected deliberately rather than bypassed silently.

---

## 23. Change Policy

Changes to the Project Guard must be treated as architectural changes when they alter:

- what constitutes a valid repository
- required files
- required directories
- project identity
- implementation-status rules
- dependency rules
- architecture boundaries
- security rules
- build rules
- release integrity

A Guard rule must not be weakened simply because an implementation currently fails it.

The preferred order is:

`Detect -> Understand -> Fix -> Verify`

not:

`Detect -> Disable -> Continue`

---

## 24. Relationship to the Kupln Development Pipeline

The Project Guard is one layer of the broader development process.

The intended progression is:

`Change`
-> `Project Guard`
-> `Repository Structure`
-> `Lexical Foundation`
-> `Syntax`
-> `Semantics`
-> `Types`
-> `Dependencies`
-> `Architecture`
-> `Tests`
-> `Build`
-> `Security / Integrity`
-> `PASS / FAIL`

Not every stage is active from the beginning.

The active stages must correspond to the current implementation state.

---

## 25. Current Bootstrap Requirement

At the current bootstrap stage, the Project Guard must remain lightweight.

The initial implementation must prioritize:

1. repository existence and root discovery
2. required documentation
3. project identity
4. forbidden artifacts
5. Guard workflow integrity
6. Guard implementation integrity

More advanced validation must be introduced only when the corresponding project components exist.

---

## 26. Long-Term Goal

The long-term goal is a Project Guard capable of validating the integrity of the complete Kupln ecosystem.

That ecosystem may eventually include:

- Kupln language
- compiler
- IR
- runtime
- memory model
- standard library
- SDKs
- native backends
- FFI
- CLI
- LSP
- formatter
- linter
- debugger
- testing tools
- build system
- package manager
- Registry
- platform integrations
- cloud integrations
- security systems
- self-hosted toolchain

The Guard must grow with the project without becoming a source of unnecessary coupling.

---

## 27. Final Principle

The Project Guard exists to protect the project from building new layers on top of a known-invalid foundation.

Its fundamental rule is:

> Do not build forward on top of a problem that can already be detected.

Every new Guard capability should make the Kupln project more structurally reliable, more reproducible, and more trustworthy without preventing legitimate progressive development.
