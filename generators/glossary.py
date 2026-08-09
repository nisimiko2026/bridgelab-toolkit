"""
BridgeLab Toolkit
Glossary Generator
"""

from __future__ import annotations

from knowledge.extractor import EntityExtractor
from knowledge.glossary import GlossaryBuilder

from .base_generator import BaseGenerator


class GlossaryGenerator(BaseGenerator):
    """
    Generates the BridgeLab glossary.
    """

    def generate(self) -> str:

        extractor = EntityExtractor()

        entities = extractor.extract(

            self.articles,

        )

        builder = GlossaryBuilder()

        return builder.build(

            entities,

        )
