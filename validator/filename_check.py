import re


class FilenameCheck:

    VALID = re.compile(

        r"^[a-z0-9-]+\.md$"

    )

    def run(self, articles):

        report = []

        for article in articles:

            if not self.VALID.match(

                article.filename

            ):

                report.append(

                    f"Invalid filename: {article.filename}"

                )

        return report
