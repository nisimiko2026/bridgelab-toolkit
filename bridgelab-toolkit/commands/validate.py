"""
BridgeLab Toolkit
Repository Validation Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from core.models import Issue
from core.repository import Repository
from metadata.validator import MetadataValidator
from reporting.base_reporter import BaseReporter
from validator.validator import RepositoryValidator


def run(root: Path) -> None:
    """Validate repository health without modifying source files."""

    typer.echo("Building repository...")

    repository = Repository(root)
    articles = repository.build()

    repository_issues = RepositoryValidator(articles).validate()
    metadata_issues = MetadataValidator().validate(articles)

    issues: list[Issue] = [
        *repository_issues,
        *metadata_issues,
    ]

    errors = [
        issue
        for issue in issues
        if issue.severity == "Error"
    ]
    warnings = [
        issue
        for issue in issues
        if issue.severity == "Warning"
    ]

    reporter = BaseReporter("Repository Validation")
    columns = ["Severity", "Article", "Category", "Message"]

    if errors:
        typer.echo()
        typer.echo("Errors")
        reporter.report(
            columns=columns,
            rows=reporter.issue_rows(errors),
        )

    if warnings:
        typer.echo()
        typer.echo("Warnings")
        reporter.report(
            columns=columns,
            rows=reporter.issue_rows(warnings),
        )

    reporter.summary(
        **{
            "Articles Checked": len(articles),
            "Errors": len(errors),
            "Warnings": len(warnings),
            "Total Issues": len(issues),
        }
    )

    if errors:
        raise typer.Exit(code=1)
