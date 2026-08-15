from core.models import Article, Issue


class HeadingCheck:

    REQUIRED = [

        "Overview",

        "Summary"

    ]

    def run(self, articles: list[Article]) -> list[Issue]:

        report: list[Issue] = []

        for article in articles:

            names = {

                h.title

                for h in article.headings

            }

            for heading in self.REQUIRED:

                if heading not in names:

                    report.append(
                        Issue(
                            severity="Warning",
                            article=article.relative_path.as_posix(),
                            category="Heading",
                            message=(
                                f"Missing heading '{heading}'"
                            ),
                        )
                    )

        return report
