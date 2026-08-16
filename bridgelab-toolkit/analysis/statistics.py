"""
BridgeLab Toolkit
Repository Statistics
"""

from __future__ import annotations

from dataclasses import dataclass

from analysis.graph import KnowledgeGraph


# ============================================================
# Repository Statistics
# ============================================================

@dataclass(slots=True)
class RepositoryStatistics:
    """
    Calculate repository statistics.
    """

    graph: KnowledgeGraph

    # ========================================================

    def article_count(self) -> int:
        return len(self.graph.articles)

    # ========================================================

    def category_count(self) -> int:
        return len(self.graph.by_category)

    # ========================================================

    def system_count(self) -> int:
        return len(self.graph.by_system)

    # ========================================================

    def tag_count(self) -> int:
        return len(self.graph.by_tag)

    # ========================================================

    def reference_count(self) -> int:
        """
        Total outgoing references.
        """

        return sum(
            len(self.graph.outgoing(article))
            for article in self.graph.articles
        )

    # ========================================================

    def orphan_count(self) -> int:
        return len(
            self.graph.orphan_articles()
        )

    # ========================================================

    def average_references(self) -> float:

        articles = self.article_count()

        if articles == 0:
            return 0.0

        return (
            self.reference_count()
            / articles
        )

    # ========================================================

    def summary(self) -> dict[str, int | float]:

        return {
            "Articles": self.article_count(),
            "Categories": self.category_count(),
            "Systems": self.system_count(),
            "Tags": self.tag_count(),
            "References": self.reference_count(),
            "Orphans": self.orphan_count(),
            "Average References": round(
                self.average_references(),
                2,
            ),
        }
