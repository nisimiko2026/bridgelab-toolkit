"""
BridgeLab Toolkit
Relationship Validator
"""

from __future__ import annotations

from core.models import CrossReference
from core.models import Issue


# ============================================================
# Validator
# ============================================================

class CrossReferenceValidator:
    """
    Validates generated cross references.
    """

    # ---------------------------------------------------------

    def validate(
        self,
        references: list[CrossReference],
    ) -> list[Issue]:

        issues: list[Issue] = []

        for reference in references:
            issues.extend(
                self._validate_reference(reference)
            )

        return issues

    # ---------------------------------------------------------

    def _validate_reference(
        self,
        reference: CrossReference,
    ) -> list[Issue]:

        issues: list[Issue] = []

        # -----------------------------------------------------
        # Self references
        # -----------------------------------------------------

        for group in [
            reference.prerequisites,
            reference.related_topics,
            reference.related_systems,
            reference.advanced_topics,
        ]:

            for item in group:

                if item.article == reference.article:

                    issues.append(
                        Issue(
                            severity="Error",
                            article=reference.article,
                            category="CrossReference",
                            message="Self reference",
                        )
                    )

        # -----------------------------------------------------
        # Duplicate references
        # -----------------------------------------------------

        seen: set[str] = set()

        for group in [
            reference.prerequisites,
            reference.related_topics,
            reference.related_systems,
            reference.advanced_topics,
        ]:

            for item in group:

                if item.article in seen:

                    issues.append(
                        Issue(
                            severity="Warning",
                            article=reference.article,
                            category="CrossReference",
                            message=f"Duplicate reference: {item.article}",
                        )
                    )

                else:
                    seen.add(item.article)

        return issues
