"""
BridgeLab Toolkit
Bibliography Command
"""

from pathlib import Path

from config import (
    OUTPUT,
)

from core.repository import Repository

from generators.bibliography import BibliographyGenerator


def run(root: Path):

    repository = Repository(root)

    repository.build()

    generator = BibliographyGenerator()

    generator.load(repository.articles)

    generator.write(

        OUTPUT / "bibliography.md"

    )
