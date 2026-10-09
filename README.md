Kupln

Kupln (كوبلن) is a general-purpose, native-first programming language and developer platform designed to make application development simple, powerful, safe, and scalable.

Kupln is not an Android framework, WebView wrapper, scripting layer, or frontend-only technology.

It is intended to become a complete programming language ecosystem with its own compiler, runtime, SDKs, standard library, package manager, registry, development tools, and native platform backends.

---

1. Vision

Kupln is being designed as a complete programming language and toolchain rather than as a thin layer over another programming language.

The long-term goal is:

Kupln Source Code
        ↓
Kupln Toolchain
        ↓
Kupln Runtime / Platform Integration
        ↓
Native Platform Capabilities
        ↓
Application

A developer should be able to write an application using Kupln without needing to understand the internal implementation of every target platform.

For example, application code may express operations such as:

open camera
access contacts
send a network request
open an application
store data
play audio
display a UI

Kupln tools are responsible for translating these high-level language and platform abstractions into the appropriate native operations supported by the target platform.

The developer should work with Kupln APIs and abstractions rather than being forced to manually implement platform-specific internals for every operation.

---

2. Core Principle

Kupln follows one fundamental rule:

«Build the language and its foundations first, build the tools that execute and develop the language second, and only then build the application ecosystem on top of those tools.»

The project therefore does not begin by building sample applications, Android applications, Web applications, or other end-user products.

The first objective is to create Kupln itself and the complete foundation required to use it.

---

3. What the Kupln Project Produces

The Kupln repository is primarily responsible for producing the Kupln language ecosystem and its developer tools.

The project is expected to contain and eventually produce:

- Kupln compiler
- Kupln runtime
- Kupln standard library
- Kupln SDK
- Kupln command-line tools
- Kupln package manager
- Kupln package format
- Kupln Registry integration
- Kupln Language Server Protocol implementation
- formatter
- linter
- debugger
- testing tools
- build tools
- diagnostics system
- platform SDKs
- native platform bridges
- interoperability and FFI tooling
- development and validation tools
- Project Guard
- bootstrap toolchain
- eventually, a self-hosted Kupln toolchain

The repository itself is not an application repository.

---

4. Kupln Toolchain

The Kupln Toolchain is the collection of tools required to develop, validate, build, run, test, debug, package, and distribute Kupln software.

The conceptual architecture is:

                    Kupln
                      │
              ┌───────┴────────┐
              ↓                ↓
          Language          Toolchain
                              │
        ┌─────────┬───────────┼───────────┐
        ↓         ↓           ↓           ↓
     Compiler   Runtime      SDKs       Tools
        │         │           │           │
        └─────────┴───────────┴───────────┘
                          ↓
                    Platform Backends
                          ↓
                 Native Platform APIs

The Toolchain must remain modular.

No single external technology is allowed to become the identity or architectural foundation of Kupln.

External technologies may be used internally during bootstrap or backend implementation when technically appropriate, but Kupln's language model, specifications, package model, and developer experience remain controlled by Kupln.

---

5. Compiler

The Kupln compiler is responsible for transforming Kupln source code into executable target representations.

The intended compiler pipeline is:

.kpl Source
    ↓
Lexer
    ↓
Parser
    ↓
AST
    ↓
Semantic Analysis
    ↓
Type Checking
    ↓
HIR
    ↓
Kupln IR
    ↓
Optimization
    ↓
Platform Backend
    ↓
Target Output

The Kupln Intermediate Representation must remain independent of any specific operating system or device platform.

This allows the same language core to support multiple targets.

---

6. Runtime

The Kupln Runtime provides the execution foundations required by compiled Kupln programs.

It will eventually cover areas such as:

- memory management
- ownership and references
- task execution
- asynchronous operations
- concurrency
- error propagation
- strings
- collections
- runtime metadata
- platform integration
- resource management

The runtime must be designed for safety and performance.

It must not make Kupln dependent on a single external runtime such as the JVM or .NET runtime.

