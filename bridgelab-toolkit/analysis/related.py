"""
BridgeLab Toolkit
Related Article Analysis
"""

from __future__ import annotations

from dataclasses import dataclass

from analysis.graph import KnowledgeGraph
from core.models import Article


# ============================================================
# Related Analyzer
# ============================================================

@dataclass(slots=True)
class RelatedAnalyzer:
    """
    Find articles related to another article.
    """

    graph: KnowledgeGraph

    # ========================================================

    def related(
        self,
        article: Article,
        limit: int = 10,
    ) -> list[tuple[Article, int]]:
        """
        Return the most closely related articles and their scores.
        """

        scores: list[tuple[int, Article]] = []

        for candidate in self.graph.articles:

            if candidate.id == article.id:
                continue

            score = self._score(
                article,
                candidate,
            )

            if score > 0:
                scores.append(
                    (score, candidate)
                )

        scores.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            (article, score)
            for score, article in scores[:limit]
        ]

    # ========================================================

    def _score(
        self,
        left: Article,
        right: Article,
    ) -> int:
        """
        Compute a similarity score.
        """

        score = 0

        #
        # Same category
        #

        if (
            left.metadata.category
            and left.metadata.category
            == right.metadata.category
        ):
            score += 5

        #
        # Same systems
        #

        score += (
            len(
                set(left.metadata.systems)
                & set(right.metadata.systems)
            )
            * 4
        )

        #
        # Shared tags
        #

        score += (
            len(
                set(left.metadata.tags)
                & set(right.metadata.tags)
            )
            * 2
        )

        #
        # Direct references
        #

        if right.id in self.graph.outgoing(left):
            score += 10

        if left.id in self.graph.outgoing(right):
            score += 10

        #
        # Shared neighbours
        #

        score += len(
            self.graph.neighbours(left)
            & self.graph.neighbours(right)
        )

        return score
