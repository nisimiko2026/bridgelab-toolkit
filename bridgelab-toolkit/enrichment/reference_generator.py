"""
BridgeLab Toolkit
Reference Generator
"""

from __future__ import annotations

from dataclasses import dataclass

from core.models import Article


# ============================================================
# Reference Generator
# ============================================================

@dataclass(slots=True)
class ReferenceGenerator:
    """
    Generate metadata references from article links.
    """

    # ========================================================

    def generate(
        self,
        article: Article,
    ) -> list[str]:
        """
        Generate a sorted list of references.
        """

        references: set[str] = set()

        for link in article.links:

            reference = self._normalize(link)

            if reference:
                references.add(reference)

        return sorted(references)

    # ========================================================

    def _normalize(
        self,
        link: str,
    ) -> str:
        """
        Normalize a Markdown link target.
        """

        link = link.strip()

        if not link:
            return ""

        # Normalize path separators
        link = link.replace("\\", "/")

        # Remove anchors
        if "#" in link:
            link = link.split("#", 1)[0]

        # Remove Markdown extension
        if link.endswith(".md"):
            link = link[:-3]

        return link