---

7. SDK

The Kupln SDK is the official development interface through which Kupln programs interact with capabilities provided by supported platforms and services.

The SDK architecture must separate:

Kupln API
    ↓
Kupln Platform Abstraction
    ↓
Target Backend
    ↓
Native Platform API

Examples of possible capabilities include:

- camera
- microphone
- notifications
- filesystem
- networking
- contacts
- Bluetooth
- location
- sensors
- graphics
- audio
- application lifecycle
- storage
- permissions
- accessibility

The exact implementation is platform-specific, but the public Kupln programming model should remain consistent whenever the underlying capability can reasonably be abstracted.

---

8. Platform Independence

The Kupln language core must not be designed around Android.

Android is the first major native application target, but it is only one backend.

The long-term architecture includes independent support for:

- Android
- iOS
- Windows
- Linux
- macOS
- Web/WASM
- additional targets as the platform evolves

The architecture must therefore avoid embedding platform-specific assumptions inside the language core.

---

9. Native Development

Kupln is native-first.

The project does not use WebView or PWA technology as a substitute for native application development.

When Kupln supports a native platform, the target backend should integrate with the platform's actual native capabilities.

For Android, the goal is real native Android application development.

For iOS, the goal is real native iOS application development.

For desktop systems, the goal is native or platform-appropriate compiled applications.

For Web, WebAssembly and appropriate web technologies may be used as an independent backend.

---

10. Programming Language

Kupln is a general-purpose programming language.

Its design combines:

- procedural programming
- object-oriented programming
- functional programming

Core language characteristics include:

- static typing
- type inference
- explicit type annotations
- generics
- Unicode identifiers
- immutable and mutable bindings
- classes
- structs
- records
- interfaces
- functions
- lambdas
- higher-order functions
- ownership and memory safety
- exception handling
- Result
- Option
- asynchronous programming
- structured concurrency

The language syntax and semantics will be formally specified before production compiler implementation expands significantly.

---

11. Memory Safety

Kupln is designed to be memory-safe by default.

The memory model will use ownership and borrowing principles together with automatic resource management.

The architecture is intended to prevent classes of problems such as:

- use-after-free
- double-free
- invalid references
- unsafe shared mutable state
- data races where they can be prevented statically

Low-level control remains an architectural goal, but unsafe operations must be explicit and controlled.

---

12. Concurrency and Async

Concurrency is a first-class part of Kupln.

The architecture includes:

- async
- await
- tasks
- structured concurrency
- cancellation
- task hierarchies
- channels
- synchronization
- safe shared state
- error propagation

Concurrency rules must be designed together with the memory and ownership system.

They must not be added later as an unrelated library feature.

---

13. Interoperability

Kupln includes a general Interoperability / FFI architecture.

Potential interoperability targets include:

- C
- C++
- Rust
- Java
- Kotlin
- Swift
- Objective-C
- native ABIs
- platform-specific APIs

These are interoperability targets, not dependencies that define the Kupln language.

The FFI architecture must preserve safety boundaries and clearly distinguish safe Kupln code from externally controlled or unsafe interfaces.

---

14. Package Management

Kupln will have an official package manager.

A Kupln project will eventually use project metadata similar in concept to:

kupln.toml

and dependency locking through:

kupln.lock

The package system must support:

- dependencies
- versions
- transitive dependencies
- deterministic resolution
- lock files
- checksums
- integrity verification
- package metadata
- platform requirements
- optional dependencies
- development dependencies
- compatibility rules

---

15. Kupln Registry

Kupln will have an official Registry architecture independent of GitHub.

The Registry is responsible for package metadata, versions, dependencies, integrity information, and distribution coordination.

GitHub may be used as an initial storage backend, but GitHub is not the architectural identity of the Kupln Registry.

The architecture must allow future storage backends without breaking the package manager or existing projects.

The future Kupln package website will act as a frontend over the Registry rather than forcing users to navigate to the underlying storage provider.

---

16. Developer Tools

