"""
BridgeLab Toolkit
Knowledge Graph
"""

from __future__ import annotations

from collections import defaultdict

from core.models import Article


# ============================================================
# Knowledge Graph
# ============================================================

class KnowledgeGraph:
    """
    In-memory representation of the knowledge repository.
    """

    def __init__(
        self,
        articles: list[Article],
    ) -> None:

        self.articles = articles

        self.by_id: dict[str, Article] = {}
        self.by_path: dict[str, Article] = {}

        self.by_category: dict[str, list[Article]] = defaultdict(list)
        self.by_system: dict[str, list[Article]] = defaultdict(list)
        self.by_tag: dict[str, list[Article]] = defaultdict(list)

        self._incoming: dict[str, set[str]] = defaultdict(set)
        self._outgoing: dict[str, set[str]] = defaultdict(set)

        self._build()

    # ========================================================

    def _build(self) -> None:

        #
        # Index articles
        #

        for article in self.articles:

            self.by_id[article.id] = article

            self.by_path[article.relative_path] = article

            if article.metadata.category:

                self.by_category[
                    article.metadata.category
                ].append(article)

            for system in article.metadata.systems:

                self.by_system[system].append(article)

            for tag in article.metadata.tags:

                self.by_tag[tag].append(article)

        #
        # Build graph
        #

        for article in self.articles:

            source = article.id

            for target in article.metadata.references:

                self._outgoing[source].add(target)
                self._incoming[target].add(source)

    # ========================================================

    def article(
        self,
        article_id: str,
    ) -> Article | None:

        return self.by_id.get(article_id)

    # ========================================================

    def find_article(
        self,
        query: str,
    ) -> Article | None:
        """
        Find an article by id, title, filename or path.
        """

        query = query.lower().strip()

        #
        # ID
        #

        if query in self.by_id:
            return self.by_id[query]

        #
        # Filename
        #

        for article in self.articles:

            if article.filename.lower() == query:
                return article

            if article.filename.removesuffix(".md").lower() == query:
                return article

        #
        # Title
        #

        for article in self.articles:

            if article.metadata.title.lower() == query:
                return article

        #
        # Relative path
        #

        if query in self.by_path:
            return self.by_path[query]

        #
        # Partial match
        #

        for article in self.articles:

            if (
                query in article.metadata.title.lower()
                or query in article.relative_path.lower()
            ):
                return article

        return None

    # ========================================================

    def outgoing(
        self,
        article: Article,
    ) -> set[str]:

        return self._outgoing.get(
            article.id,
            set(),
        )

    # ========================================================

    def incoming(
        self,
        article: Article,
    ) -> set[str]:

        return self._incoming.get(
            article.id,
            set(),
        )

    # ========================================================

    def neighbours(
        self,
        article: Article,
    ) -> set[str]:

        return (
            self.incoming(article)
            | self.outgoing(article)
        )

    # ========================================================

    def orphan_articles(
        self,
    ) -> list[Article]:

        return [
            article
            for article in self.articles
            if not self.incoming(article)
            and not self.outgoing(article)
        ]
