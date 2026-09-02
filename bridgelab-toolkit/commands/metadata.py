
"""
BridgeLab Toolkit
Metadata Command
"""

from pathlib import Path

from rich.console import Console

from config import METADATA_JSON

from core.repository import Repository

from metadata.validator import MetadataValidator

from reporting.base_reporter import BaseReporter


console = Console()


def run(root: Path):

    console.print()
    console.print("[bold cyan]Metadata Validation[/bold cyan]")
    console.print()

    # ---------------------------------------------------------
    # Build Repository
    # ---------------------------------------------------------

    repository = Repository(root)

    repository.build()

    # ---------------------------------------------------------
    # Validate Metadata
    # ---------------------------------------------------------

    validator = MetadataValidator()

    issues = validator.validate(

        repository.articles

    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    reporter = BaseReporter(

        "Metadata Validation"

    )

    reporter.report(

        columns=[

            "Severity",

            "Article",

            "Category",

            "Message",

        ],

        rows=reporter.issue_rows(

            issues

        ),

    )

    reporter.summary(

        Errors=sum(

            issue.severity == "Error"

            for issue in issues

        ),

        Warnings=sum(

            issue.severity == "Warning"

            for issue in issues

        ),

        Total=len(issues),

    )

    reporter.export(

        [

            {

                "severity": issue.severity,

                "article": issue.article,

                "category": issue.category,

                "message": issue.message,

            }

            for issue in issues

        ],

        METADATA_JSON,

    )

    console.print()

    console.print(

        "[green]Metadata validation complete.[/green]"

    )
