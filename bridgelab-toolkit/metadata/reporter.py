"""
BridgeLab Toolkit
Metadata Reporter
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .validator import MetadataIssue


class MetadataReporter:
    """
    Produces reports for metadata validation.
    """

    def __init__(self):

        self.console = Console()

    # ---------------------------------------------------------

    def console_report(
        self,
        issues: list[MetadataIssue],
    ):

        table = Table(
            title="Metadata Validation Report"
        )

        table.add_column("Severity")

        table.add_column("Article")

        table.add_column("Field")

        table.add_column("Message")

        for issue in issues:

            table.add_row(

                issue.severity,

                issue.article,

                issue.field,

                issue.message,

            )

        self.console.print(table)

    # ---------------------------------------------------------

    def json_report(
        self,
        issues: list[MetadataIssue],
        output: Path,
    ):

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = []

        for issue in issues:

            data.append(

                {

                    "severity": issue.severity,

                    "article": issue.article,

                    "field": issue.field,

                    "message": issue.message,

                }

            )

        output.write_text(

            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),

            encoding="utf-8",
        )

    # ---------------------------------------------------------

    def summary(
        self,
        issues: list[MetadataIssue],
    ):

        errors = sum(
            1
            for i in issues
            if i.severity == "Error"
        )

        warnings = sum(
            1
            for i in issues
            if i.severity == "Warning"
        )

        self.console.print()

        self.console.print(
            f"Errors   : {errors}"
        )

        self.console.print(
            f"Warnings : {warnings}"
        )

        self.console.print(
            f"Total    : {len(issues)}"
        )