Kupln will provide official developer tools, including:

kupln
├── build
├── run
├── test
├── package
├── publish
├── format
├── lint
├── debug
└── other development commands

The exact CLI interface will be formally defined during toolchain development.

Kupln does not require a dedicated IDE.

Any capable editor or development environment should be able to work with Kupln source files.

LSP support will provide advanced editor integration.

---

17. Project Guard

Project Guard is a fundamental part of the Kupln development architecture.

It is not merely a build script.

Project Guard is the project's continuous validation and protection system.

Its purpose is to detect architectural and implementation problems as early as possible.

The validation model is:

Change
  ↓
Project Guard
  ↓
Structure
  ↓
Syntax
  ↓
Semantics
  ↓
Types
  ↓
Dependencies
  ↓
Architecture
  ↓
Tests
  ↓
Build
  ↓
Security / Integrity
  ↓
PASS / FAIL

The Guard will evolve together with Kupln.

Early stages will validate repository structure, documentation, configuration, and bootstrap tooling.

As the compiler becomes available, the Guard will validate actual Kupln source code.

As additional subsystems become available, the Guard will validate:

- compiler behavior
- runtime behavior
- package integrity
- dependency resolution
- ABI compatibility
- platform backends
- reproducible builds
- security requirements
- regression tests

A known detectable problem must be fixed before the project continues to grow on top of it.

---

18. Build Philosophy

Kupln development follows:

Inspect
  ↓
Implement
  ↓
Validate
  ↓
Build
  ↓
Test
  ↓
Fix root cause
  ↓
Validate again
  ↓
Continue

The project must not accumulate known structural problems.

Temporary patches are not considered architectural solutions.

If a problem originates in an earlier design decision, the root design must be corrected rather than repeatedly patching downstream files.

---

19. Bootstrap and Self-Hosting

Kupln will initially require an existing implementation language or toolchain to bootstrap its first compiler and tools.

This is a temporary bootstrap dependency, not a permanent architectural dependency.

The long-term progression is:

Existing Language
        ↓
Bootstrap Kupln Compiler
        ↓
Kupln Compiler understands Kupln
        ↓
Kupln builds more Kupln tooling
        ↓
Kupln Toolchain becomes increasingly self-hosted
        ↓
Kupln Self-Hosting

The final architecture should minimize dependence on the original bootstrap language.

---

20. Documentation

Documentation is part of the engineering system, not an afterthought.

Major architectural specifications will be maintained separately and cross-referenced.

Expected documentation areas include:

docs/
├── constitution/
├── language/
├── type-system/
├── memory/
├── concurrency/
├── modules/
├── packages/
├── abi/
├── compiler/
├── runtime/
├── sdk/
├── security/
└── testing/

Documentation must describe actual implemented behavior.

The project must not claim that a feature exists when it is only planned.

---

21. Compatibility

Kupln will distinguish between:

- source compatibility
- language compatibility
- compiler compatibility
- standard-library compatibility
- package compatibility
- binary compatibility
- ABI compatibility
- runtime compatibility

Versioning and migration rules will be designed before the ecosystem becomes large.

Breaking changes must be explicit, controlled, documented, and accompanied by migration strategies where practical.

---

22. Security

Security is part of the architecture from the beginning.

Important areas include:

- memory safety
- package integrity
- checksums
- signatures
- dependency security
- FFI boundaries
- runtime capabilities
- permissions
- build integrity
- reproducible builds

Kupln must not rely on users discovering security problems only after deployment.

---

23. Monetization Philosophy

Kupln is designed around a free core.

An ordinary developer should be able to:

- obtain Kupln
- write Kupln code
- build projects
- test projects
- run projects
- use the core toolchain
- use public packages
- complete an application

without being forced to pay.

Paid services are intended to provide additional value rather than artificially disabling the core language.

Potential future revenue sources include:

- faster cloud builds
- additional build resources
- parallel cloud builds
- private registries
- enterprise package management
- enterprise security
- cloud services
- hosting services
- CI/CD services
- marketplace services
- professional support
- training
- certification
- enterprise services

