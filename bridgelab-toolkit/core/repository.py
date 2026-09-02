"""
BridgeLab Toolkit
Repository
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .parser import ArticleParser
from .scanner import RepositoryScanner


class Repository:
    """
    Builds and manages the BridgeLab repository.
    """

    def __init__(
        self,
        root: Path,
    ):

        self.root = root.resolve()

        self.scanner = RepositoryScanner(self.root)

        self.parser = ArticleParser()

        self.articles = []

    # =========================================================
    # Build
    # =========================================================

    def build(self):

        self.articles = self.scanner.scan()

        self.parser.parse_all(
            self.articles
        )

        return self.articles

    # =========================================================
    # Statistics
    # =========================================================

    def statistics(self):

        articles = len(self.articles)

        words = sum(
            article.words
            for article in self.articles
        )

        lines = sum(
            article.lines
            for article in self.articles
        )

        characters = sum(
            article.characters
            for article in self.articles
        )

        return {

            "articles": articles,

            "words": words,

            "lines": lines,

            "characters": characters,

            "average_words": (
                words // articles
                if articles
                else 0
            ),

            "average_lines": (
                lines // articles
                if articles
                else 0
            ),

            "average_characters": (
                characters // articles
                if articles
                else 0
            ),

        }

    # =========================================================
    # Export Repository
    # =========================================================

    def export_json(
        self,
        output: Path,
    ):

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = []

        for article in self.articles:

            item = asdict(article)

            item["path"] = str(article.path)

            item["relative_path"] = article.relative_path.as_posix()

            data.append(item)

        output.write_text(

            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),

            encoding="utf-8",

        )

    # =========================================================
    # Export Statistics
    # =========================================================

    def export_statistics(
        self,
        output: Path,
    ):

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output.write_text(

            json.dumps(
                self.statistics(),
                indent=4,
                ensure_ascii=False,
            ),

            encoding="utf-8",

        )
