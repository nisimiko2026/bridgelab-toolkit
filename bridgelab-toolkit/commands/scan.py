"""
BridgeLab Toolkit
Repository Scan Command
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from config import JSON_DATABASE, STATISTICS_JSON

from core.repository import Repository


console = Console()


def run(root: Path):

    console.print()

    console.print("[bold cyan]BridgeLab Repository[/bold cyan]")

    console.print()

    # ---------------------------------------------------------
    # Build Repository
    # ---------------------------------------------------------

    repo = Repository(root)

    repo.build()

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    repo.export_json(

        JSON_DATABASE

    )

    repo.export_statistics(

        STATISTICS_JSON

    )

    stats = repo.statistics()

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    table = Table()

    table.add_column("Item")

    table.add_column(
        "Value",
        justify="right",
    )

    table.add_row(
        "Articles",
        f'{stats["articles"]:,}',
    )

    table.add_row(
        "Words",
        f'{stats["words"]:,}',
    )

    table.add_row(
        "Lines",
        f'{stats["lines"]:,}',
    )

    table.add_row(
        "Characters",
        f'{stats["characters"]:,}',
    )

    table.add_row(
        "Average Words",
        f'{stats["average_words"]:,}',
    )

    table.add_row(
        "Average Lines",
        f'{stats["average_lines"]:,}',
    )

    table.add_row(
        "Average Characters",
        f'{stats["average_characters"]:,}',
    )

    console.print(table)

    console.print()

    console.print(

        "[green]Repository successfully scanned.[/green]"

    )
