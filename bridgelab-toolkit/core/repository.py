"""
BridgeLab Toolkit
Repository Builder
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import asdict

from .scanner import RepositoryScanner
from .parser import ArticleParser


class Repository:

    def __init__(self, root: Path):

        self.root = root

        self.scanner = RepositoryScanner(root)

        self.parser = ArticleParser()

        self.articles = []

    # ------------------------------------------------------------

    def build(self):

        self.articles = self.scanner.scan()

        self.parser.parse_all(self.articles)

        return self.articles

    # ------------------------------------------------------------

    def statistics(self):

        return {

            "articles": len(self.articles),

            "words": sum(a.word_count for a in self.articles),

            "lines": sum(a.line_count for a in self.articles),

            "bytes": sum(a.size_bytes for a in self.articles),

        }

    # ------------------------------------------------------------

    def export_json(self, output: Path):

        output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        data = []

        for article in self.articles:

            item = asdict(article)

            item["path"] = str(article.path)

            item["relative_path"] = str(article.relative_path)

            data.append(item)

        output.write_text(

            json.dumps(
                data,
                indent=4,
                ensure_ascii=False
            ),

            encoding="utf-8"

        )
