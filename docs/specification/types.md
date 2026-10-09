# Kupln Type System Specification

## 1. Purpose

This document defines the Type System of the Kupln programming language.

The Type System operates after parsing and before semantic compilation stages.

Its responsibilities are:

- represent types
- resolve declared types
- infer types where permitted
- validate type compatibility
- validate expressions
- validate function parameters and return values
- report type errors deterministically

The Type System must not generate native code, execute programs, or perform
backend-specific processing.

---

## 2. Processing Boundary

The current pipeline is:

Source
-> Lexer
-> Parser
-> AST
-> Type System
-> Semantic Analysis
-> Compiler

The Type System receives a valid AST.

Lexical errors belong to the Lexer.

Syntax errors belong to the Parser.

Type errors belong to the Type System.

Code generation errors belong to later compiler stages.

---

## 3. Type System Principles

The Type System must be:

- deterministic
- explicit
- predictable
- platform-independent
- independent from native backends
- independent from runtime execution
- compatible with the Kupln AST
- extensible for future language features

The Type System must never silently change a programmer's declared type.

---

## 4. Built-in Types

The initial Kupln Type System defines:

- `Int`
- `Float`
- `Bool`
- `String`
- `Char`
- `Null`
- `Any`
- `Void`

These names are language-level type names.

Their native representation is decided by later compiler and backend stages.

---

## 5. Integer Type

`Int` represents signed integer values.

Examples:

