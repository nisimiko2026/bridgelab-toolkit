"""
BridgeLab Toolkit
Reference Detector
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.models import Article


# ============================================================
# Reference Detector
# ============================================================

@dataclass(slots=True)
class ReferenceDetector:
    """
    Detect internal article references.
    """

    articles: list[Article]

    _titles: dict[str, str] = field(
        init=False,
        default_factory=dict,
    )

    _filenames: dict[str, str] = field(
        init=False,
        default_factory=dict,
    )

    # ========================================================

    def __post_init__(self) -> None:
        """
        Build lookup tables.
        """

        for article in self.articles:

            title = article.metadata.title.strip().lower()

            if title:
                self._titles[title] = article.id

            filename = article.filename.removesuffix(".md").lower()

            self._filenames[filename] = article.id

    # ========================================================

    def detect(
        self,
        article: Article,
    ) -> list[str]:
        """
        Detect internal references.
        """

        try:
            text = article.path.read_text(
                encoding="utf-8",
            )
        except OSError:
            return []

        references: set[str] = set()

        #
        # Wiki links
        #

        for match in re.findall(
            r"\[\[([^\]]+)\]\]",
            text,
        ):

            key = match.strip().lower()

            article_id = (
                self._titles.get(key)
                or self._filenames.get(key)
            )

            if (
                article_id
                and article_id != article.id
            ):
                references.add(article_id)

        #
        # Markdown links
        #

        for match in re.findall(
            r"\[([^\]]+)\]\([^)]+\)",
            text,
        ):

            key = match.strip().lower()

            article_id = (
                self._titles.get(key)
                or self._filenames.get(key)
            )

            if (
                article_id
                and article_id != article.id
            ):
                references.add(article_id)

        #
        # Plain title mentions
        #

        content = text.lower()

        for title, article_id in self._titles.items():

            if article_id == article.id:
                continue

            pattern = (
                r"\b"
                + re.escape(title)
                + r"\b"
            )

            if re.search(pattern, content):
                references.add(article_id)

        return sorted(references)
