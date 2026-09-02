"""
BridgeLab Toolkit
Enrich Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from core.repository import Repository

from enrichment.generator import MetadataGenerator
from enrichment.reference_detector import ReferenceDetector
from enrichment.system_detector import SystemDetector
from enrichment.tagger import TagGenerator
from enrichment.writer import MetadataWriter


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
    apply: bool = False,
) -> None:
    """
    Enrich repository metadata.
    """

    typer.echo("=" * 60)
    typer.echo("BridgeLab Metadata Enrichment")
    typer.echo("=" * 60)
    typer.echo()

    #
    # Load repository
    #

    typer.echo(f"Repository : {root}")

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles   : {len(articles)}")
    typer.echo()

    #
    # Build enrichment pipeline
    #

    tagger = TagGenerator()

    system_detector = SystemDetector()

    reference_detector = ReferenceDetector(
        articles=articles,
    )

    generator = MetadataGenerator(
        tagger=tagger,
        system_detector=system_detector,
        reference_detector=reference_detector,
    )

    writer = MetadataWriter()

    #
    # Generate metadata
    #

    typer.echo("Generating metadata...")

    generator.enrich_all(articles)

    #
    # Write metadata
    #

    if apply:

        typer.echo("Writing metadata...")

        updated = writer.write_all(articles)

        for article, message in writer.skipped:
            typer.secho(
                f"Skipped {article.relative_path.as_posix()}: {message}",
                fg=typer.colors.YELLOW,
            )

        typer.echo()
        typer.echo(f"Updated articles : {updated}")

        typer.secho(
            "Metadata enrichment completed.",
            fg=typer.colors.GREEN,
        )

        return

    proposed = writer.preview_all(articles)

    for article, message in writer.skipped:
        typer.secho(
            f"Skipped {article.relative_path.as_posix()}: {message}",
            fg=typer.colors.YELLOW,
        )

    typer.echo()

    typer.echo(f"Dry run: {proposed} articles would be updated.")

    typer.secho(
        "No source files were modified. Re-run with --apply to write changes.",
        fg=typer.colors.YELLOW,
    )
