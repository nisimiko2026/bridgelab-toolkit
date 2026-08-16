"""
BridgeLab Toolkit
Metadata Generator
"""

from __future__ import annotations

from dataclasses import dataclass

from core.models import Article

from enrichment.reference_detector import ReferenceDetector
from enrichment.system_detector import SystemDetector
from enrichment.tagger import TagGenerator


# ============================================================
# Metadata Generator
# ============================================================

@dataclass(slots=True)
class MetadataGenerator:
    """
    Generate metadata for repository articles.
    """

    tagger: TagGenerator
    system_detector: SystemDetector
    reference_detector: ReferenceDetector

    # ========================================================

    @staticmethod
    def _merge_values(
        existing: list[str],
        generated: list[str],
    ) -> list[str]:
        """
        Preserve curated values while adding generated values.
        """

        return sorted(
            {
                value.strip()
                for value in [*existing, *generated]
                if value.strip()
            },
            key=str.lower,
        )

    # ========================================================

    def enrich(
        self,
        article: Article,
    ) -> None:
        """
        Enrich one article.
        """

        #
        # Read markdown once
        #

        try:
            text = article.path.read_text(
                encoding="utf-8",
            )

        except OSError:
            return

        #
        # Systems
        #

        article.metadata.systems = self._merge_values(
            article.metadata.systems,
            self.system_detector.detect(text),
        )

        #
        # Tags
        #

        article.metadata.tags = self._merge_values(
            article.metadata.tags,
            self.tagger.generate(article),
        )

        #
        # References
        #

        article.metadata.references = self._merge_values(
            article.metadata.references,
            self.reference_detector.detect(article),
        )

    # ========================================================

    def enrich_all(
        self,
        articles: list[Article],
    ) -> None:
        """
        Enrich all articles.
        """

        for article in articles:
            self.enrich(article)
