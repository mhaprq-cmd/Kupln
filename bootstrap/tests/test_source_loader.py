"""Tests for the Kupln bootstrap source loader."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bootstrap.host.source_loader import (
    InvalidSourceEncodingError,
    InvalidSourcePathError,
    SourceFileNotFoundError,
    load_source,
)


class SourceLoaderTests(unittest.TestCase):
    """Validate the Kupln bootstrap source-loading boundary."""

    def test_load_valid_kpl_source(self) -> None:
        """A valid .kpl file must load into a SourceFile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "hello.kpl"
            content = "let message = \"مرحبا Kupln\"\nlet value = 42\n"
            path.write_text(content, encoding="utf-8")

            source = load_source(path)

            self.assertEqual(source.path, path.resolve())
            self.assertEqual(source.content, content)
            self.assertEqual(source.name, "hello.kpl")
            self.assertEqual(source.size, len(content))
            self.assertEqual(source.line_count, 3)

    def test_empty_source_has_zero_lines(self) -> None:
        """An empty source file must report zero lines."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "empty.kpl"
            path.write_text("", encoding="utf-8")

            source = load_source(path)

            self.assertEqual(source.content, "")
            self.assertEqual(source.size, 0)
            self.assertEqual(source.line_count, 0)

    def test_single_line_source_has_one_line(self) -> None:
        """A non-empty source without a newline has one line."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "single.kpl"
            path.write_text("let value = 1", encoding="utf-8")

            source = load_source(path)

            self.assertEqual(source.line_count, 1)

    def test_invalid_extension_is_rejected(self) -> None:
        """Non-.kpl files must be rejected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.txt"
            path.write_text("let value = 1", encoding="utf-8")

            with self.assertRaises(InvalidSourcePathError):
                load_source(path)

    def test_missing_source_file_is_rejected(self) -> None:
        """A missing .kpl file must raise the expected error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.kpl"

            with self.assertRaises(SourceFileNotFoundError):
                load_source(path)

    def test_directory_with_kpl_suffix_is_rejected(self) -> None:
        """A directory must not be accepted as a source file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "directory.kpl"
            path.mkdir()

            with self.assertRaises(InvalidSourcePathError):
                load_source(path)

    def test_invalid_utf8_is_rejected(self) -> None:
        """Invalid UTF-8 source data must raise the expected error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.kpl"
            path.write_bytes(b"\xff\xfe\xfa")

            with self.assertRaises(InvalidSourceEncodingError):
                load_source(path)


if __name__ == "__main__":
    unittest.main()
