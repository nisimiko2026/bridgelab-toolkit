"""
BridgeLab Toolkit
Metadata Validator
"""

from __future__ import annotations

from dataclasses import dataclass

from core.models import Article


# ============================================================
# Validation Issue
# ============================================================

@dataclass(slots=True)
class MetadataIssue:

    severity: str

    field: str

    article: str

    message: str


# ============================================================
# Metadata Validator
# ============================================================

class MetadataValidator:

    REQUIRED_FIELDS = [

        "title",

        "description",

        "category",

        "difficulty",

        "last_updated",

    ]

    VALID_DIFFICULTY = {

        "Beginner",

        "Intermediate",

        "Advanced",

        "Expert",

    }

    # --------------------------------------------------------

    def validate(
        self,
        articles: list[Article],
    ) -> list[MetadataIssue]:

        issues = []

        for article in articles:

            issues.extend(

                self._validate_article(article)

            )

        return issues

    # --------------------------------------------------------

    def _validate_article(
        self,
        article: Article,
    ) -> list[MetadataIssue]:

        issues = []

        meta = article.metadata

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        for field in self.REQUIRED_FIELDS:

            value = getattr(meta, field)

            if value:

                continue

            issues.append(

                MetadataIssue(

                    severity="Error",

                    field=field,

                    article=article.filename,

                    message=f"Missing {field}",

                )

            )

        # ----------------------------------------------------
        # Difficulty
        # ----------------------------------------------------

        if (

            meta.difficulty

            and meta.difficulty

            not in self.VALID_DIFFICULTY

        ):

            issues.append(

                MetadataIssue(

                    severity="Warning",

                    field="difficulty",

                    article=article.filename,

                    message="Invalid difficulty",

                )

            )

        # ----------------------------------------------------
        # Description length
        # ----------------------------------------------------

        if (

            meta.description

            and len(meta.description) < 30

        ):

            issues.append(

                MetadataIssue(

                    severity="Warning",

                    field="description",

                    article=article.filename,

                    message="Description too short",

                )

            )

        # ----------------------------------------------------
        # Duplicate tags
        # ----------------------------------------------------

        if len(meta.tags) != len(set(meta.tags)):

            issues.append(

                MetadataIssue(

                    severity="Warning",

                    field="tags",

                    article=article.filename,

                    message="Duplicate tags",

                )

            )

        return issues
