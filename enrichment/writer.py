"""
BridgeLab Toolkit
Metadata Writer
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.models import Article
from enrichment.parser import MetadataParser


# ============================================================
# Metadata Writer
# ============================================================

@dataclass(slots=True)
class MetadataWriter:
    """
    Write metadata back to Markdown articles.
    """

    parser: MetadataParser = field(
        default_factory=MetadataParser,
    )

    # ========================================================

    def write(
        self,
        article: Article,
    ) -> bool:
        """
        Write metadata to one article.

        Returns True if the file was modified.
        """

        text = article.path.read_text(
            encoding="utf-8",
        )

        yaml = self.parser.serialize(
            article.metadata,
        )

        body = self._body(text)

        new_text = yaml + "\n\n" + body

        if new_text == text:
            return False

        article.path.write_text(
            new_text,
            encoding="utf-8",
        )

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

        updated = 0

        for article in articles:

            if self.write(article):
                updated += 1

        return updated

    # ========================================================

    def _body(
        self,
        text: str,
    ) -> str:
        """
        Remove YAML front matter and return the Markdown body.
        """

        text = text.lstrip()

        if not text.startswith("---"):
            return text

        lines = text.splitlines()

        delimiters = 0

        for index, line in enumerate(lines):

            if line.strip() == "---":

                delimiters += 1

                if delimiters == 2:

                    return "\n".join(
                        lines[index + 1:]
                    ).lstrip()

        return text
