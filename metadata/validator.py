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
            and not self._is_valid_difficulty(article, meta.difficulty)
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
        # Description length
        # ----------------------------------------------------

        if (
            meta.description
            and len(meta.description) < 30
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
        article: Article,
        value: str,
    ) -> bool:
        """Indexes and references may span an ordered difficulty range."""

        if value in cls.VALID_DIFFICULTY:
            return True

        path = article.relative_path

        is_index_or_reference = (
            "index" in path.name.lower()
            or (path.parts and path.parts[0] == "references")
        )

        if not is_index_or_reference:
            return False

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
