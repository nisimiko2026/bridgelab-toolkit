"""
BridgeLab Toolkit
Base Reporter
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from core.models import Issue


class BaseReporter:
    """
    Base class for all BridgeLab reporters.
    """

    def __init__(self, title: str):

        self.console = Console()

        self.title = title

    # =========================================================
    # Console Report
    # =========================================================

    def report(
        self,
        issues: list[Issue],
    ):

        rows = self.build_rows(issues)

        table = Table(title=self.title)

        table.add_column("Severity")

        table.add_column("Article")

        table.add_column("Category")

        table.add_column("Message")

        for row in rows:

            table.add_row(*row)

        self.console.print(table)

        self.summary(issues)

    # =========================================================
    # Build Rows
    # =========================================================

    def build_rows(
        self,
        issues: list[Issue],
    ) -> list[list[str]]:

        rows = []

        for issue in issues:

            rows.append(

                [

                    issue.severity,

                    issue.article,

                    issue.category,

                    issue.message,

                ]

            )

        return rows

    # =========================================================
    # Summary
    # =========================================================

    def summary(
        self,
        issues: list[Issue],
    ):

        errors = sum(

            1

            for issue in issues

            if issue.severity == "Error"

        )

        warnings = sum(

            1

            for issue in issues

            if issue.severity == "Warning"

        )

        information = sum(

            1

            for issue in issues

            if issue.severity == "Info"

        )

        self.console.print()

        self.console.print(f"Errors      : {errors}")

        self.console.print(f"Warnings    : {warnings}")

        self.console.print(f"Information : {information}")

        self.console.print(f"Total       : {len(issues)}")

    # =========================================================
    # JSON Export
    # =========================================================

    def export(
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

            data.append(

                {

                    "severity": issue.severity,

                    "article": issue.article,

                    "category": issue.category,

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
