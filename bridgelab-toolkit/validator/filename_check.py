import re

from core.models import Article, Issue


class FilenameCheck:

    VALID = re.compile(

        r"^[a-z0-9-]+\.md$"

    )

    def run(self, articles: list[Article]) -> list[Issue]:

        report: list[Issue] = []

        for article in articles:

            if not self.VALID.match(

                article.filename

            ):

                report.append(
                    Issue(
                        severity="Error",
                        article=article.relative_path.as_posix(),
                        category="Filename",
                        message=f"Invalid filename: {article.filename}",
                    )
                )

        return report
