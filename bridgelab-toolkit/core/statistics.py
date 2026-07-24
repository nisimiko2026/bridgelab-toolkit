"""
BridgeLab Toolkit
Repository Statistics
"""

from __future__ import annotations

from collections import Counter

from .models import Article


class StatisticsEngine:

    def __init__(self, articles: list[Article]):

        self.articles = articles

    # ---------------------------------------------------------

    def build(self) -> dict:

        categories = Counter()

        subcategories = Counter()

        headings = Counter()

        difficulty = Counter()

        total_words = 0

        total_lines = 0

        total_bytes = 0

        for article in self.articles:

            total_words += article.word_count

            total_lines += article.line_count

            total_bytes += article.size_bytes

            if article.category:

                categories[article.category] += 1

            if article.subcategory:

                subcategories[article.subcategory] += 1

            if article.metadata.difficulty:

                difficulty[article.metadata.difficulty] += 1

            for heading in article.headings:

                headings[heading.title] += 1

        return {

            "articles": len(self.articles),

            "words": total_words,

            "lines": total_lines,

            "bytes": total_bytes,

            "average_words":

                round(total_words / len(self.articles), 1)

                if self.articles else 0,

            "categories": dict(categories),

            "subcategories": dict(subcategories),

            "difficulty": dict(difficulty),

            "headings": dict(headings),

        }
