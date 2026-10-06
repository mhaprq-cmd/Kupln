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
Only directories required by the current implementation stage should be created.
A directory must not be introduced merely to imply that a future component already exists.
9. Source File Boundary
Kupln source files use the:
.kpl
extension.
The bootstrap source-loading boundary is responsible for identifying valid Kupln source paths before later processing begins.
Source loading must remain separate from:
lexical analysis
parsing
semantic analysis
type checking
compilation
backend processing
The current source loader establishes this boundary.
10. Source Encoding
Kupln source files are loaded as UTF-8 text.
Invalid UTF-8 must be rejected by the source-loading boundary.
The bootstrap implementation must not silently replace invalid source bytes with replacement characters.
Encoding failures must remain distinguishable from:
missing files
invalid paths
unreadable files
This preserves deterministic source processing and meaningful diagnostics.
11. Source Model
Loaded source must have an explicit source representation.
The current bootstrap source model represents a loaded source file through:
normalized path
decoded source content
The source model is immutable.
The source model must remain independent from:
filesystem loading
lexical analysis
parsing
semantic analysis
compilation
backend processing
This separation allows later compiler stages to operate on stable source data.
12. Source Identity
A loaded source unit must preserve a stable identity suitable for diagnostics and later compiler stages.
The normalized source path is currently used as the source identity.
The source identity must remain independent from the host language's internal file object implementation.
Future compiler infrastructure may extend source identity with additional metadata when required.
13. Source Size and Line Information
The bootstrap source model may expose basic source measurements required by later processing.
The current implementation provides:
source name
source size in Unicode code points
source line count
An empty source has zero lines.
A non-empty source has at least one logical line.
These measurements are source-model responsibilities and must not be mixed with lexical or semantic analysis.
14. Source Loading Errors
Expected source-loading failures must use explicit bootstrap error types.
The current source loader distinguishes:
invalid source path
missing source file
unreadable source file
invalid UTF-8 encoding
These failures must not be silently converted into unrelated generic errors.
Future diagnostics infrastructure may provide richer presentation while preserving the underlying failure distinction.
15. Source Loading Determinism
Given the same valid .kpl file and the same host filesystem state, source loading must produce the same decoded source content and equivalent source representation.
The loader must not:
modify source text
perform lexical transformations
normalize language syntax
infer semantics
insert tokens
rewrite identifiers
Source loading is a boundary operation, not a compiler transformation.
16. Unicode Policy
Unicode is a fundamental part of Kupln source handling.
The bootstrap must preserve Unicode source text correctly.
This includes Unicode appearing in:
strings
characters
comments
identifiers when permitted by the Kupln specification
Unicode handling must not depend on ASCII-only assumptions.
The final lexical rules for Unicode identifiers belong to the Kupln lexical specification.
17. Source Position Model
Lexical tokens require source-location information.
The current bootstrap token model represents source positions using:
line
column
offset
Source positions must remain stable enough to support future:
diagnostics
parser errors
compiler messages
editor integration
LSP support
debugging information
The exact counting semantics for Unicode columns and offsets must be formally defined before they become externally observable compiler guarantees.
18. Token Model
The bootstrap lexer uses an immutable token representation.
A token currently contains:
token kind
original lexeme
source position
Tokens must preserve the relevant source information required by later compiler stages.
Token representation must not embed parser or semantic state.
19. Token Categories
The current bootstrap token model provides the following categories:
EOF
IDENTIFIER
KEYWORD
INTEGER
FLOAT
STRING
CHAR
OPERATOR
PUNCTUATION
COMMENT
UNKNOWN
These categories are bootstrap foundations.
Their final language-level semantics remain subject to the Kupln lexical and syntax specifications.
Additional categories may be introduced when justified by actual lexical requirements.
20. Reserved Keywords
Reserved keywords are maintained through a dedicated bootstrap boundary.
The current implementation defines:
let
var
function
return
if
else
for
while
class
interface
extends
implements
abstract
final
public
private
protected
static
struct
record
true
false
try
catch
async
await
import
export
new
this
super
null
The reserved-keyword set must remain centralized.
Individual lexer components must not independently maintain conflicting keyword lists.
21. Keyword Evolution
The bootstrap keyword list is an implementation foundation, not permission to invent future language syntax.
A keyword must be added when its language role has been sufficiently defined.
Future concepts such as:
match
do
break
continue
throw
enum
additional modifiers
additional control-flow constructs
must not be added merely because they may exist in the future.
Language evolution must follow the Kupln specification.
22. Keyword Lookup
Keyword recognition must use a stable lookup boundary.
The current implementation provides:
is_reserved_keyword(value)
and a canonical immutable reserved-keyword set.
Keyword lookup must remain deterministic.
The lookup mechanism must not depend on:
filesystem state
package installation state
network access
runtime configuration
23. Lexical Boundary
The lexer is responsible for transforming source text into lexical tokens.
The lexer must not perform responsibilities belonging to later stages.
It must not perform:
semantic analysis
type checking
code generation
backend selection
runtime execution
package resolution
The lexer may classify lexical forms according to the language specification.
24. Parser Boundary
The parser will consume lexical information and construct the syntactic representation of Kupln programs.
The parser is a future bootstrap component unless already implemented.
Parser responsibilities must remain separate from:
source loading
raw file I/O
semantic analysis
type checking
backend generation
The parser must implement the Kupln syntax specification rather than invent syntax independently.
25. Diagnostics Boundary
Diagnostics are responsible for presenting source and compilation problems to developers.
Future diagnostics infrastructure should be able to identify:
source file
source position
error category
diagnostic message
relevant source context
severity
Diagnostics must consume structured compiler information rather than forcing individual compiler components to format user-facing output independently.
26. Intermediate Representation Boundary
Future compiler stages may introduce one or more intermediate representations.
Bootstrap IR must remain independent from:
Android
iOS
Windows
Linux
macOS
Web
any single native ABI
The purpose of the IR is to provide a stable representation between language analysis and target-specific compilation.
No IR should be introduced before its responsibilities are clearly defined.
27. Compiler Boundary
The bootstrap compiler will eventually coordinate the transformation from Kupln source to target output.
The conceptual pipeline is:
.kpl Source
    ↓
