"""
BridgeLab Toolkit
Entity Extractor
"""

from __future__ import annotations

from collections import Counter

from core.models import (
    Article,
    Entity,
)


class EntityExtractor:
    """
    Extracts knowledge entities from articles.
    """

    # =========================================================
    # Extract
    # =========================================================

    def extract(
        self,
        articles: list[Article],
    ) -> list[Entity]:

        entities: list[Entity] = []

        for article in articles:

            entities.extend(

                self._extract_article(
                    article
                )

            )

        return entities

    # =========================================================
    # Article
    # =========================================================

    def _extract_article(
        self,
        article: Article,
    ) -> list[Entity]:

        counter = Counter()

        # ---------------------------------------------
        # Title
        # ---------------------------------------------

        if article.metadata.title:

            counter[
                article.metadata.title
            ] += 1

        # ---------------------------------------------
        # Aliases
        # ---------------------------------------------

        for alias in article.metadata.aliases:

            counter[alias] += 1

        # ---------------------------------------------
        # Acronyms
        # ---------------------------------------------

        for acronym in article.metadata.acronyms:

            counter[acronym] += 1

        # ---------------------------------------------
        # Systems
        # ---------------------------------------------

        for system in article.metadata.systems:

            counter[system] += 1

        entities = []

        for name, frequency in counter.items():

            entities.append(

                Entity(

                    name=name,

                    category="Knowledge",

                    article=article.id,

                    frequency=frequency,

                )

            )

        return entities
