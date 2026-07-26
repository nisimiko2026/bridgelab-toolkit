"""
BridgeLab Toolkit
Metadata Enrichment Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from core.scanner import RepositoryScanner
from enrichment.writer import MetadataWriter


# ============================================================
# Command
# ============================================================

def run(root: Path) -> None:
    """
    Insert YAML front matter into Markdown files that
    do not already contain metadata.
    """

    scanner = RepositoryScanner(root)
    articles = scanner.scan()

    writer = MetadataWriter()

    scanned = 0
    modified = 0

    for article in articles:

        scanned += 1

        if writer.write(article):
            modified += 1

    typer.echo()
    typer.echo("Metadata enrichment complete.")
    typer.echo()
    typer.echo(f"Files scanned    : {scanned}")
    typer.echo(f"Files modified   : {modified}")
    typer.echo(f"Already complete : {scanned - modified}")
    typer.echo()
