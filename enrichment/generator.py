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

        article.metadata.systems = (
            self.system_detector.detect(text)
        )

        #
        # Tags
        #

        article.metadata.tags = (
            self.tagger.generate(article)
        )

        #
        # References
        #

        article.metadata.references = (
            self.reference_detector.detect(article)
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