Source Loading
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
HIR / Kupln IR
    ↓
Optimization
    ↓
Platform Backend
    ↓
Target Output
Only components that actually exist may be represented as implemented.
Planned compiler stages must not be represented as completed features.
28. Runtime Boundary
Bootstrap infrastructure must not accidentally become a permanent runtime.
The future Kupln Runtime is a separate architectural subsystem.
It will eventually address areas such as:
memory management
ownership
resource management
asynchronous execution
concurrency
runtime support
platform integration
Bootstrap utilities may support compiler development but must not redefine the final runtime architecture.
29. Standard Library Boundary
The Kupln Standard Library is separate from bootstrap infrastructure.
Bootstrap code must not turn host-language convenience functions into implicit Kupln standard-library guarantees.
When a capability becomes part of the official Kupln Standard Library, its API and semantics must be specified independently.
30. Platform Independence
Bootstrap infrastructure must not make the Kupln language dependent on a single target platform.
The language core must remain platform-independent.
Future backends may target:
Android
iOS
Windows
Linux
macOS
WebAssembly
additional platforms
Platform-specific implementation belongs behind backend or SDK boundaries.
31. Testing Policy
Every bootstrap component must be testable.
Tests should verify actual behavior rather than implementation appearance.
The current bootstrap test suite validates source loading behavior including:
valid .kpl loading
Unicode source content
empty sources
single-line sources
invalid extensions
missing files
directories used as paths
invalid UTF-8
As bootstrap components grow, tests must expand with them.
32. Determinism
Bootstrap behavior must be deterministic wherever the input and environment are deterministic.
Bootstrap components must avoid unnecessary dependence on:
network services
wall-clock time
random values
machine-specific configuration
undeclared environment variables
uncontrolled external dependencies
Deterministic behavior is required for reliable Project Guard and CI validation.
33. Dependency Policy
Bootstrap dependencies must remain minimal.
The preferred order is:
Python standard library or equivalent host standard facilities
already-approved project infrastructure
external dependency only when technically justified
A dependency must not be introduced merely for convenience when the required capability can be provided reliably by the host standard library.
Dependencies must not silently become Kupln language requirements.
34. Security and Integrity
Bootstrap infrastructure is part of the project's trusted development foundation.
It must therefore avoid:
executing untrusted source during loading
downloading arbitrary dependencies implicitly
modifying source files silently
modifying repository state unexpectedly
bypassing Project Guard
hiding validation failures
Future compiler execution features must define their own security boundaries.
Bootstrap tooling must remain inspectable.
35. Project Guard Integration
Bootstrap infrastructure is protected by Kupln Project Guard.
The Project Guard must validate the repository foundation before later development stages rely on it.
Bootstrap changes must remain compatible with:
repository structure rules
documentation integrity
implementation integrity
dependency integrity
test requirements
build and CI validation
security and repository hygiene
As Project Guard evolves, bootstrap validation must become stronger rather than weaker.
36. CI Integration
Bootstrap tests must be executable in the project's CI environment.
The current GitHub Actions workflow executes:
Project Guard
    ↓
