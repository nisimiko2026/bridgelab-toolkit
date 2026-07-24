"""
BridgeLab Toolkit
Cross-Reference Generator
"""

from __future__ import annotations

from core.models import (
    CrossReference,
    CrossReferenceItem,
    Relationship,
)


class CrossReferenceGenerator:
    """
    Converts relationships into structured cross references.
    """

    # ---------------------------------------------------------

    def generate(
        self,
        relationships: list[Relationship],
    ) -> list[CrossReference]:

        references: dict[str, CrossReference] = {}

        for relationship in relationships:

            if relationship.source not in references:

                references[relationship.source] = CrossReference(
                    article=relationship.source
                )

            reference = references[relationship.source]

            item = CrossReferenceItem(
                article=relationship.target,
                relation=relationship.relation,
                score=relationship.score,
            )

            match relationship.relation:

                case "prerequisite":

                    reference.prerequisites.append(item)

                case "system":

                    reference.related_systems.append(item)

                case "advanced":

                    reference.advanced_topics.append(item)

                case _:

                    reference.related_topics.append(item)

        # -----------------------------------------------------
        # Sort by confidence score (highest first)
        # -----------------------------------------------------

        for reference in references.values():

            reference.prerequisites.sort(
                key=lambda x: x.score,
                reverse=True,
            )

            reference.related_topics.sort(
                key=lambda x: x.score,
                reverse=True,
            )

            reference.related_systems.sort(
                key=lambda x: x.score,
                reverse=True,
            )

            reference.advanced_topics.sort(
                key=lambda x: x.score,
                reverse=True,
            )

        return sorted(
            references.values(),
            key=lambda x: x.article,
        )
