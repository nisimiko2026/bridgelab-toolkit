"""
BridgeLab Toolkit
Metadata Validator
"""

from __future__ import annotations

from core.models import Article, Issue


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
    ) -> list[Issue]:

        issues: list[Issue] = []

        for article in articles:
            issues.extend(
                self._validate_article(article)
            )

        return issues

    # --------------------------------------------------------

    def _validate_article(
        self,
        article: Article,
    ) -> list[Issue]:

        issues: list[Issue] = []

        meta = article.metadata

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        for field in self.REQUIRED_FIELDS:

            value = getattr(meta, field)

            if value:
                continue

            issues.append(
                Issue(
                    severity="Error",
                    article=article.filename,
                    category=field,
                    message=f"Missing {field}",
                )
            )

        # ----------------------------------------------------
        # Difficulty
        # ----------------------------------------------------

        if (
            meta.difficulty
            and meta.difficulty not in self.VALID_DIFFICULTY
        ):
            issues.append(
                Issue(
                    severity="Warning",
                    article=article.filename,
                    category="difficulty",
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
                Issue(
                    severity="Warning",
                    article=article.filename,
                    category="description",
                    message="Description too short",
                )
            )

        # ----------------------------------------------------
        # Duplicate tags
        # ----------------------------------------------------

        if len(meta.tags) != len(set(meta.tags)):
            issues.append(
                Issue(
                    severity="Warning",
                    article=article.filename,
                    category="tags",
                    message="Duplicate tags",
                )
            )

        return issues
