class HeadingCheck:

    REQUIRED = [

        "Overview",

        "Summary"

    ]

    def run(self, articles):

        report = []

        for article in articles:

            names = {

                h.title

                for h in article.headings

            }

            for heading in self.REQUIRED:

                if heading not in names:

                    report.append(

                        f"{article.filename}: missing heading '{heading}'"

                    )

        return report
