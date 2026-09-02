"""
BridgeLab Toolkit
Relationship Graph
"""

from __future__ import annotations

from collections import defaultdict

from core.models import Relationship


class RelationshipGraph:
    """
    Stores all relationships between BridgeLab articles.
    """

    def __init__(self):

        self._outgoing = defaultdict(list)

        self._incoming = defaultdict(list)

    # ---------------------------------------------------------

    def add(
        self,
        relationship: Relationship,
    ):

        self._outgoing[
            relationship.source
        ].append(relationship)

        self._incoming[
            relationship.target
        ].append(relationship)

    # ---------------------------------------------------------

    def build(
        self,
        relationships: list[Relationship],
    ):

        self.clear()

        for relationship in relationships:

            self.add(relationship)

    # ---------------------------------------------------------

    def outgoing(
        self,
        article_id: str,
    ) -> list[Relationship]:

        return self._outgoing.get(
            article_id,
            []
        )

    # ---------------------------------------------------------

    def incoming(
        self,
        article_id: str,
    ) -> list[Relationship]:

        return self._incoming.get(
            article_id,
            []
        )

    # ---------------------------------------------------------

    def neighbors(
        self,
        article_id: str,
    ) -> list[str]:

        result = set()

        for relationship in self.outgoing(article_id):

            result.add(
                relationship.target
            )

        for relationship in self.incoming(article_id):

            result.add(
                relationship.source
            )

        return sorted(result)

    # ---------------------------------------------------------

    def count(self):

        return sum(

            len(v)

            for v in self._outgoing.values()

        )

    # ---------------------------------------------------------

    def clear(self):

        self._outgoing.clear()

        self._incoming.clear()
