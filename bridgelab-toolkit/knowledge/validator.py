"""
BridgeLab Toolkit
Knowledge Validator
"""

from __future__ import annotations

from core.models import Entity
from core.models import Issue


class KnowledgeValidator:
    """
    Validates extracted knowledge entities.
    """

    # =========================================================
    # Validate
    # =========================================================

    def validate(
        self,
        entities: list[Entity],
    ) -> list[Issue]:

        issues: list[Issue] = []

        seen: set[tuple[str, str]] = set()

        for entity in entities:

            # ---------------------------------------------
            # Missing name
            # ---------------------------------------------

            if not entity.name.strip():

                issues.append(

                    Issue(

                        severity="Error",

                        article=entity.article,

                        category="Knowledge",

                        message="Entity has no name",

                    )

                )

            # ---------------------------------------------
            # Missing category
            # ---------------------------------------------

            if not entity.category.strip():

                issues.append(

                    Issue(

                        severity="Warning",

                        article=entity.article,

                        category="Knowledge",

                        message=f"'{entity.name}' has no category",

                    )

                )

            # ---------------------------------------------
            # Duplicate entity
            # ---------------------------------------------

            key = (

                entity.article,

                entity.name.lower(),

            )

            if key in seen:

                issues.append(

                    Issue(

                        severity="Warning",

                        article=entity.article,

                        category="Knowledge",

                        message=f"Duplicate entity: {entity.name}",

                    )

                )

            else:

                seen.add(key)

        return issues