The monetization architecture must be designed so that paid services can be introduced without breaking the free core or forcing developers to pay simply to improve or use the language.

---

24. Future Kupln Platform

The long-term vision may expand beyond the language and toolchain into a broader Kupln platform.

Possible future components include:

- Kupln Studio
- advanced development environments
- cloud services
- package marketplace
- enterprise platform
- additional platform SDKs
- additional native targets
- specialized development environments
- potentially a future Kupln operating environment

These are future possibilities.

They must not distort the architecture of the initial language and toolchain.

---

25. Current Scope

The current project is focused on establishing the Kupln language and its complete tooling foundation.

The initial order is:

1. Documentation / Architecture
2. Project Guard
3. Bootstrap infrastructure
4. Language foundations
5. Compiler
6. Runtime
7. Standard Library
8. SDK
9. Developer Tools
10. Package Manager
11. Registry integration
12. Platform backends
13. Native application support
14. Progressive self-hosting

The exact implementation order may be refined by Project Guard and architectural dependencies.

---

26. What This Repository Does Not Claim Yet

At the beginning of development, the following must not be falsely represented as completed:

- production Kupln compiler
- production runtime
- self-hosting
- Android backend
- iOS backend
- Web backend
- desktop backends
- production SDKs
- public package registry
- production cloud services
- dedicated IDE
- Kupln operating system

Features are considered complete only when their implementation and validation requirements have actually been satisfied.

---

27. Development Rule

Every new component must answer four questions:

1. Why does this component exist?
2. Which architectural specification defines it?
3. Which existing components depend on it?
4. How will Project Guard validate it?

If a component cannot answer these questions, it should not be added merely to make the repository appear more complete.

---
28. Project Status

Current Stage: Foundation and Bootstrap Development

Kupln is progressing through its foundational implementation in controlled, validated stages. The project is building its language infrastructure before expanding into the complete compiler toolchain and platform ecosystem.

Completed and Validated Components

The repository currently includes:

- Project Guard: Repository validation integrated into GitHub Actions.
- Bootstrap infrastructure: Initial source-loading and host-side foundations.
- Lexer: Initial lexical analysis implementation and tests.
- Parser and AST: Initial parsing infrastructure and abstract syntax tree.
- Type System — Phase 6: Initial type-system implementation, including type definitions, environments, declaration checking, expression checking, and the main type checker.

Latest Validation Status

- GitHub Actions validation completed successfully.
- The Bootstrap test suite passed 52 tests in the latest confirmed successful run.
- The identified type-operation conflicts were corrected and the mixed-numeric addition rejection is covered by a test.

These results validate the current implementation and tests; they do not imply that the complete Kupln compiler or production toolchain is finished.

Phase Status

- Phase 6 — Type System: CLOSED.
- Phase 7: NEXT. Its implementation scope and acceptance criteria must be established before work begins.

Remaining Work

The project still needs to implement and validate the subsequent compiler and language components, followed by the runtime, standard library, SDK, developer tools, package management, Registry integration, native platform backends, and progressive self-hosting.

These components remain planned work unless their implementation and validation are confirmed in the repository.

The project continues to follow its core development cycle:

Inspect → Implement → Validate → Test → Fix verified issues → Validate again.

Only actual repository state and test results should be used to update this status. Planned features must not be described as completed.

---

29. Guiding Principle

Kupln is intended to grow from a language into a complete developer platform.

The project therefore prioritizes:

Correct architecture
        ↓
Safety
        ↓
Simplicity
        ↓
Performance
        ↓
Portability
        ↓
Developer freedom
        ↓
Long-term scalability

The objective is not to create a quick prototype that works temporarily.

The objective is to build a foundation that can continue growing without requiring repeated architectural rewrites.

---

Project: Kupln
Arabic name: كوبلن
Language extension: ".kpl"
Status: Foundation / Initial Development
