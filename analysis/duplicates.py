"""
BridgeLab Toolkit
Duplicate Analysis
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.models import Article
from .graph import KnowledgeGraph


# ============================================================
# Duplicate Analyzer
# ============================================================

@dataclass(slots=True)
class DuplicateAnalyzer:
    """
    Detect duplicate articles.
    """

    graph: KnowledgeGraph

    duplicates: dict[str, list[Article]] = field(
        init=False,
        default_factory=dict,
    )

    # ========================================================

    def analyze(self) -> dict[str, list[Article]]:
        """
        Find duplicate article titles.
        """

        groups: dict[str, list[Article]] = {}

        for article in self.graph.articles:

            title = (
                article.metadata.title
                or article.filename.replace(".md", "")
            )

            key = self._normalize(title)

            groups.setdefault(key, []).append(article)

        self.duplicates = {
            key: articles
            for key, articles in groups.items()
            if len(articles) > 1
        }

        return self.duplicates

    # ========================================================

    def count(self) -> int:
        """
        Number of duplicate groups.
        """

        return len(self.analyze())

    # ========================================================

    def report(self) -> list[str]:
        """
        Human-readable report.
        """

        lines: list[str] = []

        duplicates = self.analyze()

        lines.append(
            f"Duplicate groups: {len(duplicates)}"
        )

        lines.append("")

        for key in sorted(duplicates):

            articles = duplicates[key]

            lines.append(
                f"{articles[0].metadata.title} ({len(articles)})"
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

    # ========================================================

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        """
        Normalize a title for comparison.
        """

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9]+",
            " ",
            text,
        )

        return " ".join(text.split())
