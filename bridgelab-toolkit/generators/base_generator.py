"""
BridgeLab Toolkit
Base Generator
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.models import Article

from .writer import DocumentWriter
from .validator import GeneratorValidator


class BaseGenerator(ABC):
    """
    Base class for all BridgeLab content generators.
    """

    def __init__(self):

        self.articles: list[Article] = []

        self.writer = DocumentWriter()

        self.validator = GeneratorValidator()

    # =========================================================
    # Name
    # =========================================================

    @property
    def name(self) -> str:
        """
        Generator name.
        """

        return self.__class__.__name__

    # =========================================================
    # Load
    # =========================================================

    def load(
        self,
        articles: list[Article],
    ) -> None:
        """
        Load repository articles.
        """

        self.articles = sorted(

            articles,

            key=lambda article: (
                article.metadata.title
                or article.filename
            ).lower(),

        )

    # =========================================================
    # Generate
    # =========================================================

    @abstractmethod
    def generate(self) -> str:
        """
        Generate Markdown.
        """

        raise NotImplementedError

    # =========================================================
    # Validate
    # =========================================================

    def validate(
        self,
        content: str,
    ):
        """
        Validate generated content.
        """

        return self.validator.validate(

            self.name,

            content,

        )

    # =========================================================
    # Post Process
    # =========================================================

    def post_process(
        self,
        content: str,
    ) -> str:
        """
        Optional hook for subclasses.
        """

        return content

    # =========================================================
    # Write
    # =========================================================

    def write(
        self,
        output: Path,
    ):
        """
        Generate, validate and write the document.
        """

        content = self.generate()

        content = self.post_process(content)

        issues = self.validate(content)

        errors = [

            issue

            for issue in issues

            if issue.severity == "Error"

        ]

        if errors:

            raise ValueError(

                f"{self.name} failed validation."

            )

        self.writer.write(

            output,

            content,

        )

        return issues
