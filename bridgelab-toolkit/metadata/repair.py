"""
BridgeLab Toolkit
Metadata Repair Engine
"""

from __future__ import annotations

from core.models import Article
from core.models import Metadata

from .generator import MetadataGenerator


class MetadataRepair:
    """
    Repairs incomplete metadata.

    Existing values are preserved whenever possible.
    """

    def __init__(self):

        self.generator = MetadataGenerator()

    # ---------------------------------------------------------

    def repair(
        self,
        article: Article,
    ) -> Metadata:

        generated = self.generator.from_article(article)

        meta = article.metadata

        if not meta.title:
            meta.title = generated.title

        if not meta.description:
            meta.description = generated.description

        if not meta.category:
            meta.category = generated.category

        if not meta.subcategory:
            meta.subcategory = generated.subcategory

        if not meta.difficulty:
            meta.difficulty = generated.difficulty

        if not meta.tags:
            meta.tags = generated.tags

        if not meta.systems:
            meta.systems = generated.systems

        if not meta.last_updated:
            meta.last_updated = generated.last_updated

        return meta

    # ---------------------------------------------------------

    def repair_all(
        self,
        articles: list[Article],
    ):

        for article in articles:

            self.repair(article)

        return articles
