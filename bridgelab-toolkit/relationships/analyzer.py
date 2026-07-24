"""
BridgeLab Toolkit
Relationship Analyzer
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.models import Article


# ============================================================
# Relationship
# ============================================================

@dataclass(slots=True)
class Relationship:

    source: str

    target: str

    relation: str

    score: float = 1.0


# ============================================================
# Analyzer
# ============================================================

class RelationshipAnalyzer:
    """
    Discovers relationships between BridgeLab articles.
    """

    def analyze(
        self,
        articles: list[Article],
    ) -> list[Relationship]:

        relationships = []

        for article in articles:

            relationships.extend(

                self._analyze_article(
                    article,
                    articles,
                )

            )

        return relationships

    # --------------------------------------------------------

    def _analyze_article(

        self,

        article: Article,

        articles: list[Article],

    ) -> list[Relationship]:

        result = []

        # ------------------------------------------
        # Same Category
        # ------------------------------------------

        for other in articles:

            if other.id == article.id:
                continue

            if (
                article.category
                and article.category == other.category
            ):

                result.append(

                    Relationship(

                        source=article.id,

                        target=other.id,

                        relation="category",

                        score=0.60,

                    )

                )

        # ------------------------------------------
        # Same Subcategory
        # ------------------------------------------

        for other in articles:

            if other.id == article.id:
                continue

            if (
                article.subcategory
                and article.subcategory
                == other.subcategory
            ):

                result.append(

                    Relationship(

                        source=article.id,

                        target=other.id,

                        relation="subcategory",

                        score=0.80,

                    )

                )

        # ------------------------------------------
        # Shared Systems
        # ------------------------------------------

        for other in articles:

            if other.id == article.id:
                continue

            if not article.metadata.systems:
                continue

            shared = set(

                article.metadata.systems

            ).intersection(

                other.metadata.systems

            )

            if not shared:
                continue

            result.append(

                Relationship(

                    source=article.id,

                    target=other.id,

                    relation="system",

                    score=0.70,

                )

            )

        return result
