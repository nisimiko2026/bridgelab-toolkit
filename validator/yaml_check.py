class YAMLCheck:

    REQUIRED = [

        "title",

        "description"

    ]

    def run(self, articles):

        report = []

        for article in articles:

            meta = article.metadata

            for field in self.REQUIRED:

                if not getattr(meta, field):

                    report.append(

                        f"{article.filename}: missing {field}"

                    )

        return report
