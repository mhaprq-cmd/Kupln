"""Kupln Bootstrap Source Loader.

This module provides the first source-loading boundary of the Kupln
bootstrap infrastructure.

Responsibilities:
    - validate Kupln source paths
    - read .kpl source files as UTF-8
    - provide deterministic source-loading results
    - distinguish expected loading failures

This module intentionally does not perform:
    - source modeling
    - lexical analysis
    - parsing
    - semantic analysis
    - type checking
    - compilation
    - backend processing
"""

from __future__ import annotations

from pathlib import Path

from .source_model import SourceFile


KUPLN_SOURCE_EXTENSION = ".kpl"


class SourceLoadError(Exception):
    """Base class for expected source-loading failures."""


class InvalidSourcePathError(SourceLoadError):
    """Raised when the requested path is not a valid source-file path."""


class SourceFileNotFoundError(SourceLoadError):
    """Raised when the requested source file does not exist."""


class SourceFileUnreadableError(SourceLoadError):
    """Raised when the requested source file cannot be read."""


class InvalidSourceEncodingError(SourceLoadError):
    """Raised when the source file is not valid UTF-8."""


def load_source(path: str | Path) -> SourceFile:
    """Load a Kupln .kpl source file as UTF-8.

    Args:
        path: Path to the Kupln source file.

    Returns:
        A SourceFile containing the normalized Path and decoded source text.

    Raises:
        InvalidSourcePathError:
            If the path does not identify a .kpl source file.
        SourceFileNotFoundError:
            If the source file does not exist.
        SourceFileUnreadableError:
            If the source file cannot be read.
        InvalidSourceEncodingError:
            If the source file is not valid UTF-8.
    """

    source_path = Path(path)

    if source_path.suffix != KUPLN_SOURCE_EXTENSION:
        raise InvalidSourcePathError(
            f"Kupln source files must use the "
            f"'{KUPLN_SOURCE_EXTENSION}' extension: {source_path}"
        )

    if not source_path.is_file():
        if source_path.exists():
            raise InvalidSourcePathError(
                f"Kupln source path is not a file: {source_path}"
            )

        raise SourceFileNotFoundError(
            f"Kupln source file was not found: {source_path}"
        )

    try:
        content = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidSourceEncodingError(
            f"Kupln source file is not valid UTF-8: {source_path}"
        ) from exc
    except OSError as exc:
        raise SourceFileUnreadableError(
            f"Kupln source file could not be read: {source_path}"
        ) from exc

    return SourceFile(
        path=source_path.resolve(),
        content=content,
    )
