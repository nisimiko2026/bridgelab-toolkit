from core.models import Article, Issue


class ReferenceCheck:
    """Validate article identifiers stored in front-matter references."""

    def run(self, articles: list[Article]) -> list[Issue]:
        article_ids = {article.id.casefold() for article in articles}
        report: list[Issue] = []

        for article in articles:
            seen: set[str] = set()
            for target in article.metadata.references:
                normalized = target.strip().removesuffix(".md").casefold()

                if normalized == article.id.casefold():
                    report.append(
                        self._issue(article, "Error", "Self reference")
                    )
                elif normalized in seen:
                    report.append(
                        self._issue(
                            article,
                            "Warning",
                            f"Duplicate reference: {target}",
                        )
                    )
                elif normalized not in article_ids:
                    report.append(
                        self._issue(
                            article,
                            "Error",
                            f"Missing reference target: {target}",
                        )
                    )

                seen.add(normalized)

        return report

    @staticmethod
    def _issue(article: Article, severity: str, message: str) -> Issue:
        return Issue(
            severity=severity,
            article=article.relative_path.as_posix(),
            category="Reference",
            message=message,
        )
