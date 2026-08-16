from core.models import Article, Issue


class HeadingCheck:
    """Validate the structural heading used to introduce ordinary articles."""

    INTRODUCTORY_HEADINGS = {
        "overview",
        "introduction",
        "purpose",
        "objectives",
    }
    GENERATED_ROOT_DOCUMENTS = {
        "acronyms.md",
        "bibliography.md",
        "glossary.md",
    }

    def run(self, articles: list[Article]) -> list[Issue]:
        report: list[Issue] = []

        for article in articles:
            if not self._requires_introduction(article):
                continue

            names = {heading.title.strip().casefold() for heading in article.headings}
            if names.isdisjoint(self.INTRODUCTORY_HEADINGS):
                report.append(
                    Issue(
                        severity="Warning",
                        article=article.relative_path.as_posix(),
                        category="Heading",
                        message=(
                            "Missing introductory heading "
                            "(Overview, Introduction, Purpose, or Objectives)"
                        ),
                    )
                )

        return report

    @classmethod
    def _requires_introduction(cls, article: Article) -> bool:
        path = article.relative_path
        parts = tuple(part.casefold() for part in path.parts)
        filename = path.name.casefold()

        if "index" in path.stem.casefold():
            return False
        if filename in cls.GENERATED_ROOT_DOCUMENTS and len(parts) == 1:
            return False
        if parts[:1] == ("references",):
            return False
        if parts[:2] == ("bidding", "convention-cards"):
            return False

        return True
