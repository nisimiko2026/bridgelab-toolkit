"""
BridgeLab Toolkit
Glossary Command
"""

from pathlib import Path

from config import (
    OUTPUT,
)

from core.repository import Repository

from generators.glossary import GlossaryGenerator


def run(root: Path):

    repository = Repository(root)

    repository.build()

    generator = GlossaryGenerator()

    generator.load(repository.articles)

    generator.write(

        OUTPUT / "glossary.md"

    )
