# Kupln Syntax Specification

## 1. Purpose

This document defines the syntax of the Kupln programming language.

It specifies how Kupln source code is structurally formed from the lexical tokens defined by:

`docs/specification/lexical.md`

This specification is the authoritative syntax boundary for the bootstrap parser and later Kupln parser implementations.

The syntax layer defines structure only.

It does not define:

- type correctness
- name resolution
- overload resolution
- variable lifetime
- ownership or borrowing rules
- memory management semantics
- execution behavior
- runtime behavior
- platform behavior
- code generation
- backend behavior
- package resolution
- optimization

Those responsibilities belong to later compiler and semantic layers.

---

## 2. Syntax Boundary

The Kupln frontend is conceptually divided into the following boundaries:

```text
Source Text
    ↓
Lexer
    ↓
Tokens
    ↓
Parser
    ↓
Syntax Tree / AST
    ↓
Semantic Analysis
    ↓
Type System
    ↓
Intermediate Representation
    ↓
Compiler / Backend
The parser consumes tokens and determines whether they form a valid Kupln syntactic structure.
The parser must not perform semantic analysis.
3. Input to the Parser
The parser receives the token stream produced by the Kupln lexer.
The lexer currently provides these token categories:
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
The parser must reject UNKNOWN tokens as invalid syntax unless a future specification explicitly assigns them a syntactic meaning.
4. Comments and Trivia
Comments are lexically represented as COMMENT tokens during the bootstrap stage.
Comments do not form program structure.
The parser shall treat comments as syntactic trivia and ignore them when determining grammar structure.
Comments must not change the syntactic meaning of surrounding tokens.
The lexical specification defines the supported comment forms:
// line comment

/* block comment */
5. Whitespace and Line Structure
Whitespace is not syntactically significant.
Newlines do not terminate statements.
Statement termination is determined by the grammar, normally through ;.
Therefore:
let x = 1;
and:
let
x
=
1
;
have the same syntactic structure when the lexical layer produces the corresponding tokens.
Formatting remains the responsibility of developer tools.
6. Grammar Notation
This document uses an EBNF-like notation.
The notation is:
A = B ;
defines a production.
A = B | C ;
means either B or C.
[A]
means optional.
{ A }
means zero or more repetitions.
Parentheses group grammar expressions.
Terminal tokens are written using quoted symbols or token names.
7. Compilation Unit
A Kupln source file is a compilation unit.
compilation-unit
    = { top-level-item } EOF ;
A compilation unit may contain:
imports
declarations
exported declarations
statements allowed at the top level
The exact semantic restrictions on top-level executable code are outside the syntax layer.
8. Top-Level Items
top-level-item
    = import-declaration
    | export-declaration
    | declaration
    | statement ;
A future language revision may restrict top-level statements without changing the fundamental parser architecture.
9. Declarations
declaration
    = variable-declaration
    | function-declaration
    | class-declaration
    | interface-declaration
    | struct-declaration
    | record-declaration ;
Declarations may appear at the top level and, where permitted by their syntactic form, inside blocks.
Semantic rules determine which declarations are legal in a particular scope.
10. Variable Declarations
Kupln provides let and var declaration forms.
variable-declaration
    = [ declaration-modifiers ]
      variable-keyword
      identifier
      [ type-annotation ]
      [ "=" expression ]
      ";" ;

variable-keyword
    = "let"
    | "var" ;
A declaration may therefore take forms such as:
let value = 10;
var name = "Kupln";
let count: Number = 10;
var item: Item;
Whether a declaration requires initialization, what let and var mean, and whether reassignment is permitted are semantic rules.
11. Type Annotations
Type syntax is recognized structurally by the parser but its validity is determined later by the type system.
type-annotation
    = ":" type-reference ;

type-reference
    = type-name { "." type-name } ;

type-name
    = IDENTIFIER ;
The syntax layer does not determine whether a referenced type exists.
Examples:
let count: Number = 10;
let user: User;
let value: package.Type;
Name resolution and type validation are outside the parser.
12. Functions
A function declaration has the following structure:
function-declaration
    = [ "async" ]
      [ declaration-modifiers ]
      "function"
      identifier
      "(" [ parameter-list ] ")"
      [ type-annotation ]
      block ;
Parameters are defined by:
parameter-list
    = parameter { "," parameter } ;

parameter
    = identifier
      [ type-annotation ] ;
Examples:
function greet(name) {
    return name;
}
function add(a: Number, b: Number): Number {
    return a + b;
}
async function loadData(): Data {
    return await fetchData();
}
The meaning of async and await belongs to the semantic/runtime layers.
13. Declaration Modifiers
The current lexical keyword set includes declaration and access modifiers.
declaration-modifiers
    = { declaration-modifier } ;

declaration-modifier
    = "abstract"
    | "final"
    | "public"
    | "private"
    | "protected"
    | "static" ;
The parser recognizes their syntactic placement.
Their legality and interaction are semantic rules.
14. Blocks
A block is a sequence of statements and declarations enclosed by braces.
block
    = "{" { block-item } "}" ;

block-item
    = declaration
    | statement ;
An empty block is valid:
{
}
15. Statements
statement
    = block
    | variable-declaration
    | expression-statement
    | return-statement
    | if-statement
    | while-statement
    | for-statement
    | try-statement
    | empty-statement ;
16. Expression Statements
expression-statement
    = expression ";" ;
Examples:
foo();
x = 10;
counter++;
17. Empty Statements
empty-statement
    = ";" ;
An empty statement has no syntactic content beyond its terminator.
Its semantic meaning, if any, is defined later.
18. Return Statements
return-statement
    = "return" [ expression ] ";" ;
Both forms are syntactically valid:
return;
return value;
Whether a return value is allowed in a particular function is a semantic rule.
19. Conditional Statements
if-statement
    = "if"
      "(" expression ")"
      statement
      [ "else" statement ] ;
Examples:
if (condition) {
    doSomething();
}
if (condition) {
    first();
} else {
    second();
}
The else associates with the nearest unmatched if.
20. While Loops
while-statement
    = "while"
      "(" expression ")"
      statement ;
Example:
while (condition) {
    process();
}
21. For Loops
The current syntax uses a three-part for form.
for-statement
    = "for"
      "("
      [ for-initializer ]
      ";"
      [ expression ]
      ";"
      [ expression ]
      ")"
      statement ;
The initializer may be a variable declaration or expression.
for-initializer
    = variable-declaration-no-semicolon
    | expression ;
The declaration form used inside the for header omits its final semicolon:
variable-declaration-no-semicolon
    = [ declaration-modifiers ]
      variable-keyword
      identifier
      [ type-annotation ]
      [ "=" expression ] ;
Example:
for (let i = 0; i < 10; i++) {
    process(i);
}
22. Try and Catch
try-statement
    = "try"
      block
      "catch"
      "(" identifier ")"
      block ;
Example:
try {
    process();
} catch (error) {
    handle(error);
}
The current syntax specification does not introduce a finally keyword because it is not part of the current reserved keyword set.
23. Import Declarations
The current syntax provides a minimal import form.
import-declaration
    = "import" STRING ";" ;
Example:
import "core";
Module resolution, package resolution, import visibility, and dependency resolution are outside the syntax layer.
The import grammar may be extended in a later specification revision.
24. Export Declarations
export-declaration
    = "export" declaration ;
Example:
export function add(a, b) {
    return a + b;
}
The semantic meaning of exported declarations belongs to the module and package systems.
25. Class Declarations
class-declaration
    = [ declaration-modifiers ]
      "class"
      identifier
      [ extends-clause ]
      [ implements-clause ]
      class-body ;

class-body
    = "{"
      { class-member }
      "}" ;
Inheritance:
extends-clause
    = "extends" type-reference ;
Interfaces implemented by a class:
implements-clause
    = "implements"
      type-reference
      { "," type-reference } ;
26. Class Members
class-member
    = field-declaration
    | function-declaration ;
Fields:
field-declaration
    = [ declaration-modifiers ]
      identifier
      [ type-annotation ]
      [ "=" expression ]
      ";" ;
A class may therefore contain:
class User {
    public name: String;

    private age: Number = 0;

    function greet() {
        return name;
    }
}
Whether a member is accessible, mutable, static, abstract, final, or otherwise restricted is determined semantically.
27. Interface Declarations
interface-declaration
    = [ declaration-modifiers ]
      "interface"
      identifier
      [ extends-clause ]
      interface-body ;

interface-body
    = "{"
      { interface-member }
      "}" ;
An interface member is currently represented as a function declaration without a body:
interface-member
    = interface-function-declaration
    | field-signature ;

interface-function-declaration
    = [ declaration-modifiers ]
      "function"
      identifier
      "(" [ parameter-list ] ")"
      [ type-annotation ]
      ";" ;

field-signature
    = identifier
      [ type-annotation ]
      ";" ;
The semantic meaning of interfaces is defined by later language layers.
28. Struct Declarations
struct-declaration
    = [ declaration-modifiers ]
      "struct"
      identifier
      struct-body ;

struct-body
    = "{"
      { field-declaration }
      "}" ;
The parser recognizes the structure only.
Memory layout, value semantics, ownership, copying, and ABI behavior belong to later phases.
29. Record Declarations
record-declaration
    = [ declaration-modifiers ]
      "record"
      identifier
      record-body ;

record-body
    = "{"
      { field-declaration }
      "}" ;
Record semantics are outside the syntax layer.
30. Expressions
Expressions form the primary computational syntax of Kupln.
expression
    = assignment-expression ;
The expression grammar is organized by precedence.
Higher-precedence expressions bind more tightly than lower-precedence expressions.
31. Assignment Expressions
assignment-expression
    = conditional-expression
      [ "=" assignment-expression ] ;
Assignment is right-associative.
Example:
a = b = value;
The parser determines structure only.
Whether the left-hand side is assignable is a semantic rule.
32. Conditional Expressions
conditional-expression
    = null-coalescing-expression
      [ "?" expression ":" conditional-expression ] ;
Example:
result = condition ? first : second;
33. Null-Coalescing Expressions
null-coalescing-expression
    = logical-or-expression
      { "??" logical-or-expression } ;
34. Logical OR Expressions
logical-or-expression
    = logical-and-expression
      { "||" logical-and-expression } ;
35. Logical AND Expressions
logical-and-expression
    = equality-expression
      { "&&" equality-expression } ;
36. Equality Expressions
equality-expression
    = comparison-expression
      { equality-operator comparison-expression } ;

equality-operator
    = "=="
    | "!=" ;
37. Comparison Expressions
comparison-expression
    = additive-expression
      { comparison-operator additive-expression } ;

comparison-operator
    = "<"
    | ">"
    | "<="
    | ">=" ;
38. Additive Expressions
additive-expression
    = multiplicative-expression
      { additive-operator multiplicative-expression } ;

additive-operator
    = "+"
    | "-" ;
39. Multiplicative Expressions
multiplicative-expression
    = unary-expression
      { multiplicative-operator unary-expression } ;

multiplicative-operator
    = "*"
    | "/"
    | "%" ;
40. Unary Expressions
unary-expression
    = "await" unary-expression
    | unary-operator unary-expression
    | postfix-expression ;

unary-operator
    = "+"
    | "-"
    | "!" 
    | "++"
    | "--" ;
Examples:
-x
!ready
++counter
--counter
The semantic validity of unary operators is outside the parser.
41. Postfix Expressions
postfix-expression
    = primary-expression
      { postfix-operation }
      [ postfix-increment ] ;

postfix-operation
    = call-expression
    | member-access
    | index-access ;

postfix-increment
    = "++"
    | "--" ;
42. Function Calls
call-expression
    = "(" [ argument-list ] ")" ;

argument-list
    = expression { "," expression } ;
Example:
calculate(a, b);
Calls may be chained:
object.method(a)(b);
43. Member Access
member-access
    = "." identifier ;
Example:
user.name
object.method
44. Index Access
index-access
    = "[" expression "]" ;
Example:
items[index]
45. Primary Expressions
primary-expression
    = identifier
    | integer-literal
    | float-literal
    | string-literal
    | char-literal
    | boolean-literal
    | null-literal
    | this-expression
    | super-expression
    | new-expression
    | array-literal
    | parenthesized-expression ;
46. Identifiers
identifier
    = IDENTIFIER ;
Identifier lexical rules are defined by:
docs/specification/lexical.md
The parser must not redefine lexical identifier rules.
47. Literal Expressions
Integer and floating-point literals use the lexical forms defined by the lexical specification.
integer-literal
    = INTEGER ;

float-literal
    = FLOAT ;

string-literal
    = STRING ;

char-literal
    = CHAR ;
Boolean literals:
boolean-literal
    = "true"
    | "false" ;
Null:
null-literal
    = "null" ;
Although these are currently lexed as keyword tokens, their use as literal expressions is defined syntactically here.
48. This Expression
this-expression
    = "this" ;
Example:
this.name
49. Super Expression
super-expression
    = "super" ;
Examples:
super();
super.name;
super.method();
The legality and behavior of super are semantic rules.
50. Object Construction
new-expression
    = "new"
      type-reference
      "(" [ argument-list ] ")" ;
Example:
new User(name);
The parser does not determine whether the referenced type is constructible.
51. Array Literals
The current syntax supports a basic array literal form.
array-literal
    = "["
      [ expression { "," expression } ]
      "]" ;
Examples:
[]
[1, 2, 3]
["a", "b", "c"]
The semantic type of an array is determined later.
52. Parenthesized Expressions
parenthesized-expression
    = "(" expression ")" ;
Example:
(a + b) * c
Parentheses explicitly override normal expression precedence.
53. Async and Await
The current lexical specification reserves async and await.
Asynchronous functions use:
async function name(...) {
    ...
}
Await expressions use:
Therefore await is also accepted as an expression form:
expression
    = assignment-expression ;

The semantic restrictions on where await may appear are defined later.
54. Operator Precedence
The current precedence hierarchy, from lowest to highest, is:
1.  assignment             =
2.  conditional             ? :
3.  null coalescing         ??
4.  logical OR              ||
5.  logical AND             &&
6.  equality                == !=
7.  comparison              < > <= >=
8.  additive                + -
9.  multiplicative          * / %
10. unary                   + - ! ++ --
11. postfix                 calls, member access, indexing, ++ --
12. primary                 literals, identifiers, grouping, etc.
Assignment is right-associative.
Conditional expressions are right-associative.
The binary operators at the same precedence level are left-associative unless a future specification explicitly changes their associativity.
55. Statement Termination
Simple statements and declarations use ;.
Examples:
let x = 1;

x = 2;

return x;

foo();
Blocks do not require a semicolon:
if (condition) {
    foo();
}
The syntax does not use automatic semicolon insertion in the current specification.
56. Ambiguity and Parser Responsibility
The parser must resolve syntactic ambiguity according to the grammar and precedence rules defined by this specification.
The parser must not resolve ambiguity using semantic information that belongs to later compiler phases unless a future specification explicitly requires such behavior.
Where a future language feature introduces ambiguity, the syntax specification must be updated before the implementation is changed.
57. Syntax Errors
The parser must report syntax errors when the token stream cannot be matched to the grammar.
Examples include:
missing closing )
missing closing }
missing ]
missing statement terminator
malformed declaration
malformed function parameter list
malformed expression
invalid operator placement
unexpected EOF
unexpected token
Syntax diagnostics must identify the relevant source position when available.
The exact diagnostic API may be defined by the parser and compiler infrastructure specifications.
58. Parser Boundary
The parser is responsible for:
consuming lexical tokens
validating syntactic structure
applying grammar rules
applying expression precedence
constructing the syntax representation
reporting syntax errors
preserving source positions where required
The parser is not responsible for:
type checking
name resolution
ownership checking
borrow checking
overload resolution
constant evaluation
code generation
optimization
runtime execution
platform selection
package resolution
59. Syntax Tree Boundary
The parser should produce a structured syntax representation suitable for later compiler phases.
The exact AST node hierarchy is not fixed by this document.
The AST design must preserve enough information for later stages to perform:
semantic analysis
type checking
name resolution
ownership analysis
lowering
intermediate representation generation
AST design must not prematurely encode backend-specific behavior.
60. Current Bootstrap Scope
The current syntax specification establishes the foundation for the first Kupln parser.
It intentionally does not define every future Kupln language feature.
The following are outside the current syntax scope unless separately added to the specification:
pattern matching
switch
match
do/while
break
continue
throw
finally
enumerations
generic type parameters
lambda expressions
destructuring
operator overloading
macros
annotations/attributes
advanced module syntax
advanced pattern syntax
advanced collection syntax
metaprogramming syntax
These features must not be implemented merely because they may be useful in the future.
61. Reserved Keyword Discipline
The syntax specification may use only keywords that are part of the current lexical specification.
The current syntax uses:
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
Future keywords must not be introduced implicitly by the parser.
A new keyword requires a corresponding lexical specification update.
62. Syntax Evolution
Changes to Kupln syntax must follow this order:
Syntax decision
    ↓
Syntax specification update
    ↓
Parser implementation
    ↓
Parser tests
    ↓
Project Guard / CI validation
The implementation must not silently introduce syntax that is absent from the specification.
If a syntax feature conflicts with the lexical layer, the lexical specification must be reviewed first.
63. Determinism
Given the same valid token stream, the parser must produce the same syntactic structure.
Given the same invalid token stream, syntax validation must deterministically identify failure according to the parser's diagnostic rules.
Parser behavior must not depend on:
system locale
platform
filesystem ordering
network access
external services
nondeterministic iteration
runtime environment differences
64. Implementation Conformance
A parser implementation conforms to this specification when:
It consumes the token model defined by the lexical layer.
It recognizes the grammar defined here.
It applies the specified operator precedence.
It recognizes the current reserved keywords only where syntactically defined.
It reports invalid syntax deterministically.
It preserves source positions where required.
It does not perform semantic analysis.
It has automated tests covering implemented grammar.
Project Guard and CI continue to pass.
Any intentional syntax deviation is reflected in the specification before or together with the implementation change.
65. Relationship to Later Phases
This specification establishes the syntax foundation for the next compiler stages.
The following phases will build on it:
Phase 5
Kupln Syntax
    ↓
Phase 6
Kupln Type System
    ↓
Phase 7
Kupln Semantics
    ↓
Phase 8
Kupln Compiler
The syntax layer must therefore remain independent from the type system, semantic analyzer, runtime, and platform backends.
66. Final Principle
Kupln syntax must be explicit, deterministic, extensible, and independently testable.
The parser must understand the structure of the language without attempting to decide what that structure means.
The syntax specification is the contract between the lexical layer and the semantic/compiler layers.
