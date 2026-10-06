# Kupln Lexical Specification

## 1. Purpose

This document defines the lexical rules of the Kupln programming language.

The lexical layer transforms Kupln source text into an ordered sequence of lexical tokens.

The lexer is responsible for recognizing lexical forms only.

The lexer must not perform:

- parsing
- semantic analysis
- type checking
- name resolution
- code generation
- backend selection
- runtime execution
- package resolution

The lexical specification is authoritative for the Kupln lexical foundation.

---

## 2. Source Encoding

Kupln source files use UTF-8 encoding.

Invalid UTF-8 input must be rejected before lexical analysis begins.

The lexer operates on decoded Unicode source text.

The lexer must preserve the original source lexeme represented by each token.

---

## 3. Source Positions

Every emitted token has a source position containing:

- line
- column
- offset

Line numbering starts at `1`.

Column numbering starts at `1`.

Offset numbering starts at `0`.

A newline advances the line number and resets the column to `1`.

The exact Unicode counting semantics of columns and offsets remain subject to future formalization before becoming an externally guaranteed compiler or tooling interface.

---

## 4. Whitespace

Whitespace separates lexical elements but does not normally produce tokens.

The bootstrap lexer recognizes:

- space
- horizontal tab
- carriage return
- line feed

Whitespace must not change the lexical identity of adjacent tokens except where required to prevent ambiguous token formation.

---

## 5. Identifiers

An identifier names a program element.

An identifier begins with:

- `_`
- a Unicode alphabetic character

After the first character, an identifier may contain:

- `_`
- Unicode alphabetic characters
- Unicode numeric characters

Identifiers are case-sensitive.

Examples:

