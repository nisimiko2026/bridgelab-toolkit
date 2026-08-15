from core.models import Article, Issue


class DirectoryCheck:

    def run(self, articles: list[Article]) -> list[Issue]:

        report: list[Issue] = []

        directories = {

            article.relative_path.parent

            for article in articles

        }

        for directory in sorted(
            directories,
            key=lambda path: path.as_posix(),
        ):

            has_index = any(

                a.relative_path.parent == directory

                and "index" in a.filename

                for a in articles

            )

            if not has_index:

                report.append(
                    Issue(
                        severity="Warning",
                        article=directory.as_posix(),
                        category="Directory",
                        message="No index file",
                    )
                )

        return report
