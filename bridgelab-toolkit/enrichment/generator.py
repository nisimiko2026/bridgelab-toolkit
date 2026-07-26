"""
BridgeLab Toolkit
Metadata Generator
"""

from __future__ import annotations

from dataclasses import dataclass

from core.models import Article


# ============================================================
# Metadata Generator
# ============================================================

@dataclass(slots=True)
class MetadataGenerator:
    """
    Generates default YAML front matter.
    """

    def generate(
        self,
        article: Article,
    ) -> str:
        """
        Generate a metadata block.
        """

        title = (
            article.metadata.title
            or article.filename.replace("-", " ").replace(".md", "").title()
        )

        return (
            "---\n"
            f"title: {title}\n"
            "description:\n"
            "category:\n"
            "subcategory:\n"
            "difficulty:\n"
            "tags: []\n"
            "systems: []\n"
            "aliases: []\n"
            "acronyms: []\n"
            "references: []\n"
            "last_updated:\n"
            "status: Draft\n"
            "---\n\n"
        )

    def has_metadata(
        self,
        text: str,
    ) -> bool:
        """
        Return True if the document already contains YAML front matter.
        """

        text = text.lstrip()

        if not text.startswith("---"):
            return False

        lines = text.splitlines()

        if len(lines) < 3:
            return False

        for line in lines[1:]:
            if line.strip() == "---":
                return True

        return False