```text
value
_value
message2
رسالة
بيانات_المستخدم
An identifier must not be classified as an identifier when its complete lexeme is a reserved keyword.
6. Reserved Keywords
Reserved keywords have predefined language-level meaning.
The current reserved keyword set is:
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
Keyword recognition must be centralized through the Kupln keyword definition.
A longer identifier containing a keyword must remain an identifier.
For example:
let
letter
return
returnValue
The first and third examples are keywords.
The second and fourth examples are identifiers.
Future keywords must not be added without a language specification decision.
7. Integer Literals
An integer literal consists of one or more decimal digits.
Examples:
0
1
42
1000
The bootstrap lexical foundation recognizes decimal integer literals.
Numeric sign characters are operators rather than part of the integer literal.
Therefore:
-42
is lexically represented as:
-
42
Numeric bases other than decimal are not part of the current lexical foundation.
8. Floating-Point Literals
A bootstrap floating-point literal consists of:
one or more decimal digits
a decimal point
one or more decimal digits
Examples:
0.0
3.14
42.5
The following forms are not currently part of the bootstrap floating-point syntax:
.5
5.
1e10
1.5e10
These forms may be introduced later through an explicit lexical specification change.
9. String Literals
String literals are enclosed by double quotation marks:
"hello"
A string literal may contain Unicode characters.
The original lexeme, including its quotation marks, is preserved in the token.
A backslash introduces an escaped character sequence.
For example:
"hello \"Kupln\""
An unterminated string literal is a lexical error.
The complete set of valid escape sequences will be formalized before the language guarantees their semantic interpretation.
10. Character Literals
Character literals are enclosed by single quotation marks:
'A'
'م'
A character literal represents one character or one escaped character sequence.
Examples:
'A'
'م'
'\n'
An unterminated or structurally invalid character literal is a lexical error.
The complete escape-sequence semantics will be formalized separately from lexical recognition.
11. Punctuation
The current lexical punctuation set is:
(
)
{
}
[
]
,
.
:
;
Each punctuation symbol is emitted as a PUNCTUATION token.
Punctuation does not have semantic meaning at the lexical layer beyond its identity.
12. Operators
The bootstrap lexical foundation recognizes operator symbols.
Single-character operators currently include:
+
-
*
/
%
=
!
<
>
&
|
^
?
The current multi-character operator set includes:
==
!=
<=
>=
++
--
&&
||
->
??
Operator recognition must use the longest valid operator sequence supported by the lexical specification.
Operators are distinct from punctuation.
The final operator set remains extensible through explicit language specification changes.
13. Comments
Kupln supports line comments and block comments.
13.1 Line Comments
A line comment begins with:
//
and continues until the next line ending or end of source.
Example:
// this is a comment
Line comments are lexically represented as COMMENT tokens in the bootstrap implementation.
13.2 Block Comments
A block comment begins with:
/*
and ends with:
*/
Example:
/*
   this is a
   block comment
*/
Block comments may span multiple lines.
An unterminated block comment is a lexical error.
The bootstrap lexer preserves comments as COMMENT tokens.
Future parser and tooling stages may define whether comments are retained, discarded, or attached as trivia.
14. Token Categories
The bootstrap token model currently provides:
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
UNKNOWN is reserved for future lexical handling where required.
The lexer must not silently discard unsupported source characters.
Unsupported characters must produce a lexical error unless the lexical specification explicitly defines them.
15. End of File
Every successful lexical analysis produces exactly one EOF token.
The EOF token has:
kind: EOF
empty lexeme
source position at the end of the processed source
No additional tokens may appear after EOF.
16. Lexical Errors
The lexer must report malformed lexical input rather than silently accepting or ignoring it.
The bootstrap lexical foundation currently recognizes errors including:
unsupported characters
unterminated strings
invalid character literals
unterminated block comments
Lexical errors must preserve enough source-position information to support future diagnostics.
17. Unicode Policy
Kupln source is Unicode-aware.
Unicode must be preserved in:
identifiers
strings
character literals
comments
source text
The lexical implementation must not impose an ASCII-only restriction.
The currently implemented identifier rule uses the host language's Unicode character classification facilities as a bootstrap mechanism.
The final Unicode identifier profile may be refined through a future specification revision.
18. Lexical Determinism
Given identical decoded source text, lexical analysis must produce the same ordered token sequence.
Lexical behavior must not depend on:
network access
filesystem state
current time
random values
machine-specific configuration
undeclared environment variables
19. Lexical Preservation
Where a token represents source text, the lexer should preserve the original lexeme rather than silently rewriting it.
This includes:
identifier spelling
keyword spelling
numeric literal spelling
string literal spelling
character literal spelling
operator spelling
punctuation spelling
comment spelling
Normalization and semantic interpretation belong to later compiler stages unless explicitly defined as lexical behavior.
20. Lexical Boundary
The lexical layer ends after tokenization.
The following operations belong to later stages:
Tokenization
    ↓
Parsing
    ↓
AST Construction
    ↓
Semantic Analysis
    ↓
Type Checking
    ↓
IR Construction
    ↓
Optimization
    ↓
Backend Compilation
The lexer must not construct an AST or perform semantic interpretation.
21. Specification Evolution
Changes to lexical behavior must update this specification before or together with the corresponding implementation change.
A lexical implementation must not introduce undocumented language syntax.
Changes affecting:
identifiers
keywords
literals
operators
punctuation
comments
Unicode rules
token categories
source positions
lexical errors
must be evaluated against the Kupln architecture and Bootstrap Constitution.
22. Current Bootstrap Scope
The current lexical foundation intentionally provides only the minimum lexical functionality required to establish a reliable Kupln lexer.
It does not yet define the complete final Kupln language.
The following remain future specification areas where required:
complete escape-sequence semantics
complete numeric literal system
exact Unicode identifier profile
complete operator inventory
complete punctuation inventory
lexical treatment of additional literal types
exact source-position semantics
final comment/trivia model
These must be introduced through explicit specification work rather than accidental implementation growth.
23. Implementation Conformance
The bootstrap lexer must conform to this specification within the scope of the rules currently marked as implemented.
Tests must verify observable lexical behavior.
When a specification rule becomes implemented, corresponding tests should be added or expanded.
The implementation must not be considered complete merely because the lexer source exists.
Conformance requires:
implementation
automated tests
successful CI validation
consistency with the Bootstrap Constitution
