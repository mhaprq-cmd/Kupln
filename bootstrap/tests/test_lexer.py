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

    def test_unicode_identifier(self) -> None:
        """Unicode identifiers must be preserved by the lexer."""
        tokens = Lexer("let رسالة = 10").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[1].kind, TokenKind.IDENTIFIER)
        self.assertEqual(tokens[1].lexeme, "رسالة")

    def test_integer_and_float_literals(self) -> None:
        """Integer and decimal floating-point literals must be classified."""
        tokens = Lexer("42 3.14").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.INTEGER)
        self.assertEqual(tokens[0].lexeme, "42")

        self.assertEqual(tokens[1].kind, TokenKind.FLOAT)
        self.assertEqual(tokens[1].lexeme, "3.14")

    def test_string_literal(self) -> None:
        """String literals must preserve their original lexeme."""
        tokens = Lexer('"hello Kupln"').tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.STRING)
        self.assertEqual(tokens[0].lexeme, '"hello Kupln"')

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

    def test_line_comment(self) -> None:
        """Line comments must be emitted as comment tokens."""
        tokens = Lexer("// hello\nlet value = 1").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.COMMENT)
        self.assertEqual(tokens[0].lexeme, "// hello")

        self.assertEqual(tokens[1].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[1].lexeme, "let")

    def test_block_comment(self) -> None:
        """Block comments must be emitted as comment tokens."""
        tokens = Lexer("/* hello */ let").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.COMMENT)
        self.assertEqual(tokens[0].lexeme, "/* hello */")

        self.assertEqual(tokens[1].kind, TokenKind.KEYWORD)
        self.assertEqual(tokens[1].lexeme, "let")

    def test_eof_token(self) -> None:
        """Every successful tokenization must end with an explicit EOF token."""
        tokens = Lexer("").tokenize()

        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].kind, TokenKind.EOF)
        self.assertEqual(tokens[0].lexeme, "")

    def test_source_positions(self) -> None:
        """Token positions must track line, column, and offset."""
        tokens = Lexer("let\nvalue").tokenize()

        self.assertEqual(tokens[0].position.line, 1)
        self.assertEqual(tokens[0].position.column, 1)
        self.assertEqual(tokens[0].position.offset, 0)

        self.assertEqual(tokens[1].position.line, 2)
        self.assertEqual(tokens[1].position.column, 1)
        self.assertEqual(tokens[1].position.offset, 4)

    def test_reserved_keyword_boundary(self) -> None:
        """Keyword lookup must not classify longer identifiers as keywords."""
        self.assertTrue(is_reserved_keyword("let"))
        self.assertFalse(is_reserved_keyword("letter"))

        tokens = Lexer("letter").tokenize()

        self.assertEqual(tokens[0].kind, TokenKind.IDENTIFIER)
        self.assertEqual(tokens[0].lexeme, "letter")

    def test_unterminated_string_raises_error(self) -> None:
        """An unterminated string literal must raise a lexer error."""
        with self.assertRaises(LexerError):
            Lexer('"unterminated').tokenize()

    def test_unterminated_char_raises_error(self) -> None:
        """An unterminated character literal must raise a lexer error."""
        with self.assertRaises(LexerError):
            Lexer("'A").tokenize()

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
