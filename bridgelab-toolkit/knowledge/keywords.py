"""
BridgeLab Toolkit
Keyword Engine
"""

from __future__ import annotations

from collections import Counter

from core.models import Entity
from core.models import Keyword


class KeywordEngine:
    """
    Builds a keyword index from extracted entities.
    """

    # =========================================================
    # Build
    # =========================================================

    def build(
        self,
        entities: list[Entity],
    ) -> list[Keyword]:

        counter = Counter()

        article_map = {}

        for entity in entities:

            words = entity.name.split()

            for word in words:

                keyword = word.lower()

                counter[keyword] += entity.frequency

                article_map.setdefault(

                    keyword,

                    entity.article,

                )

        keywords = []

        for word in sorted(counter):

            keywords.append(

                Keyword(

                    word=word,

                    article=article_map[word],

                    frequency=counter[word],

                )

            )

        return keywords
