# =========================================================
# Statistics
# =========================================================

def statistics(self):

    articles = len(self.articles)

    words = sum(
        article.words
        for article in self.articles
    )

    lines = sum(
        article.lines
        for article in self.articles
    )

    characters = sum(
        article.characters
        for article in self.articles
    )

    return {

        "articles": articles,

        "words": words,

        "lines": lines,

        "characters": characters,

        "average_words": (
            words // articles
            if articles
            else 0
        ),

        "average_lines": (
            lines // articles
            if articles
            else 0
        ),

        "average_characters": (
            characters // articles
            if articles
            else 0
        ),

    }
