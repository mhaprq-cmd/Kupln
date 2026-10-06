"""Tests for the Kupln bootstrap lexer."""

from __future__ import annotations

import unittest

from bootstrap.lexer.keywords import is_reserved_keyword
from bootstrap.lexer.lexer import (
    Lexer,
    LexerError,
    UnexpectedCharacterError,
)
from bootstrap.lexer.token import TokenKind


class LexerTests(unittest.TestCase):
    """Validate the Kupln bootstrap lexical foundation."""

    def test_identifier_and_keyword_recognition(self) -> None:
        """Identifiers and reserved keywords must be classified correctly."""
        tokens = Lexer("let value = return").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[0].lexeme, "let")

        self.assertEqual(tokens[1].kind, TokenKind.IDENTIFIER)
        self.assertEqual(tokens[1].lexeme, "value")

        self.assertEqual(tokens[2].kind, TokenKind.OPERATOR)
        self.assertEqual(tokens[2].lexeme, "=")

        self.assertEqual(tokens[3].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[3].lexeme, "return")

        self.assertEqual(tokens[4].kind, TokenKind.EOF)

    def test_identifier_with_underscore(self) -> None:
        """Identifiers may begin with or contain underscores."""
        tokens = Lexer("_value value_name __private").tokenize()

        identifiers = [token.lexeme for token in tokens[:-1]]

        self.assertEqual(
            identifiers,
            ["_value", "value_name", "__private"],
        )

        for token in tokens[:-1]:
            self.assertEqual(token.kind, TokenKind.IDENTIFIER)

    def test_unicode_identifier(self) -> None:
        """Unicode identifiers must be preserved by the lexer."""
        tokens = Lexer("let رسالة = 10").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[1].kind, TokenKind.IDENTIFIER)
        self.assertEqual(tokens[1].lexeme, "رسالة")

    def test_unicode_identifier_with_numeric_character(self) -> None:
        """Unicode numeric characters may continue an identifier."""
        tokens = Lexer("بيانات٢").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.IDENTIFIER)
        self.assertEqual(tokens[0].lexeme, "بيانات٢")

    def test_identifier_is_case_sensitive(self) -> None:
        """Identifiers must preserve case distinctions."""
        tokens = Lexer("value Value VALUE").tokenize()

        self.assertEqual(
            [token.kind for token in tokens[:-1]],
            [
                TokenKind.IDENTIFIER,
                TokenKind.IDENTIFIER,
                TokenKind.IDENTIFIER,
            ],
        )

        self.assertEqual(
            [token.lexeme for token in tokens[:-1]],
            ["value", "Value", "VALUE"],
        )

    def test_integer_and_float_literals(self) -> None:
        """Integer and decimal floating-point literals must be classified."""
        tokens = Lexer("42 3.14").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.INTEGER)
        self.assertEqual(tokens[0].lexeme, "42")

        self.assertEqual(tokens[1].kind, TokenKind.FLOAT)
        self.assertEqual(tokens[1].lexeme, "3.14")

    def test_negative_number_is_operator_followed_by_integer(self) -> None:
        """Numeric sign characters must remain separate operators."""
        tokens = Lexer("-42").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.OPERATOR)
        self.assertEqual(tokens[0].lexeme, "-")

        self.assertEqual(tokens[1].kind, TokenKind.INTEGER)
        self.assertEqual(tokens[1].lexeme, "42")

    def test_string_literal(self) -> None:
        """String literals must preserve their original lexeme."""
        tokens = Lexer('"hello Kupln"').tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.STRING)
        self.assertEqual(tokens[0].lexeme, '"hello Kupln"')

    def test_unicode_string_literal(self) -> None:
        """Unicode characters inside strings must be preserved."""
        tokens = Lexer('"مرحبا Kupln"').tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.STRING)
        self.assertEqual(tokens[0].lexeme, '"مرحبا Kupln"')

    def test_escaped_string_literal(self) -> None:
        """Escaped characters inside strings must be accepted."""
        tokens = Lexer(r'"hello \"Kupln\""').tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.STRING)
        self.assertEqual(tokens[0].lexeme, r'"hello \"Kupln\""')

    def test_character_literal(self) -> None:
        """Character literals must be classified correctly."""
        tokens = Lexer("'A' 'م'").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.CHAR)
        self.assertEqual(tokens[0].lexeme, "'A'")

        self.assertEqual(tokens[1].kind, TokenKind.CHAR)
        self.assertEqual(tokens[1].lexeme, "'م'")

    def test_escaped_character_literal(self) -> None:
        """Escaped character literals must be accepted."""
        tokens = Lexer(r"'\n'").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.CHAR)
        self.assertEqual(tokens[0].lexeme, r"'\n'")

    def test_punctuation(self) -> None:
        """Supported punctuation must be emitted as punctuation tokens."""
        tokens = Lexer("(){}[],.:;").tokenize()

        punctuation = [token.lexeme for token in tokens[:-1]]

        self.assertEqual(
            punctuation,
            ["(", ")", "{", "}", "[", "]", ",", ".", ":", ";"],
        )

        for token in tokens[:-1]:
            self.assertEqual(token.kind, TokenKind.PUNCTUATION)

    def test_single_character_operators(self) -> None:
        """All current single-character operators must be recognized."""
        tokens = Lexer("+ - * / % = ! < > & | ^ ?").tokenize()

        operators = [token.lexeme for token in tokens[:-1]]

        self.assertEqual(
            operators,
            ["+", "-", "*", "/", "%", "=", "!", "<", ">", "&", "|", "^", "?"],
        )

        for token in tokens[:-1]:
            self.assertEqual(token.kind, TokenKind.OPERATOR)

    def test_multi_character_operators(self) -> None:
        """Supported multi-character operators must remain single tokens."""
        tokens = Lexer("== != <= >= ++ -- && || -> ??").tokenize()

        operators = [token.lexeme for token in tokens[:-1]]

        self.assertEqual(
            operators,
            ["==", "!=", "<=", ">=", "++", "--", "&&", "||", "->", "??"],
        )

        for token in tokens[:-1]:
            self.assertEqual(token.kind, TokenKind.OPERATOR)

    def test_operator_longest_match(self) -> None:
        """Supported multi-character operators must use the longest match."""
        tokens = Lexer("== != <= >= ++ -- && || -> ??").tokenize()

        self.assertEqual(
            [token.lexeme for token in tokens[:-1]],
            ["==", "!=", "<=", ">=", "++", "--", "&&", "||", "->", "??"],
        )

    def test_line_comment(self) -> None:
        """Line comments must be emitted as comment tokens."""
        tokens = Lexer("// hello\nlet value = 1").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.COMMENT)
        self.assertEqual(tokens[0].lexeme, "// hello")

        self.assertEqual(tokens[1].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[1].lexeme, "let")

    def test_line_comment_at_end_of_source(self) -> None:
        """A line comment may continue to the end of the source."""
        tokens = Lexer("// hello").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.COMMENT)
        self.assertEqual(tokens[0].lexeme, "// hello")
        self.assertEqual(tokens[1].kind, TokenKind.EOF)

    def test_unicode_line_comment(self) -> None:
        """Unicode content inside comments must be preserved."""
        tokens = Lexer("// تعليق عربي").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.COMMENT)
        self.assertEqual(tokens[0].lexeme, "// تعليق عربي")

    def test_block_comment(self) -> None:
        """Block comments must be emitted as comment tokens."""
        tokens = Lexer("/* hello */ let").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.COMMENT)
        self.assertEqual(tokens[0].lexeme, "/* hello */")

        self.assertEqual(tokens[1].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[1].lexeme, "let")

    def test_multiline_block_comment(self) -> None:
        """Block comments may span multiple lines."""
        tokens = Lexer("/* line one\nline two */let").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.COMMENT)
        self.assertEqual(tokens[0].lexeme, "/* line one\nline two */")

        self.assertEqual(tokens[1].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[1].lexeme, "let")

    def test_eof_token(self) -> None:
        """Every successful tokenization must end with an explicit EOF token."""
        tokens = Lexer("").tokenize()

        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].kind, TokenKind.EOF)
        self.assertEqual(tokens[0].lexeme, "")

    def test_eof_position(self) -> None:
        """EOF must point to the end of the processed source."""
        tokens = Lexer("let").tokenize()

        eof = tokens[-1]

        self.assertEqual(eof.kind, TokenKind.EOF)
        self.assertEqual(eof.position.line, 1)
        self.assertEqual(eof.position.column, 4)
        self.assertEqual(eof.position.offset, 3)

    def test_source_positions(self) -> None:
        """Token positions must track line, column, and offset."""
        tokens = Lexer("let\nvalue").tokenize()

        self.assertEqual(tokens[0].position.line, 1)
        self.assertEqual(tokens[0].position.column, 1)
        self.assertEqual(tokens[0].position.offset, 0)

        self.assertEqual(tokens[1].position.line, 2)
        self.assertEqual(tokens[1].position.column, 1)
        self.assertEqual(tokens[1].position.offset, 4)

    def test_crlf_source_positions(self) -> None:
        """CRLF line endings must advance to the next line."""
        tokens = Lexer("let\r\nvalue").tokenize()

        self.assertEqual(tokens[0].position.line, 1)
        self.assertEqual(tokens[0].position.column, 1)
        self.assertEqual(tokens[0].position.offset, 0)

        self.assertEqual(tokens[1].position.line, 2)
        self.assertEqual(tokens[1].position.column, 1)
        self.assertEqual(tokens[1].position.offset, 5)

    def test_reserved_keyword_boundary(self) -> None:
        """Keyword lookup must not classify longer identifiers as keywords."""
        self.assertTrue(is_reserved_keyword("let"))
        self.assertFalse(is_reserved_keyword("letter"))

        tokens = Lexer("letter").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.IDENTIFIER)
        self.assertEqual(tokens[0].lexeme, "letter")

    def test_reserved_keywords_remain_centralized(self) -> None:
        """The lexer must classify the current reserved keywords."""
        keywords = (
            "let",
            "var",
            "function",
            "return",
            "if",
            "else",
            "for",
            "while",
            "class",
            "interface",
            "extends",
            "implements",
            "abstract",
            "final",
            "public",
            "private",
            "protected",
            "static",
            "struct",
            "record",
            "true",
            "false",
            "try",
            "catch",
            "async",
            "await",
            "import",
            "export",
            "new",
            "this",
            "super",
            "null",
        )

        for keyword in keywords:
            self.assertTrue(is_reserved_keyword(keyword))

        tokens = Lexer(" ".join(keywords)).tokenize()

        for token, keyword in zip(tokens[:-1], keywords):
            self.assertEqual(token.kind, TokenKind.KEYWORD)
            self.assertEqual(token.lexeme, keyword)

    def test_token_lexeme_preservation(self) -> None:
        """Lexical tokens must preserve their original source spelling."""
        source = 'message 42 3.14 "hello" \'A\' == ;'

        tokens = Lexer(source).tokenize()

        self.assertEqual(
            [token.lexeme for token in tokens[:-1]],
            ["message", "42", "3.14", '"hello"', "'A'", "==", ";"],
        )

    def test_unterminated_string_raises_error(self) -> None:
        """An unterminated string literal must raise a lexer error."""
        with self.assertRaises(LexerError):
            Lexer('"unterminated').tokenize()

    def test_unterminated_char_raises_error(self) -> None:
        """An unterminated character literal must raise a lexer error."""
        with self.assertRaises(LexerError):
            Lexer("'A").tokenize()

    def test_empty_character_literal_raises_error(self) -> None:
        """An empty character literal must raise a lexer error."""
        with self.assertRaises(LexerError):
            Lexer("''").tokenize()

    def test_multi_character_literal_raises_error(self) -> None:
        """A character literal containing multiple raw characters must fail."""
        with self.assertRaises(LexerError):
            Lexer("'AB'").tokenize()

    def test_unterminated_escaped_character_literal_raises_error(self) -> None:
        """An escaped character without a closing quote must fail."""
        with self.assertRaises(LexerError):
            Lexer(r"'\n").tokenize()

    def test_unterminated_block_comment_raises_error(self) -> None:
        """An unterminated block comment must raise a lexer error."""
        with self.assertRaises(LexerError):
            Lexer("/* unterminated").tokenize()

    def test_unsupported_character_raises_error(self) -> None:
        """Unsupported characters must fail instead of being silently ignored."""
        with self.assertRaises(UnexpectedCharacterError):
            Lexer("@").tokenize()


if __name__ == "__main__":
    unittest.main()
