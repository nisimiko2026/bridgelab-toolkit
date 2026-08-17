"""
BridgeLab Toolkit
Metadata Validator
"""

from __future__ import annotations

import datetime as dt
import re

from core.models import Article, Issue


# ============================================================
# Metadata Validator
# ============================================================

class MetadataValidator:

    MIN_DESCRIPTION_LENGTH = 30
    DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

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

    GENERATED_ROOT_DOCUMENTS = {
        "acronyms.md",
        "bibliography.md",
        "glossary.md",
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

        subject = article.relative_path.as_posix()

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        for field in self.REQUIRED_FIELDS:

            if (
                field == "difficulty"
                and not self._requires_difficulty(article)
            ):
                continue

            value = getattr(meta, field)

            if value:
                continue

            issues.append(
                Issue(
                    severity="Error",
                    article=subject,
                    category=field,
                    message=f"Missing {field}",
                )
            )

        # ----------------------------------------------------
        # Difficulty
        # ----------------------------------------------------

        if (
            self._requires_difficulty(article)
            and meta.difficulty
            and not self._is_valid_difficulty(meta.difficulty)
        ):
            issues.append(
                Issue(
                    severity="Warning",
                    article=subject,
                    category="difficulty",
                    message="Invalid difficulty",
                )
            )

        # ----------------------------------------------------
        # Last-updated date
        # ----------------------------------------------------

        if meta.last_updated:
            if not self.DATE_RE.fullmatch(meta.last_updated):
                issues.append(
                    Issue(
                        severity="Error",
                        article=subject,
                        category="last_updated",
                        message="Invalid last_updated format; expected YYYY-MM-DD",
                    )
                )
            else:
                try:
                    dt.date.fromisoformat(meta.last_updated)
                except ValueError:
                    issues.append(
                        Issue(
                            severity="Error",
                            article=subject,
                            category="last_updated",
                            message="Invalid last_updated calendar date",
                        )
                    )

        # ----------------------------------------------------
        # Description length
        # ----------------------------------------------------

        if (
            meta.description
            and len(meta.description) < self.MIN_DESCRIPTION_LENGTH
        ):
            issues.append(
                Issue(
                    severity="Warning",
                    article=subject,
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
                    article=subject,
                    category="tags",
                    message="Duplicate tags",
                )
            )

        return issues

    # --------------------------------------------------------

    @classmethod
    def _requires_difficulty(
        cls,
        article: Article,
    ) -> bool:
        """Generated root and reference documents have no instructional level."""

        path = article.relative_path

        return (
            path.name not in cls.GENERATED_ROOT_DOCUMENTS
            and (not path.parts or path.parts[0] != "references")
        )

    # --------------------------------------------------------

    @classmethod
    def _is_valid_difficulty(
        cls,
        value: str,
    ) -> bool:
        """Accept a single level, all levels, or an ordered level range."""

        if value in cls.VALID_DIFFICULTY:
            return True

        if value == "All Levels":
            return True

        levels = value.split(" to ")

        if len(levels) != 2:
            return False

        start, end = levels
        order = ("Beginner", "Intermediate", "Advanced", "Expert")

        return (
            start in order
            and end in order
            and order.index(start) < order.index(end)
        )
