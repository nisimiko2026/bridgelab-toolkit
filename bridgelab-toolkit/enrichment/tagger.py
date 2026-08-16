"""
BridgeLab Toolkit
Tag Generator
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.models import Article


# ============================================================
# Tag Generator
# ============================================================

@dataclass(slots=True)
class TagGenerator:
    """
    Generate tags for an article.
    """

    # ========================================================

    def generate(
        self,
        article: Article,
    ) -> list[str]:
        """
        Generate tags from an article.
        """

        try:
            text = article.path.read_text(
                encoding="utf-8",
            ).lower()

        except OSError:
            return []

        tags: set[str] = set()

        #
        # Category
        #

        if article.metadata.category:
            tags.add(
                article.metadata.category.lower()
            )

        #
        # Subcategory
        #

        if article.metadata.subcategory:
            tags.add(
                article.metadata.subcategory.lower()
            )

        #
        # Systems
        #

        for system in article.metadata.systems:
            tags.add(system.lower())

        #
        # Keyword tags
        #

        keywords = {
            "opening",
            "response",
            "rebid",
            "overcall",
            "double",
            "redouble",
            "cue bid",
            "slam",
            "notrump",
            "transfer",
            "stayman",
            "blackwood",
            "gerber",
            "relay",
            "forcing",
            "competitive",
            "preempt",
            "takeout",
            "negative",
            "support",
            "lead",
            "discard",
            "signal",
            "finesse",
            "ruff",
            "squeeze",
            "endplay",
        }

        for keyword in keywords:

            pattern = (
                r"\b"
                + re.escape(keyword)
                + r"\b"
            )

            if re.search(pattern, text):
                tags.add(keyword)

        return sorted(tags)