Bootstrap tests
The bootstrap implementation must remain compatible with the project's supported CI environment.
CI success is evidence that the current validation suite passes.
It does not by itself prove that future bootstrap components are complete.
37. No Silent Architectural Drift
Bootstrap implementation must not silently drift away from the Kupln architecture.
A change that affects:
language syntax
keywords
source representation
token representation
compiler boundaries
runtime assumptions
dependency boundaries
platform assumptions
must be evaluated against the relevant Kupln specifications and constitutions.
If a conflict is detected, the conflict must be resolved explicitly.
38. Progressive Enforcement
Bootstrap infrastructure is intentionally built incrementally.
Early stages may validate only:
source loading
source representation
token foundations
keyword foundations
tests
repository integrity
Later stages may validate:
lexical correctness
syntax correctness
semantic correctness
type correctness
compiler correctness
runtime correctness
package integrity
backend correctness
reproducibility
The absence of a later validation layer does not mean that the corresponding feature is already implemented.
39. Migration to Self-Hosting
Bootstrap infrastructure must provide a controlled migration path toward Kupln self-hosting.
The long-term progression is:
Host Language
      ↓
Bootstrap Tooling
      ↓
Bootstrap Kupln Compiler
      ↓
Kupln Compiler Can Compile Kupln
      ↓
Kupln Implements More Tooling
      ↓
Progressive Self-Hosting
      ↓
Kupln Toolchain Built by Kupln
Migration must be incremental.
No bootstrap component should be retained permanently merely because it was the first implementation.
Conversely, a bootstrap component must not be removed before its replacement is sufficiently validated.
40. Bootstrap Exit Criteria and Final Principle
Bootstrap infrastructure is considered mature enough to transition toward self-hosting when the project has established reliable implementations of the language foundations required by the next architectural stage.
Exit criteria must be based on actual implementation and validation rather than elapsed time or repository size.
At minimum, the transition must preserve:
language specification integrity
source compatibility
lexical correctness
syntax correctness
semantic correctness
type-system correctness
compiler correctness
test coverage appropriate to the implemented stage
Project Guard validation
deterministic development workflows
architectural independence from the original host implementation
The bootstrap layer exists to make Kupln possible.
It is not the destination.
The final objective is:
Build Kupln -> Use Kupln -> Build Kupln With Kupln -> Progressively Own the Toolchain
Kupln must grow from a controlled bootstrap foundation into an independent, self-hosted programming language and toolchain without allowing temporary bootstrap decisions to become permanent architectural constraints.
