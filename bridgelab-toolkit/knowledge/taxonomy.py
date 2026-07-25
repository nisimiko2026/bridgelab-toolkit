"""
BridgeLab Toolkit
Taxonomy Builder
"""

from __future__ import annotations

from collections import defaultdict

from core.models import Entity


class TaxonomyBuilder:
    """
    Builds a taxonomy from extracted entities.
    """

    def build(
        self,
        entities: list[Entity],
    ) -> dict[str, list[Entity]]:

        taxonomy = defaultdict(list)

        for entity in entities:

            taxonomy[entity.category].append(entity)

        for category in taxonomy:

            taxonomy[category].sort(

                key=lambda entity: entity.name.lower()

            )

        return dict(taxonomy)
