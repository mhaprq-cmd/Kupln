"""Kupln Bootstrap Lexer.

This module provides the first lexical scanner for Kupln source text.

Responsibilities:
    - scan source text character by character
    - recognize identifiers and reserved keywords
    - recognize integer and floating-point literals
    - recognize punctuation and operators
    - track stable source positions
    - emit an explicit EOF token

This module intentionally does not perform:
    - parsing
    - semantic analysis
    - type checking
    - compilation
    - backend processing
"""

from __future__ import annotations

from .keywords import is_reserved_keyword
from .token import SourcePosition, Token, TokenKind


_WHITESPACE = frozenset({" ", "\t", "\r", "\n"})

_PUNCTUATION = frozenset(
    {
        "(",
        ")",
        "{",
        "}",
        "[",
        "]",
        ",",
        ".",
        ":",
        ";",
    }
)

_OPERATOR_START = frozenset(
    {
        "+",
        "-",
        "*",
        "/",
        "%",
        "=",
        "!",
        "<",
        ">",
        "&",
        "|",
        "^",
        "?",
    }
)


class LexerError(Exception):
    """Base class for expected lexical errors."""


class UnexpectedCharacterError(LexerError):
    """Raised when the lexer encounters an unsupported character."""


class Lexer:
    """Lexical scanner for Kupln source text."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        """Tokenize the complete source and return all tokens."""

        tokens: list[Token] = []

        while not self._at_end():
            self._skip_whitespace()

            if self._at_end():
                break

            tokens.append(self._scan_token())

        tokens.append(
            Token(
                kind=TokenKind.EOF,
                lexeme="",
                position=self._position(),
            )
        )

        return tokens

    def _scan_token(self) -> Token:
        character = self._peek()

        if character == "/" and self._peek_next() == "/":
            return self._scan_line_comment()

        if character == "/" and self._peek_next() == "*":
            return self._scan_block_comment()

        if self._is_identifier_start(character):
            return self._scan_identifier()

        if character.isdigit():
            return self._scan_number()

        if character == '"':
            return self._scan_string()

        if character == "'":
            return self._scan_char()

        if character in _PUNCTUATION:
            return self._scan_punctuation()

        if character in _OPERATOR_START:
            return self._scan_operator()

        position = self._position()
        raise UnexpectedCharacterError(
            f"Unexpected character {character!r} "
            f"at {position.line}:{position.column}."
        )

    def _scan_identifier(self) -> Token:
        position = self._position()
        start = self.index

        self._advance()

        while not self._at_end() and self._is_identifier_continue(self._peek()):
            self._advance()

        lexeme = self.source[start:self.index]

        kind = (
            TokenKind.KEYWORD
            if is_reserved_keyword(lexeme)
            else TokenKind.IDENTIFIER
        )

        return Token(
            kind=kind,
            lexeme=lexeme,
            position=position,
        )

    def _scan_number(self) -> Token:
        position = self._position()
        start = self.index

        while not self._at_end() and self._peek().isdigit():
            self._advance()

        kind = TokenKind.INTEGER

        if (
            not self._at_end()
            and self._peek() == "."
            and self._peek_next().isdigit()
        ):
            kind = TokenKind.FLOAT
            self._advance()

            while not self._at_end() and self._peek().isdigit():
                self._advance()

        return Token(
            kind=kind,
            lexeme=self.source[start:self.index],
            position=position,
        )

    def _scan_string(self) -> Token:
        position = self._position()
        start = self.index

        self._advance()

        while not self._at_end():
            character = self._peek()

            if character == '"':
                self._advance()

                return Token(
                    kind=TokenKind.STRING,
                    lexeme=self.source[start:self.index],
                    position=position,
                )

            if character == "\\":
                self._advance()

                if not self._at_end():
                    self._advance()

                continue

            self._advance()

        raise LexerError(
            f"Unterminated string literal "
            f"at {position.line}:{position.column}."
        )

    def _scan_char(self) -> Token:
        position = self._position()
        start = self.index

        self._advance()

        if self._at_end():
            raise LexerError(
                f"Unterminated character literal "
                f"at {position.line}:{position.column}."
            )

        if self._peek() == "\\":
            self._advance()

            if self._at_end():
                raise LexerError(
                    f"Unterminated character literal "
                    f"at {position.line}:{position.column}."
                )

            self._advance()
        else:
            self._advance()

        if self._at_end() or self._peek() != "'":
            raise LexerError(
                f"Invalid character literal "
                f"at {position.line}:{position.column}."
            )

        self._advance()

        return Token(
            kind=TokenKind.CHAR,
            lexeme=self.source[start:self.index],
            position=position,
        )

    def _scan_punctuation(self) -> Token:
        position = self._position()
        character = self._advance()

        return Token(
            kind=TokenKind.PUNCTUATION,
            lexeme=character,
            position=position,
        )

    def _scan_operator(self) -> Token:
        position = self._position()
        start = self.index

        first = self._advance()

        if self._at_end():
            return Token(
                kind=TokenKind.OPERATOR,
                lexeme=first,
                position=position,
            )

        second = self._peek()

        if first in {"=", "!", "<", ">"} and second == "=":
            self._advance()
        elif first in {"+", "-", "&", "|"} and second == first:
            self._advance()
        elif first == "-" and second == ">":
            self._advance()
        elif first == "?" and second == "?":
            self._advance()

        return Token(
            kind=TokenKind.OPERATOR,
            lexeme=self.source[start:self.index],
            position=position,
        )

    def _scan_line_comment(self) -> Token:
        position = self._position()
        start = self.index

        self._advance()
        self._advance()

        while not self._at_end() and self._peek() != "\n":
            self._advance()

        return Token(
            kind=TokenKind.COMMENT,
            lexeme=self.source[start:self.index],
            position=position,
        )

    def _scan_block_comment(self) -> Token:
        position = self._position()
        start = self.index

        self._advance()
        self._advance()

        while not self._at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()

                return Token(
                    kind=TokenKind.COMMENT,
                    lexeme=self.source[start:self.index],
                    position=position,
                )

            self._advance()

        raise LexerError(
            f"Unterminated block comment "
            f"at {position.line}:{position.column}."
        )

    def _skip_whitespace(self) -> None:
        while not self._at_end() and self._peek() in _WHITESPACE:
            self._advance()

    def _is_identifier_start(self, character: str) -> bool:
        return character == "_" or character.isalpha()

    def _is_identifier_continue(self, character: str) -> bool:
        return character == "_" or character.isalnum()

    def _peek(self) -> str:
        if self._at_end():
            return "\0"

        return self.source[self.index]

    def _peek_next(self) -> str:
        next_index = self.index + 1

        if next_index >= len(self.source):
            return "\0"

        return self.source[next_index]

    def _advance(self) -> str:
        character = self.source[self.index]
        self.index += 1

        if character == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return character

    def _position(self) -> SourcePosition:
        return SourcePosition(
            line=self.line,
            column=self.column,
            offset=self.index,
        )

    def _at_end(self) -> bool:
        return self.index >= len(self.source)