```kpl
let age: Int = 25;
let count = 100;
Integer literals are inferred as Int.
6. Floating Type
Float represents floating-point numeric values.
Examples:
let price: Float = 19.5;
let ratio = 0.25;
Floating-point literals are inferred as Float.
7. Boolean Type
Bool represents logical values.
Valid literals:
true
false
Boolean expressions include:
let enabled: Bool = true;
let result = age > 18;
8. String Type
String represents text values.
Example:
let name: String = "Kupln";
String literals are inferred as String.
9. Character Type
Char represents a single character.
Example:
let letter: Char = 'A';
Character literals are inferred as Char.
10. Null Type
Null represents the absence of a value.
Example:
let value = null;
Null is compatible with nullable reference-like types.
The exact nullable type syntax is reserved for a later specification revision.
The Type System must not treat null as compatible with arbitrary value types such as Int, Float, Bool, or Char.
11. Any Type
Any represents an explicitly dynamic/general value.
Example:
let value: Any = 10;
Any value may be assigned to Any.
A value of type Any may require runtime checking when used as a more specific type.
The initial implementation may restrict unsafe implicit conversions from Any.
12. Void Type
Void represents the absence of a return value.
Functions returning no value use:
function log(message: String): Void {
    ...
}
Void is not a normal value type.
13.1 Shared Type-Name Namespace

The following user-defined declaration kinds share one type-name namespace within the same applicable scope:

- "class"
- "interface"
- "struct"
- "record"

A type name must be unique across all four declaration kinds within that scope.

13.1.1 Duplicate Type Names

The compiler must reject duplicate type names even when the declarations use different declaration kinds.

For example, the following declarations are invalid:

class Account {}
interface Account {}

The same rule applies to duplicate declarations of the same kind:

struct Account {}
struct Account {}

It also applies to every other combination of the four declaration kinds.

13.1.2 Exported Declarations

The "export" modifier does not create a separate type-name namespace and does not exempt a declaration from duplicate-name validation.

The compiler must reject conflicting type names whether neither declaration, either declaration, or both declarations use "export".

For example, the following declarations are invalid:

class Account {}
export interface Account {}

Exporting both declarations does not make the duplicate valid.

13.1.3 Scope

The uniqueness rule applies within the same applicable scope.

Allowing identical type names in independent namespaces or modules is deferred until Kupln defines and implements its namespace/module system.

This rule does not establish support for namespaces or modules that are not otherwise implemented.

13.1.4 Diagnostics

When duplicate type names are detected, the compiler must report a semantic error.

The diagnostic should identify:

- The duplicated type name.
- The conflicting declaration kinds, when available.
- The source position of the conflicting declaration.

Duplicate-name validation must remain effective when compilation proceeds through the normal analysis pipeline.

13.1.5 Conformance

The implementation must include regression tests for:

- Duplicate names within each declaration kind.
- Duplicate names across different declaration kinds.
- Duplicate names with all relevant "export" combinations.
- Diagnostic messages and source positions.
- Duplicate-name detection through the normal compilation pipeline.
14. Type References
A type reference identifies a type by name.
Examples:
Int
String
User
The initial Type System supports named type references represented by the current AST.
Advanced generic type syntax is outside the current scope.
15. Type Annotation
Variables may explicitly declare their type.
Example:
let count: Int = 10;
The initializer must be compatible with the declared type.
Invalid example:
let count: Int = "hello";
This must produce a type error.
16. Type Inference
A variable without an explicit type may infer its type from its initializer.
Example:
let count = 10;
The inferred type is Int.
Examples:
let name = "Kupln";
let enabled = true;
let price = 4.5;
let letter = 'K';
Inference is performed from the expression's resulting type.
17. Missing Type and Initializer
A variable without a type annotation may omit its initializer only if a later language rule explicitly permits deferred typing.
For the initial Type System:
let value;
is a type error.
A variable must therefore have either:
an explicit type and compatible initializer, or
an initializer from which its type can be inferred.
18. Assignment Compatibility
Assignment requires the value type to be compatible with the target type.
Example:
let x: Int = 10;
x = 20;
is valid.
Example:
let x: Int = 10;
x = "text";
is invalid.
The Type System must not perform arbitrary implicit conversions.
19. Numeric Compatibility
Int and Float are distinct types.
The initial Type System must not silently convert between them unless an explicit conversion rule is later added.
Therefore:
let x: Int = 1.5;
is invalid.
And:
let x: Float = 1;
is also invalid for the initial implementation.
20. Binary Arithmetic
The operators:
+
-
*
/
%
require compatible numeric operands.
Initial valid combinations:
Int  op Int    -> Int
Float op Float -> Float
Mixed numeric operands are rejected until explicit conversion rules exist.
21. String Addition
The + operator may concatenate two String values.
Example:
let message = "Hello " + "Kupln";
Result type:
String
The initial implementation must not automatically convert arbitrary values to strings.
22. Comparison Operators
The operators:
<
>
<=
>=
produce Bool.
Operands must be type-compatible.
Example:
let result = age >= 18;
Result:
Bool
23. Equality Operators
The operators:
==
!=
produce Bool.
Operands must be comparable according to the Type System's compatibility rules.
Incompatible unrelated value types must produce a type error.
24. Logical Operators
The operators:
&&
||
require Bool operands.
Example:
let result = enabled && active;
Result:
Bool
Non-Boolean operands are invalid.
25. Logical Not
The unary operator:
!
requires a Bool operand.
Result:
Bool
Example:
let result = !enabled;
26. Unary Numeric Operators
The unary operators:
+
-
require numeric operands.
The resulting type is the operand's numeric type.
27. Increment and Decrement
The operators:
++
--
require a mutable numeric target.
They are valid for numeric variables and valid writable expressions as defined by later semantic rules.
The result type is the operand's type.
28. Assignment Expression
Assignment:
=
requires a writable target.
The assigned value must be compatible with the target type.
The resulting expression type is the target/value type according to the language's assignment semantics.
The Type System must reject assignment to non-writable expressions.
29. Conditional Expression
The expression:
condition ? whenTrue : whenFalse
requires:
condition to be Bool
both result expressions to have compatible types
Example:
let x = enabled ? 1 : 2;
The inferred type is Int.
30. Null-Coalescing
The operator:
??
requires a nullable/reference-compatible left operand.
The right operand must produce a compatible resulting type.
The resulting type is the common compatible result type.
Exact nullable syntax and advanced nullability analysis are deferred.
31. Identifier Resolution
The Type System requires access to the declared type of every referenced identifier.
For the initial implementation, a symbol/type environment may be maintained by the Type System.
Unknown identifiers must produce an error.
Example:
let x = unknownValue;
must fail type checking.
32. Scope
The Type System must respect lexical scopes created by:
compilation unit
function
block
class/interface/struct/record declarations where applicable
A nested scope may access valid declarations from its enclosing scope.
Declarations in an inner scope must not leak into an outer scope.
33. Variable Redeclaration
Redeclaring a variable with the same name in the same scope must produce an error unless a future language rule explicitly permits it.
Shadowing in nested scopes is reserved for semantic-policy refinement.
34. Function Types
A function has:
a name
parameter types
a return type
an async state
Example:
function add(a: Int, b: Int): Int {
    return a + b;
}
The function's parameter and return types must be validated.
35. Function Parameters
Every parameter must have a valid type annotation in the initial system.
Example:
function greet(name: String): Void {
    ...
}
Missing or unknown parameter types are errors.
36. Function Calls
A function call must satisfy:
the target is callable
argument count matches parameter count
every argument is compatible with its parameter type
Example:
add(1, 2);
is valid for:
function add(a: Int, b: Int): Int
Wrong argument count or incompatible types must produce errors.
37. Return Statements
A return expression must be compatible with the enclosing function's return type.
Example:
function getValue(): Int {
    return 10;
}
is valid.
This is invalid:
function getValue(): Int {
    return "text";
}
A Void function must not return a value.
38. Missing Return
The initial Type System must verify return compatibility.
Complete control-flow analysis for proving that every path returns a value is deferred to the Semantic Analysis phase unless it is required by the initial implementation.
39. If Conditions
The condition of if must be Bool.
Example:
if enabled {
    ...
}
Non-Boolean conditions are errors.
40. While Conditions
The condition of while must be Bool.
Example:
while active {
    ...
}
41. For Conditions
For the current classic for syntax:
for initializer; condition; update {
    ...
}
the condition, when present, must be Bool.
The initializer and update expressions must independently satisfy their type rules.
42. Blocks
Expressions and declarations inside a block are checked within that block's scope.
The Type System must preserve the AST structure and must not rewrite source syntax.
43. New Expression
The new expression creates a value of a user-defined type.
Example:
new User();
The referenced type must exist and be constructible according to the currently defined declaration rules.
Constructor overloading and advanced constructor semantics are deferred.
44. Member Access
For:
object.member
the Type System must:
determine the type of object
find the member
determine the member's type
validate accessibility according to currently available declaration data
Detailed visibility rules may be completed during Semantic Analysis.
45. Index Access
For:
value[index]
the Type System must verify that the target supports indexing and that the index expression has the required index type.
Initial built-in array indexing requires an Int index.
46. Arrays
Array expressions:
[1, 2, 3]
must contain compatible element types.
Example:
let values = [1, 2, 3];
infers an integer-element array type.
Mixed incompatible elements are rejected.
A dedicated array type representation is required internally.
47. This
this is valid only where an enclosing instance context exists.
Its type is the current class type.
Using this outside an instance context is an error.
48. Super
super is valid only in a class with an applicable parent type.
Its type is the appropriate parent class type.
Using super where no valid parent exists is an error.
49. Classes
A class declaration introduces a reference-like named type.
The Type System records:
class name
parent type
implemented interfaces
fields
methods
Inheritance compatibility is validated according to declared types.
50. Interfaces
An interface introduces a contract type.
A class implementing an interface must eventually satisfy its required members.
Detailed contract completeness checks may be finalized in Semantic Analysis.
51. Structs
A struct introduces a named value-like type.
Its fields must have valid types.
The initial Type System does not define native memory layout.
52. Records
A record introduces a named structured type.
Its fields must have valid types.
Record equality, immutability, generated members, and serialization behavior are deferred.
53. Inheritance
A declared extends type must resolve to a valid inheritable type.
Invalid inheritance relationships must produce type/semantic errors.
Circular inheritance detection is reserved for Semantic Analysis if required.
54. Interface Implementation
An implements type must resolve to an interface.
Implementing a non-interface type is an error.
Complete member-contract verification may be performed by Semantic Analysis.
55. Async Functions
An async function remains type-checked like a normal function for its parameters and internal expressions.
Its asynchronous result representation is reserved for the future async runtime/type specification.
56. Await
await is valid only in an asynchronous context unless future language rules explicitly expand its use.
The operand must be awaitable according to the async type model.
The complete awaitable type model is deferred until the async/runtime specification is finalized.
57. Type Equality
Two types are equal when they represent the same logical Kupln type.
Primitive types compare by their built-in identity.
Named user-defined types compare by their resolved declaration identity.
58. Type Compatibility
Compatibility is distinct from equality.
The Type System must explicitly define compatibility rather than assuming that different type names are interchangeable.
Initial implicit compatibility is intentionally minimal.
59. No Arbitrary Implicit Conversion
The Type System must not silently perform conversions such as:
String -> Int
Int -> String
Float -> Int
Int -> Float
Bool -> Int
unless a future language specification explicitly permits them.
60. Type Errors
Type errors must include at minimum:
error category
source position
relevant expression or declaration
expected type when applicable
actual type when applicable
Example:
Type error: expected Int, found String
61. Deterministic Diagnostics
The same source program and same compiler state must produce the same type diagnostics.
Diagnostics must preserve source positions from the AST.
62. Error Recovery
The initial Type System may stop after detecting a fatal type error.
Advanced multi-error recovery is not required for the first implementation.
63. Type Environment
The implementation must maintain a type environment containing enough information to resolve:
variables
parameters
functions
user-defined types
members
The environment must support nested scopes.
64. AST Boundary
The Type System consumes the existing AST.
It may annotate or associate type information with AST nodes through a separate type-analysis structure.
It must not modify the parser's lexical or syntactic responsibilities.
65. Separation from Semantic Analysis
The initial Type System handles type correctness.
The following may be handled more completely by Semantic Analysis:
complete name resolution
visibility/access policies
inheritance-cycle analysis
interface contract completeness
advanced control-flow rules
definite initialization
unreachable code
advanced overload resolution
66. Separation from Compiler
The Type System must not:
generate machine code
generate bytecode
generate IR
select CPU instructions
select Android/iOS/desktop backends
perform native ABI lowering
execute programs
67. Unsupported Features
The initial Type System does not implement:
generics
union types
intersection types
function/lambda types
operator overloading
pattern matching types
dependent types
advanced type inference
user-defined implicit conversions
macros
annotations
advanced nullability
ownership/borrowing types
These require later specifications.
68. Testing Requirements
Phase 6 must include tests for:
every built-in type
explicit annotations
inference
valid assignments
invalid assignments
arithmetic
comparisons
logical operators
equality
conditional expressions
null-coalescing
variables and scopes
functions
parameters
calls
return types
conditions
arrays
member access
indexing
new
classes
interfaces
structs
records
this
super
async/await
invalid programs
diagnostic positions
69. Regression Testing
All existing tests from:
Host
Lexer
Parser
must continue to pass.
Type System tests must not require native platform SDKs.
70. Implementation Dependencies
The implementation may use the Python standard library.
External dependencies are not required for the bootstrap Type System.
The implementation must work with the current repository structure.
71. Current Bootstrap Scope
Phase 6 implements only the minimum Type System required to validate the current Kupln syntax.
Advanced language features remain deferred.
The implementation must not prematurely introduce compiler, runtime, or platform-specific concepts.
72. Phase 6 Completion Criteria
Phase 6 is complete when:
A Type System implementation exists.
Built-in types are represented.
User-defined types are represented.
Type annotations are validated.
Type inference works for supported expressions.
Assignment compatibility works.
Function calls and returns are checked.
Expression types are checked.
Scope/type environments work.
Type errors are deterministic and positioned.
Type System tests pass.
Existing Host, Lexer, and Parser tests pass.
Project Guard passes.
CI passes.
No compiler/backend/runtime implementation is introduced prematurely.
73. Final Principle
The Kupln Type System answers one fundamental question:
"Is this program type-correct according to the Kupln language rules?"
It does not answer how the program is executed or how it is compiled for a specific platform.
Those responsibilities belong to later phases.
