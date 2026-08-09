"""
BridgeLab Toolkit
Coverage Analysis
"""

from __future__ import annotations

from dataclasses import dataclass

from analysis.graph import KnowledgeGraph
from core.models import Article


# ============================================================
# Coverage Analyzer
# ============================================================

@dataclass(slots=True)
class CoverageAnalyzer:
    """
    Analyze metadata coverage across the repository.
    """

    graph: KnowledgeGraph

    # ========================================================

    def missing_category(self) -> list[Article]:

        return [
            article
            for article in self.graph.articles
            if not article.metadata.category
        ]

    # ========================================================

    def missing_systems(self) -> list[Article]:

        return [
            article
            for article in self.graph.articles
            if not article.metadata.systems
        ]

    # ========================================================

    def missing_tags(self) -> list[Article]:

        return [
            article
            for article in self.graph.articles
            if not article.metadata.tags
        ]

    # ========================================================

    def missing_references(self) -> list[Article]:

        return [
            article
            for article in self.graph.articles
            if not article.metadata.references
        ]

    # ========================================================

    def missing_description(self) -> list[Article]:

        return [
            article
            for article in self.graph.articles
            if not article.metadata.description
        ]

    # ========================================================

    def summary(self) -> dict[str, int]:

        return {
            "Articles": len(self.graph.articles),
            "Missing Categories": len(
                self.missing_category()
            ),
            "Missing Systems": len(
                self.missing_systems()
            ),
            "Missing Tags": len(
                self.missing_tags()
            ),
            "Missing References": len(
                self.missing_references()
            ),
            "Missing Descriptions": len(
                self.missing_description()
            ),
        }
