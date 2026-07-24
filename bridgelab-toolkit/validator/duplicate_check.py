from collections import Counter


class DuplicateCheck:

    def run(self, articles):

        report = []

        names = Counter()

        for article in articles:

            names[article.filename] += 1

        for name, count in names.items():

            if count > 1:

                report.append(

                    f"Duplicate filename: {name}"

                )

        return report
