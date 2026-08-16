"""
BridgeLab Toolkit
Metadata Writer
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from core.models import Article, Metadata


# ============================================================
# Metadata Writer
# ============================================================

@dataclass(slots=True)
class MetadataWriter:
    """
    Write metadata back to Markdown articles.
    """

    skipped: list[tuple[Article, str]] = field(
        init=False,
        default_factory=list,
    )

    FRONT_MATTER_RE = re.compile(
        r"\A---[ \t]*(?:\r\n|\n)(?:(.*?)(?:\r\n|\n))?---[ \t]*(?:\r\n|\n)",
        re.DOTALL,
    )

    # ========================================================

    def preview(
        self,
        article: Article,
    ) -> bool:
        """
        Determine whether one article would be modified.

        Returns True if metadata differs. Malformed YAML is skipped.
        """

        prepared = self._prepare(article)

        if prepared is None:
            return False

        text, new_text = prepared

        return new_text != text

    # ========================================================

    def preview_all(
        self,
        articles: list[Article],
    ) -> int:
        """
        Return the number of articles that would be modified.
        """

        self.skipped.clear()

        return sum(
            self.preview(article)
            for article in articles
        )

    # ========================================================

    def write(
        self,
        article: Article,
    ) -> bool:
        """
        Atomically write metadata to one article.

        Returns True if the file was modified. Malformed YAML is skipped.
        """

        prepared = self._prepare(article)

        if prepared is None:
            return False

        text, new_text = prepared

        if new_text == text:
            return False

        self._atomic_write(article, new_text)

        return True

    # ========================================================

    def write_all(
        self,
        articles: list[Article],
    ) -> int:
        """
        Write all articles.

        Returns the number of updated files.
        """

        self.skipped.clear()

        updated = 0

        for article in articles:

            if self.write(article):
                updated += 1

        return updated

    # ========================================================

    def _prepare(
        self,
        article: Article,
    ) -> tuple[str, str] | None:
        """
        Build rewritten content while preserving the original Markdown body.
        """

        # newline="" prevents Python from translating the Markdown body
        # while it is carried through the front-matter replacement.
        with article.path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as source:
            text = source.read()

        if article.metadata_error:
            self._skip(article, article.metadata_error)
            return None

        existing, body = self._existing_metadata(article, text)

        if existing is None:
            return None

        metadata = self._merge_metadata(existing, article.metadata)

        return text, self._serialize(metadata) + body

    # ========================================================

    def _existing_metadata(
        self,
        article: Article,
        text: str,
    ) -> tuple[dict[object, object] | None, str]:
        """
        Parse existing front matter and retain the body byte-for-byte.
        """

        if text.startswith("\ufeff---"):
            self._skip(
                article,
                "UTF-8 BOM before YAML front matter; article was not modified",
            )
            return None, ""

        if not text.startswith("---"):
            return {}, text

        match = self.FRONT_MATTER_RE.match(text)

        if not match:
            self._skip(
                article,
                "Malformed YAML front matter: missing closing delimiter",
            )
            return None, ""

        try:
            data = yaml.safe_load(match.group(1) or "")
        except yaml.YAMLError as error:
            self._skip(article, f"Malformed YAML front matter: {error}")
            return None, ""

        if data is None:
            data = {}

        if not isinstance(data, dict):
            self._skip(
                article,
                "Malformed YAML front matter: expected a mapping",
            )
            return None, ""

        return data, text[match.end():]

    # ========================================================

    @staticmethod
    def _merge_metadata(
        existing: dict[object, object],
        metadata: Metadata,
    ) -> dict[object, object]:
        """
        Put known metadata first while retaining unknown existing fields.
        """

        merged: dict[object, object] = dict(asdict(metadata))

        for key, value in existing.items():
            if key not in merged:
                merged[key] = value

        return merged

    # ========================================================

    @staticmethod
    def _serialize(metadata: dict[object, object]) -> str:
        """
        Serialize front matter with deterministic known-field ordering.
        """

        return (
            "---\n"
            + yaml.safe_dump(
                metadata,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
            + "---\n"
        )

    # ========================================================

    def _skip(
        self,
        article: Article,
        message: str,
    ) -> None:
        entry = (article, message)

        if entry not in self.skipped:
            self.skipped.append(entry)

    # ========================================================

    @staticmethod
    def _atomic_write(
        article: Article,
        content: str,
    ) -> None:
        """
        Replace the original only after a complete temporary write succeeds.
        """

        temporary_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=article.path.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                temporary_file.write(content)

            os.replace(temporary_path, article.path)
        except OSError:
            if temporary_path:
                Path(temporary_path).unlink(missing_ok=True)

            raise
