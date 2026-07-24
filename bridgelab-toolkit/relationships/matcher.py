"""
BridgeLab Toolkit
Relationship Matcher
"""

from __future__ import annotations

from collections import defaultdict

from core.models import Relationship


class RelationshipMatcher:
    """
    Groups relationships into editorial categories.
    """

    # ---------------------------------------------------------

    def match(
        self,
        relationships: list[Relationship],
    ) -> dict[str, list[Relationship]]:

        groups = defaultdict(list)

        for relationship in relationships:

            group = self._classify(
                relationship
            )

            groups[group].append(
                relationship
            )

        return groups

    # ---------------------------------------------------------

    def _classify(
        self,
        relationship: Relationship,
    ) -> str:

        match relationship.relation:

            case "subcategory":
                return "Related Topics"

            case "category":
                return "Related Topics"

            case "system":
                return "Related Systems"

            case "prerequisite":
                return "Prerequisites"

            case "advanced":
                return "Advanced Topics"

            case _:
                return "Related Topics"
