"""
BridgeLab Toolkit
Base Reporter
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from core.models import Issue


class BaseReporter:
    """
    Generic reporter for the BridgeLab Toolkit.
    """

    def __init__(self, title: str):

        self.console = Console()

        self.title = title

    # =========================================================
    # Console Report
    # =========================================================

    def report(
        self,
        columns: list[str],
        rows: list[list[str]],
    ) -> None:
        """
        Display a Rich table.
        """

        table = Table(title=self.title)

        for column in columns:

            table.add_column(column)

        for row in rows:

            table.add_row(*row)

        self.console.print(table)

    # =========================================================
    # Issue Rows
    # =========================================================

    def issue_rows(
        self,
        issues: list[Issue],
    ) -> list[list[str]]:
        """
        Convert Issue objects into table rows.
        """

        return [

            [

                issue.severity,

                issue.article,

                issue.category,

                issue.message,

            ]

            for issue in issues

        ]

    # =========================================================
    # Summary
    # =========================================================

    def summary(
        self,
        **values: int,
    ) -> None:
        """
        Display summary values.
        """

        self.console.print()

        for key, value in values.items():

            self.console.print(

                f"{key:<12}: {value}"

            )

    # =========================================================
    # JSON Export
    # =========================================================

    def export(
        self,
        data: Any,
        output: Path,
    ) -> None:
        """
        Export data as JSON.
        """

        output.parent.mkdir(

            parents=True,

            exist_ok=True,

        )

        output.write_text(

            json.dumps(

                data,

                indent=4,

                ensure_ascii=False,

            ),

            encoding="utf-8",

        )
