"""
Scan command
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from core.repository import Repository
from config import JSON_DATABASE
from config import STATISTICS_JSON

console = Console()


def run(root: Path):

    repo = Repository(root)

    repo.build()

    repo.export_json(JSON_DATABASE)

    repo.export_statistics(STATISTICS_JSON)

    stats = repo.statistics()

    table = Table(title="BridgeLab Repository")

    table.add_column("Item")

    table.add_column("Value", justify="right")

    table.add_row("Articles", str(stats["articles"]))

    table.add_row("Words", f'{stats["words"]:,}')

    table.add_row("Lines", f'{stats["lines"]:,}')

    table.add_row("Bytes", f'{stats["bytes"]:,}')

    table.add_row("Average Words", str(stats["average_words"]))

    console.print(table)

    console.print()

    console.print("[green]Repository successfully scanned.[/green]")
