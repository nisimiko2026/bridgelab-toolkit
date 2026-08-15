"""
BridgeLab Toolkit
Repository Validator
"""

from __future__ import annotations

from core.models import Article, Issue

from .duplicate_check import DuplicateCheck
from .filename_check import FilenameCheck
from .heading_check import HeadingCheck
from .directory_check import DirectoryCheck


class RepositoryValidator:

    def __init__(self, articles: list[Article]):

        self.articles = articles

        self.checks = [

            DuplicateCheck(),

            FilenameCheck(),

            HeadingCheck(),

            DirectoryCheck(),

        ]

    # ----------------------------------------------------

    def validate(self) -> list[Issue]:

        report: list[Issue] = []

        for check in self.checks:

            report.extend(

                check.run(self.articles)

            )

        return report
