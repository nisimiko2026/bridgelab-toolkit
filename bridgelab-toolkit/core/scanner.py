"""
BridgeLab Toolkit
Repository Scanner

Scans the BridgeLab repository and returns all Markdown articles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .models import Article


# ============================================================
# Directories to ignore
# ============================================================

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


# ============================================================
# Repository Scanner
# ============================================================

class RepositoryScanner:
    """
    Recursively scan a BridgeLab repository.
    """

    def __init__(
        self,
        root: Path,
    ) -> None:

        self.root = root.resolve()

    # ========================================================

    def scan(
        self,
    ) -> list[Article]:

        print(f"Repository root : {self.root}")
        print(f"Exists          : {self.root.exists()}")

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

        articles.sort(
            key=lambda article: article.relative_path.as_posix()
        )

        return articles

    # ========================================================

    def _markdown_files(
        self,
        directory: Path,
    ) -> Iterator[Path]:

        print(f"Scanning directory: {directory}")

        if not directory.exists():
            raise FileNotFoundError(
                f"Directory does not exist: {directory}"
            )

        for entry in directory.iterdir():

            if entry.is_dir():

                if entry.name in IGNORE_DIRS:
                    continue

                yield from self._markdown_files(entry)
                continue

            if entry.suffix.lower() != ".md":
                continue

            yield entry

    # ========================================================

    @staticmethod
    def _make_id(
        relative_path: Path,
    ) -> str:
        """
        Convert

            conventions/doubles/negative-double.md

        into

            conventions/doubles/negative-double
        """

        return relative_path.with_suffix("").as_posix()
