"""
BridgeLab Toolkit
Cross-Reference Validator
"""

from __future__ import annotations

from dataclasses import dataclass

from core.models import CrossReference


# ============================================================
# Validation Issue
# ============================================================

@dataclass(slots=True)
class CrossReferenceIssue:

    severity: str

    article: str

    message: str


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
    ) -> list[CrossReferenceIssue]:

        issues = []

        for reference in references:

            issues.extend(

                self._validate_reference(
                    reference
                )

            )

        return issues

    # ---------------------------------------------------------

    def _validate_reference(
        self,
        reference: CrossReference,
    ) -> list[CrossReferenceIssue]:

        issues = []

        # -----------------------------------------
        # Self reference
        # -----------------------------------------

        for group in [

            reference.prerequisites,

            reference.related_topics,

            reference.related_systems,

            reference.advanced_topics,

        ]:

            for item in group:

                if item.article == reference.article:

                    issues.append(

                        CrossReferenceIssue(

                            severity="Error",

                            article=reference.article,

                            message="Self reference",

                        )

                    )

        # -----------------------------------------
        # Duplicate references
        # -----------------------------------------

        seen = set()

        for group in [

            reference.prerequisites,

            reference.related_topics,

            reference.related_systems,

            reference.advanced_topics,

        ]:

            for item in group:

                if item.article in seen:

                    issues.append(

                        CrossReferenceIssue(

                            severity="Warning",

                            article=reference.article,

                            message=f"Duplicate reference: {item.article}",

                        )

                    )

                seen.add(item.article)

        return issues
