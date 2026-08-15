"""
BridgeLab Toolkit
Cross-Reference Reporter
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from core.models import Issue


class CrossReferenceReporter:
    """
    Produces reports for cross-reference validation.
    """

    def __init__(self):

        self.console = Console()

    # ---------------------------------------------------------

    def console_report(
        self,
        issues: list[Issue],
    ):

        table = Table(
            title="Cross-Reference Validation"
        )

        table.add_column("Severity")

        table.add_column("Article")

        table.add_column("Message")

        for issue in issues:

            table.add_row(

                issue.severity,

                issue.article,

                issue.message,

            )

        self.console.print(table)

    # ---------------------------------------------------------

    def summary(
        self,
        issues: list[Issue],
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

    # ---------------------------------------------------------

    def json_report(
        self,
        issues: list[Issue],
        output: Path,
    ):

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = []

        for issue in issues:

            data.append({

                "severity": issue.severity,

                "source": issue.article,

                "category": issue.category,

                "message": issue.message,

            })

        output.write_text(

            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),

            encoding="utf-8",

        )
