"""
BridgeLab Toolkit
Repository Scanner

Scans the BridgeLab repository and returns all Markdown articles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .models import Article


# ---------------------------------------------------------------------
# Directories to ignore
# ---------------------------------------------------------------------

IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
}


# ---------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------

class RepositoryScanner:
    """
    Recursively scans a BridgeLab repository.

    Example

        scanner = RepositoryScanner(root)

        articles = scanner.scan()
    """

    def __init__(self, root: Path):

        self.root = root.resolve()

    # ---------------------------------------------------------

    def scan(self) -> list[Article]:

        articles: list[Article] = []

        for md_file in self._markdown_files(self.root):

            relative = md_file.relative_to(self.root)

            directory = (
                relative.parent.as_posix()
                if relative.parent != Path(".")
                else ""
            )

            article = Article(

                id=self._make_id(relative),

                filename=md_file.name,

                path=md_file,

                relative_path=relative,

                directory=directory,

            )

            articles.append(article)

        articles.sort(key=lambda a: a.relative_path.as_posix())

        return articles

    # ---------------------------------------------------------

    def _markdown_files(self, directory: Path) -> Iterator[Path]:

        for entry in directory.iterdir():

            if entry.is_dir():

                if entry.name in IGNORE_DIRS:
                    continue

                yield from self._markdown_files(entry)

                continue

            if entry.suffix.lower() != ".md":
                continue

            yield entry

    # ---------------------------------------------------------

    @staticmethod
    def _make_id(relative_path: Path) -> str:
        """
        Example

            conventions/doubles/negative-double.md

        becomes

            conventions/doubles/negative-double
        """

        return relative_path.with_suffix("").as_posix()
