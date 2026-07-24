"""
BridgeLab Toolkit
Metadata Generator
"""

from __future__ import annotations

from core.models import Metadata


class MetadataGenerator:
    """
    Generates default metadata for articles that
    do not yet contain YAML front matter.
    """

    # ---------------------------------------------------------

    def generate(
        self,
        title: str,
        category: str,
        subcategory: str = "",
    ) -> Metadata:

        return Metadata(

            title=title,

            description="",

            category=category,

            subcategory=subcategory,

            difficulty="Intermediate",

            tags=[],

            systems=[],

            last_updated="",

        )

    # ---------------------------------------------------------

    def from_article(
        self,
        article,
    ) -> Metadata:

        title = article.filename.replace(
            ".md",
            ""
        )

        title = title.replace(
            "-",
            " "
        ).title()

        category = article.directory.split("/")[0]

        subcategory = ""

        if "/" in article.directory:

            subcategory = article.directory.split("/")[1]

        return self.generate(

            title,

            category,

            subcategory,

        )
