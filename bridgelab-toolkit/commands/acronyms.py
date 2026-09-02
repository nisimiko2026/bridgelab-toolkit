"""
BridgeLab Toolkit
Acronym Command
"""

from pathlib import Path

from config import (
    OUTPUT,
)

from core.repository import Repository

from generators.acronyms import AcronymGenerator


def run(root: Path):

    repository = Repository(root)

    repository.build()

    generator = AcronymGenerator()

    generator.load(repository.articles)

    generator.write(

        OUTPUT / "acronyms.md"

    )
