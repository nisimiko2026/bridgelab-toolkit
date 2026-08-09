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

    typer.echo("Writing metadata...")

    updated = writer.write_all(articles)

    typer.echo()

    typer.echo(f"Updated articles : {updated}")

    typer.secho(
        "Metadata enrichment completed.",
        fg=typer.colors.GREEN,
    )
