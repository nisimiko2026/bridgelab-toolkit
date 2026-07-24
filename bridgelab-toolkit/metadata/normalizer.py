"""
BridgeLab Toolkit
Metadata Normalizer
"""

from __future__ import annotations

from core.models import Article


class MetadataNormalizer:
    """
    Standardizes metadata values.
    """

    CATEGORY_MAP = {

        "conventions": "Conventions",
        "planning": "Planning",
        "declarer-play": "Declarer Play",
        "defense": "Defense",
        "duplicate-bridge": "Duplicate Bridge",
        "systems": "Systems",

    }

    DIFFICULTY_MAP = {

        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "advanced": "Advanced",
        "expert": "Expert",

    }

    # ---------------------------------------------------------

    def normalize(
        self,
        article: Article,
    ):

        meta = article.metadata

        # ------------------------------------------
        # Category
        # ------------------------------------------

        if meta.category:

            key = meta.category.strip().lower()

            if key in self.CATEGORY_MAP:

                meta.category = self.CATEGORY_MAP[key]

        # ------------------------------------------
        # Difficulty
        # ------------------------------------------

        if meta.difficulty:

            key = meta.difficulty.strip().lower()

            if key in self.DIFFICULTY_MAP:

                meta.difficulty = self.DIFFICULTY_MAP[key]

        # ------------------------------------------
        # Tags
        # ------------------------------------------

        meta.tags = sorted(

            set(

                tag.strip().lower()

                for tag in meta.tags

                if tag.strip()

            )

        )

        # ------------------------------------------
        # Systems
        # ------------------------------------------

        meta.systems = sorted(

            set(

                system.strip()

                for system in meta.systems

                if system.strip()

            )

        )

        return article

    # ---------------------------------------------------------

    def normalize_all(
        self,
        articles: list[Article],
    ):

        for article in articles:

            self.normalize(article)

        return articles
