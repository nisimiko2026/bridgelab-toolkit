class DirectoryCheck:

    def run(self, articles):

        report = []

        directories = {

            article.relative_path.parent

            for article in articles

        }

        for directory in directories:

            has_index = any(

                a.relative_path.parent == directory

                and "index" in a.filename

                for a in articles

            )

            if not has_index:

                report.append(

                    f"{directory}: no index file"

                )

        return report
