# Kupln Bootstrap Infrastructure Constitution

## 1. Purpose

The Kupln Bootstrap Infrastructure defines the initial technical foundation required to begin implementing the Kupln language and its toolchain.

Bootstrap infrastructure exists to provide a controlled path from:

`Repository -> Host Tools -> Kupln Toolchain -> Kupln Self-Hosting`

The bootstrap stage must remain small, deterministic, inspectable, and replaceable.

It must not become a permanent architectural limitation on Kupln.

---

## 2. Bootstrap Principle

The bootstrap system exists to start building Kupln before Kupln can build itself.

The initial implementation may therefore use an existing host language and host platform.

The host implementation is temporary infrastructure.

It must not redefine the long-term design of the Kupln language.

The intended progression is:

`Bootstrap`
-> `Working Kupln Toolchain`
-> `Kupln Implementation`
-> `Progressive Self-Hosting`
-> `Kupln Toolchain Built by Kupln`

---

## 3. Bootstrap Goals

The bootstrap infrastructure must eventually provide the minimum capabilities required to implement and validate the first Kupln language components.

These capabilities may include:

- source file handling
- lexical processing
- token representation
- syntax processing
- diagnostics
- intermediate representations
- compiler orchestration
- testing
- command-line execution
- deterministic builds

Only capabilities required by the current implementation stage should be introduced.

---

## 4. Bootstrap Is Not the Final Architecture

Bootstrap code must not be treated as the final Kupln implementation merely because it is the first implementation.

The bootstrap layer may be replaced, rewritten, or progressively self-hosted.

The following must remain separate concepts:

- bootstrap implementation
- Kupln language specification
- Kupln compiler architecture
- Kupln runtime architecture
- Kupln standard library
- Kupln SDK
- Kupln developer tools
- Kupln self-hosting system

Bootstrap infrastructure must implement the specification.

It must not silently redefine the specification.

---

## 5. Host Language Policy

The initial bootstrap implementation may use a mature host language.

The host language should provide:

- reliable standard tooling
- file and text processing
- testing support
- deterministic execution
- Unicode support
- cross-platform availability
- maintainability
- minimal unnecessary dependencies

The initial bootstrap should prefer the host language's standard library whenever practical.

External dependencies must have a clear technical justification.

---

## 6. Host Dependency Boundary

Host-specific dependencies must remain behind clearly defined bootstrap boundaries.

The Kupln language design must not become dependent on:

- host-specific syntax
- host-specific semantics
- host-specific memory behavior
- host-specific package conventions
- host-specific APIs

A host implementation detail must not become a Kupln language rule unless explicitly approved as part of the Kupln specification.

---

## 7. Bootstrap Components

The bootstrap infrastructure may progressively contain components such as:

```text
bootstrap/
    host/
    lexer/
    parser/
    diagnostics/
    ir/
    compiler/
    tests/
