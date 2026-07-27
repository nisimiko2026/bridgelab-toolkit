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
    Generate suggested metadata for an article.
    """

    # ========================================================
    # Generate
    # ========================================================

    def generate(
        self,
        article: Article,
    ) -> Metadata:
        """
        Generate metadata inferred from the article.
        """

        metadata = Metadata()

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        metadata.title = article.metadata.title

        if not metadata.title:

            for heading in article.headings:

                if heading.level == 1:

                    metadata.title = heading.title.strip()

                    break

        if not metadata.title:

            metadata.title = (
                article.filename
                .replace("-", " ")
                .replace(".md", "")
                .title()
            )

        # ----------------------------------------------------
        # Category / Subcategory
        # ----------------------------------------------------

        parts = str(article.relative_path).replace("\\", "/").split("/")

        if len(parts) >= 2:
            metadata.category = parts[0]

        if len(parts) >= 3:
            metadata.subcategory = parts[1]

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        metadata.status = "Draft"

        # ----------------------------------------------------
        # Last Updated
        # ----------------------------------------------------

        metadata.last_updated = date.today().isoformat()

        return metadata
