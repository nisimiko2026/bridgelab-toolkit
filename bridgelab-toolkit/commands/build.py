"""
BridgeLab Toolkit
Build Command
"""

from pathlib import Path

from core.repository import Repository

from generators.glossary import GlossaryGenerator
from generators.acronyms import AcronymGenerator
from generators.bibliography import BibliographyGenerator

from config import OUTPUT


def run(root: Path):

    repository = Repository(root)

    repository.build()

    generators = [

        (

            GlossaryGenerator(),

            OUTPUT / "glossary.md",

        ),

        (

            AcronymGenerator(),

            OUTPUT / "acronyms.md",

        ),

        (

            BibliographyGenerator(),

            OUTPUT / "bibliography.md",

        ),

    ]

    for generator, output in generators:

        generator.load(

            repository.articles

        )

        generator.write(

            output

        )
