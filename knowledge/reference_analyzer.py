"""
BridgeLab Toolkit
Reference Analyzer
"""

from __future__ import annotations

from collections import defaultdict

from core.models import Article


class ReferenceAnalyzer:
    """
    Analyzes bibliography references.
    """

    # =========================================================
    # Analyze
    # =========================================================

    def analyze(
        self,
        articles: list[Article],
    ) -> dict[str, list[str]]:

        references = defaultdict(list)

        for article in articles:

            for reference in article.metadata.references:

                reference = reference.strip()

                if not reference:

                    continue

                references[reference].append(

                    article.id

                )

        return dict(

            sorted(

                references.items(),

                key=lambda item: item[0].lower(),

            )

        )
