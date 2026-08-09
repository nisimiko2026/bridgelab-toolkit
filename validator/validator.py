"""
BridgeLab Toolkit
Repository Validator
"""

from __future__ import annotations

from .duplicate_check import DuplicateCheck
from .filename_check import FilenameCheck
from .yaml_check import YAMLCheck
from .heading_check import HeadingCheck
from .directory_check import DirectoryCheck


class RepositoryValidator:

    def __init__(self, articles):

        self.articles = articles

        self.checks = [

            DuplicateCheck(),

            FilenameCheck(),

            YAMLCheck(),

            HeadingCheck(),

            DirectoryCheck(),

        ]

    # ----------------------------------------------------

    def validate(self):

        report = []

        for check in self.checks:

            report.extend(

                check.run(self.articles)

            )

        return report
