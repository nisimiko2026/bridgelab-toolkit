"""
BridgeLab Toolkit
Learning Path Analysis
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from analysis.graph import KnowledgeGraph
from core.models import Article


# ============================================================
# Learning Path Analyzer
# ============================================================

@dataclass(slots=True)
class LearningPathAnalyzer:
    """
    Generate learning paths through the knowledge graph.
    """

    graph: KnowledgeGraph

    # ========================================================

    def path(
        self,
        start: Article,
    ) -> list[Article]:
        """
        Return a breadth-first learning path beginning at an article.
        """

        visited: set[str] = set()

        queue: deque[str] = deque([start.id])

        result: list[Article] = []

        while queue:

            article_id = queue.popleft()

            if article_id in visited:
                continue

            visited.add(article_id)

            article = self.graph.article(article_id)

            if article is None:
                continue

            result.append(article)

            #
            # Follow outgoing references.
            #

            for target in sorted(
                self.graph.outgoing(article)
            ):

                if target not in visited:
                    queue.append(target)

        return result

    # ========================================================

    def prerequisites(
        self,
        article: Article,
    ) -> list[Article]:
        """
        Articles that reference this article.
        """

        result: list[Article] = []

        for article_id in sorted(
            self.graph.incoming(article)
        ):

            target = self.graph.article(article_id)

            if target is not None:
                result.append(target)

        return result

    # ========================================================

    def next_topics(
        self,
        article: Article,
    ) -> list[Article]:
        """
        Articles referenced by this article.
        """

        result: list[Article] = []

        for article_id in sorted(
            self.graph.outgoing(article)
        ):

            target = self.graph.article(article_id)

            if target is not None:
                result.append(target)

        return result
