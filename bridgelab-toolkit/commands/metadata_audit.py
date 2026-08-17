"""Read-only metadata-audit command."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

import typer

from config import PROJECT
from metadata.audit import MetadataAuditor


def _console_text(value: str) -> str:
    """Escape characters unsupported by the active Windows console encoding."""

    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return value.encode(encoding, errors="backslashreplace").decode(encoding)


def run(root: Path) -> None:
    auditor = MetadataAuditor(
        root,
        systems_file=PROJECT / "data" / "systems.yaml",
        taxonomy_file=PROJECT / "data" / "taxonomy.yaml",
    )
    records, findings = auditor.audit()

    typer.echo("BridgeLab Metadata Audit (read-only)")
    typer.echo()
    for finding in findings:
        suggested = (
            f" | suggested-group={finding.suggested_canonical_group}"
            if finding.suggested_canonical_group
            else ""
        )
        typer.echo(
            _console_text(
                f"{finding.severity} | {finding.article} | {finding.field} | "
                f"{finding.rule} | observed={finding.observed!r}{suggested} | "
                f"{finding.message}"
            )
        )

    counts = Counter(finding.severity for finding in findings)
    typer.echo()
    typer.echo(f"Articles Checked: {len(records)}")
    typer.echo(f"Errors          : {counts['Error']}")
    typer.echo(f"Warnings        : {counts['Warning']}")
    typer.echo(f"Info            : {counts['Info']}")
    typer.echo(f"Total Findings  : {len(findings)}")
    typer.echo("No source files were modified.")
