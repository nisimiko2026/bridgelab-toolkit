
"""
BridgeLab Toolkit
Article Parser

Parses Markdown articles, including:

- YAML front matter
- Markdown headings
- Basic statistics
- Internal Markdown links
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .models import Article, Metadata, Heading


class ArticleParser:
    """
    Parses BridgeLab Markdown articles.
    """

    # ----------------------------------------------------------
    # Regular expressions
    # ----------------------------------------------------------

    YAML_RE = re.compile(
        r"^---\n(.*?)\n---",
        re.DOTALL,
    )

    HEADING_RE = re.compile(
        r"^(#{1,6})\s+(.*)$"
    )

    LINK_RE = re.compile(
        r"\[.*?\]\((.*?)\)"
    )

    # ----------------------------------------------------------

    def parse(self, article: Article) -> Article:
        """
        Parse a single article.
        """

        text = article.path.read_text(
            encoding="utf-8"
        )

        self._parse_statistics(article, text)

        self._parse_yaml(article, text)

        self._parse_headings(article, text)

        self._parse_links(article, text)

        return article

    # ----------------------------------------------------------

    def parse_all(
        self,
        articles: list[Article],
    ) -> list[Article]:

        for article in articles:

            self.parse(article)

        return articles

    # ==========================================================
    # Statistics
    # ==========================================================

    def _parse_statistics(
        self,
        article: Article,
        text: str,
    ):

        article.word_count = len(
            text.split()
        )

        article.line_count = len(
            text.splitlines()
        )

        article.size_bytes = article.path.stat().st_size

    # ==========================================================
    # YAML
    # ==========================================================

    def _parse_yaml(
        self,
        article: Article,
        text: str,
    ):

        match = self.YAML_RE.search(text)

        if not match:
            return

        try:

            data = yaml.safe_load(
                match.group(1)
            )

            if not data:
                return

            article.metadata = Metadata(

                title=data.get(
                    "title",
                    ""
                ),

                description=data.get(
                    "description",
                    ""
                ),

                category=data.get(
                    "category",
                    ""
                ),

                subcategory=data.get(
                    "subcategory",
                    ""
                ),

                difficulty=data.get(
                    "difficulty",
                    ""
                ),

                tags=data.get(
                    "tags",
                    []
                ),

                systems=data.get(
                    "systems",
                    []
                ),

                last_updated=data.get(
                    "last_updated",
                    ""
                ),

            )

        except Exception as ex:

            article.errors.append(
                f"YAML error: {ex}"
            )

    # ==========================================================
    # Headings
    # ==========================================================

    def _parse_headings(
        self,
        article: Article,
        text: str,
    ):

        article.headings.clear()

        for line in text.splitlines():

            match = self.HEADING_RE.match(line)

            if not match:
                continue

            article.headings.append(

                Heading(

                    level=len(
                        match.group(1)
                    ),

                    title=match.group(2).strip(),

                )

            )

    # ==========================================================
    # Links
    # ==========================================================

    def _parse_links(
        self,
        article: Article,
        text: str,
    ):

        article.outgoing_links.clear()

        for match in self.LINK_RE.finditer(text):

            article.outgoing_links.append(
                match.group(1)
            )
