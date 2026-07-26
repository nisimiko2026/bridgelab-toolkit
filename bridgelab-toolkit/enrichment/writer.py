"""
BridgeLab Toolkit
Metadata Writer
"""

from __future__ import annotations

from pathlib import Path

from core.models import Article
from enrichment.generator import MetadataGenerator


# ============================================================
# Metadata Writer
# ============================================================

class MetadataWriter:
    """
    Inserts YAML front matter into Markdown files.
    """

    def __init__(self) -> None:
        self.generator = MetadataGenerator()

    # --------------------------------------------------------

    def write(
        self,
        article: Article,
    ) -> bool:
        """
        Insert metadata into an article.

        Returns True if the file was modified.
        """

        text = article.path.read_text(encoding="utf-8")

        if self.generator.has_metadata(text):
            return False

        metadata = self.generator.generate(article)

        article.path.write_text(
            metadata + text,
            encoding="utf-8",
        )

        return True
