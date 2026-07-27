"""
BridgeLab Toolkit
Metadata Generator
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from core.models import Article, Metadata


# ============================================================
# Metadata Generator
# ============================================================

@dataclass(slots=True)
class MetadataGenerator:
    """
    Generate metadata inferred from an article.
    """

    # ========================================================
    # Generate
    # ========================================================

    def generate(
        self,
        article: Article,
    ) -> Metadata:
        """
        Generate suggested metadata for an article.
        """

        metadata = Metadata()

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        metadata.title = self._title(article)

        # ----------------------------------------------------
        # Category / Subcategory
        # ----------------------------------------------------

        category, subcategory = self._categories(article)

        metadata.category = category
        metadata.subcategory = subcategory

        # ----------------------------------------------------
        # Defaults
        # ----------------------------------------------------

        metadata.status = "Draft"
        metadata.last_updated = date.today().isoformat()

        return metadata

    # ========================================================
    # Helpers
    # ========================================================

    def _title(
        self,
        article: Article,
    ) -> str:
        """
        Determine the article title.
        """

        if article.metadata.title:
            return article.metadata.title

        for heading in article.headings:

            if heading.level == 1:
                return heading.title.strip()

        return (
            article.filename
            .replace("-", " ")
            .replace(".md", "")
            .title()
        )

    # --------------------------------------------------------

    def _categories(
        self,
        article: Article,
    ) -> tuple[str, str]:
        """
        Determine category and subcategory
        from the article path.
        """

        parts = article.relative_path.parts

        # Temporary debugging
        print(article.relative_path)
        print(parts)
        print()

        category = ""
        subcategory = ""

        if len(parts) >= 2:
            category = parts[0].replace("-", " ").title()

        if len(parts) >= 3:
            subcategory = parts[1].replace("-", " ").title()

        return category, subcategory
