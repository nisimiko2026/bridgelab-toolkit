from collections import defaultdict

from core.models import Article, Issue


class DuplicateCheck:

    def run(self, articles: list[Article]) -> list[Issue]:

        report: list[Issue] = []

        names: dict[str, list[Article]] = defaultdict(list)

        for article in articles:

            names[article.filename].append(article)

        for name in sorted(names):

            duplicates = names[name]

            if len(duplicates) > 1:

                subject = min(
                    article.relative_path.as_posix()
                    for article in duplicates
                )

                report.append(
                    Issue(
                        severity="Error",
                        article=subject,
                        category="Filename",
                        message=f"Duplicate filename: {name}",
                    )
                )

        return report
