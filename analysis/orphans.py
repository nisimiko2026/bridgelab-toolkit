"""
BridgeLab Toolkit
Orphan Analysis
"""

from __future__ import annotations

from dataclasses import dataclass

from core.models import Article

from .graph import KnowledgeGraph


# ============================================================
# Orphan Analyzer
# ============================================================

@dataclass(slots=True)
class OrphanAnalyzer:
    """
    Analyze orphan articles.
    """

    graph: KnowledgeGraph

    # ========================================================

    def articles(self) -> list[Article]:
        """
        Return all orphan articles.
        """

        return self.graph.orphan_articles()

    # ========================================================

    def count(self) -> int:
        """
        Number of orphan articles.
        """

        return len(self.articles())

    # ========================================================

    def by_category(
        self,
    ) -> dict[str, list[Article]]:
        """
        Group orphan articles by category.
        """

        result: dict[str, list[Article]] = {}

        for article in self.articles():

            category = article.metadata.category or "Uncategorized"

            result.setdefault(category, []).append(article)

        return dict(sorted(result.items()))

    # ========================================================

    def summary(
        self,
    ) -> dict[str, int]:
        """
        Number of orphan articles per category.
        """

        return {
            category: len(articles)
            for category, articles
            in self.by_category().items()
        }

    # ========================================================

    def report(self) -> list[str]:
        """
        Human-readable orphan report.
        """

        lines: list[str] = []

        lines.append(
            f"Total orphan articles: {self.count()}"
        )

        lines.append("")

        for category, articles in self.by_category().items():

            lines.append(
                f"{category} ({len(articles)})"
            )

            for article in sorted(
                articles,
                key=lambda a: a.relative_path.as_posix(),
            ):
                lines.append(
                    f"  - {article.relative_path.as_posix()}"
                )

            lines.append("")

        return lines
