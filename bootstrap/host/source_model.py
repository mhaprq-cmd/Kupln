"""Kupln Bootstrap Source Model.

This module defines the source representation used by the Kupln
bootstrap infrastructure after source loading.

Responsibilities:
    - represent a loaded Kupln source unit
    - preserve the normalized source path
    - preserve the complete decoded source text
    - provide stable source identity information
    - provide basic source-size information

This module intentionally does not perform:
    - file-system loading
    - lexical analysis
    - parsing
    - semantic analysis
    - type checking
    - compilation
    - backend processing
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    """Immutable representation of a loaded Kupln source file."""

    path: Path
    content: str

    @property
    def name(self) -> str:
        """Return the source file name."""
        return self.path.name

    @property
    def size(self) -> int:
        """Return the source size in Unicode code points."""
        return len(self.content)

    @property
    def line_count(self) -> int:
        """Return the number of logical source lines.

        An empty source has zero lines.
        A non-empty source always has at least one line.
        """
        if not self.content:
            return 0

        return self.content.count("\n") + 1
