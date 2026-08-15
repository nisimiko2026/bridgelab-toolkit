"""
BridgeLab Toolkit
Article Parser
"""

from __future__ import annotations

import re

import yaml

from .models import Article, Heading, Metadata


class ArticleParser:
    """
    Parses BridgeLab Markdown articles.
    """

    # ==========================================================
    # Regular Expressions
    # ==========================================================

    YAML_RE = re.compile(
        r"^---\n(.*?)\n---",
        re.DOTALL,
    )

    HEADING_RE = re.compile(
        r"^(#{1,6})\s+(.*)$",
        re.MULTILINE,
    )

    LINK_RE = re.compile(
        r"\[.*?\]\((.*?)\)"
    )

    # ==========================================================
    # Public API
    # ==========================================================

    def parse(
        self,
        article: Article,
    ) -> Article:

        text = article.path.read_text(
            encoding="utf-8"
        )

        self._parse_statistics(
            article,
            text,
        )

        self._parse_yaml(
            article,
            text,
        )

        self._parse_headings(
            article,
            text,
        )

        self._parse_links(
            article,
            text,
        )

        return article

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

        article.words = len(text.split())

        article.lines = len(text.splitlines())

        article.characters = len(text)

    # ==========================================================
    # YAML
    # ==========================================================

    def _parse_yaml(
        self,
        article: Article,
        text: str,
    ) -> None:

        article.metadata_error = None

        match = self.YAML_RE.search(text)

        if not match:

            if text.startswith("---"):
                article.metadata_error = (
                    "Malformed YAML front matter: missing closing delimiter"
                )

            return

        try:

            data = yaml.safe_load(
                match.group(1)
            )

            if data is None:
                return

            if not isinstance(data, dict):
                raise ValueError(
                    "YAML front matter must contain a mapping"
                )

            article.metadata = Metadata(

                title=str(data.get("title", "")),

                description=str(
                    data.get("description", "")
                ),

                category=str(
                    data.get("category", "")
                ),

                subcategory=str(
                    data.get("subcategory", "")
                ),

                difficulty=str(
                    data.get("difficulty", "")
                ),

                tags=list(
                    data.get("tags", [])
                ),

                systems=list(
                    data.get("systems", [])
                ),

                aliases=list(
                    data.get("aliases", [])
                ),

                acronyms=list(
                    data.get("acronyms", [])
                ),

                references=list(
                    data.get("references", [])
                ),

                last_updated=str(
                    data.get("last_updated", "")
                ),

                status=str(
                    data.get("status", "")
                ),

            )

        except Exception as error:

            article.metadata_error = (
                f"Malformed YAML front matter: {error}"
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

        for match in self.HEADING_RE.finditer(text):

            article.headings.append(

                Heading(

                    level=len(match.group(1)),

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

        article.links.clear()

        for match in self.LINK_RE.finditer(text):

            article.links.append(

                match.group(1)

            )
