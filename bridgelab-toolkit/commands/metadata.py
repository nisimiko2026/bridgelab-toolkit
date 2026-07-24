"""
BridgeLab Toolkit
Metadata Command
"""

from pathlib import Path

from rich.console import Console

from core.repository import Repository

from metadata.validator import MetadataValidator
from metadata.reporter import MetadataReporter

from config import OUTPUT

console = Console()


def run(root: Path):

    console.print()

    console.print("[bold cyan]Metadata Validation[/bold cyan]")

    console.print()

    # ---------------------------------------------
    # Build repository
    # ---------------------------------------------

    repo = Repository(root)

    repo.build()

    # ---------------------------------------------
    # Validate metadata
    # ---------------------------------------------

    validator = MetadataValidator()

    issues = validator.validate(
        repo.articles
    )

    # ---------------------------------------------
    # Report
    # ---------------------------------------------

    reporter = MetadataReporter()

    reporter.console_report(issues)

    reporter.summary(issues)

    reporter.json_report(

        issues,

        OUTPUT / "metadata_validation.json"

    )

    console.print()

    console.print(

        "[green]Metadata validation complete.[/green]"

    )
