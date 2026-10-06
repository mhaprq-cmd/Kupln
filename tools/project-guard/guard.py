#!/usr/bin/env python3

"""
Kupln Project Guard
===================

The canonical validation engine for the Kupln repository.

This tool is intentionally dependency-free and uses only the Python
standard library.

Exit codes:
    0 = PASS
    1 = FAIL
"""

from __future__ import annotations

import fnmatch
import sys
from pathlib import Path


PROJECT_NAME = "Kupln"
README_FILE = "README.md"
GUARD_WORKFLOW = ".github/workflows/project-guard.yml"

FORBIDDEN_PATTERNS = (
    "*.apk",
    "*.aab",
    "*.class",
    "*.jar",
    "*.exe",
    "*.dll",
    "*.so",
    "*.o",
    "*.obj",
    "*.tmp",
    "*.log",
)


class Guard:
    """Central Project Guard validation engine."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.failed = False

    def fail(self, message: str) -> None:
        self.failed = True
        print(f"FAIL: {message}")

    def pass_check(self, message: str) -> None:
        print(f"PASS: {message}")

    def section(self, number: int, title: str) -> None:
        print()
        print(f"[{number}] {title}")

    def check_repository_root(self) -> None:
        self.section(1, "Repository root")

        git_directory = self.root / ".git"

        if git_directory.is_dir():
            self.pass_check("Git repository detected.")
        else:
            self.fail("Git repository metadata is missing.")

    def check_documentation(self) -> None:
        self.section(2, "Required documentation")

        readme = self.root / README_FILE

        if readme.is_file():
            self.pass_check("README.md exists.")
        else:
            self.fail("README.md is missing.")

    def check_project_identity(self) -> None:
        self.section(3, "Project identity")

        readme = self.root / README_FILE

        if not readme.is_file():
            self.fail("Cannot verify project identity because README.md is missing.")
            return

        try:
            content = readme.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.fail("README.md is not valid UTF-8 text.")
            return
        except OSError as exc:
            self.fail(f"README.md could not be read: {exc}")
            return

        if PROJECT_NAME.lower() in content.lower():
            self.pass_check("Kupln identity detected.")
        else:
            self.fail("README.md does not identify the Kupln project.")

    def check_forbidden_artifacts(self) -> None:
        self.section(4, "Generated and binary artifacts")

        found = []

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            if ".git" in path.parts:
                continue

            relative = path.relative_to(self.root).as_posix()

            for pattern in FORBIDDEN_PATTERNS:
                if fnmatch.fnmatch(path.name, pattern):
                    found.append(relative)
                    break

        if not found:
            self.pass_check("No forbidden generated artifacts detected.")
            return

        for item in sorted(found):
            self.fail(f"Unexpected generated/binary file detected: {item}")

    def check_guard_structure(self) -> None:
        self.section(5, "Project Guard structure")

        workflow_directory = self.root / ".github" / "workflows"
        workflow_file = self.root / GUARD_WORKFLOW

        if workflow_directory.is_dir():
            self.pass_check("GitHub Actions workflow directory exists.")
        else:
            self.fail(".github/workflows directory is missing.")

        if workflow_file.is_file():
            self.pass_check("Project Guard workflow exists.")
        else:
            self.fail("Project Guard workflow is missing.")

    def run(self) -> int:
        print("========================================")
        print("        Kupln Project Guard")
        print("========================================")

        self.check_repository_root()
        self.check_documentation()
        self.check_project_identity()
        self.check_forbidden_artifacts()
        self.check_guard_structure()

        print()
        print("[6] Final Guard decision")
        print()

        if self.failed:
            print("========================================")
            print("        PROJECT GUARD: FAIL")
            print("========================================")
            return 1

        print("========================================")
        print("        PROJECT GUARD: PASS")
        print("========================================")
        print()
        print("Repository foundation is valid.")

        return 0


def find_repository_root() -> Path:
    """
    Determine the repository root from this file's location.

    Current structure:
        repository/
        ├── README.md
        ├── .github/
        │   └── workflows/
        │       └── project-guard.yml
        └── tools/
            └── project-guard/
                └── guard.py
    """

    current_file = Path(__file__).resolve()

    return current_file.parents[2]


def main() -> int:
    root = find_repository_root()

    guard = Guard(root)

    return guard.run()


if __name__ == "__main__":
    sys.exit(main())
