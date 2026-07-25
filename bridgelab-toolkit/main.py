"""
BridgeLab Toolkit

Main entry point.
"""

from pathlib import Path

import typer

from config import REPOSITORY

from commands.scan import run as scan_command
from commands.metadata import run as metadata_command
from commands.crossrefs import run as crossrefs_command
from commands.glossary import run as glossary_command
from commands.acronyms import run as acronyms_command
from commands.bibliography import run as bibliography_command
from commands.knowledge import run as knowledge_command
from commands.build import run as build_command


# ============================================================
# Application
# ============================================================

app = typer.Typer(
    help="BridgeLab Editorial Toolkit",
    add_completion=False,
    no_args_is_help=True,
)


# ============================================================
# Scan Repository
# ============================================================

@app.command()
def scan(
    root: Path = typer.Option(
        REPOSITORY,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Scan the repository.
    """

    scan_command(root)


# ============================================================
# Metadata
# ============================================================

@app.command()
def metadata(
    root: Path = typer.Option(
        REPOSITORY,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Validate article metadata.
    """

    metadata_command(root)


# ============================================================
# Cross References
# ============================================================

@app.command()
def crossrefs(
    root: Path = typer.Option(
        REPOSITORY,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Generate and validate cross references.
    """

    crossrefs_command(root)


# ============================================================
# Glossary
# ============================================================

@app.command()
def glossary(
    root: Path = typer.Option(
        REPOSITORY,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Generate glossary.
    """

    glossary_command(root)


# ============================================================
# Acronyms
# ============================================================

@app.command()
def acronyms(
    root: Path = typer.Option(
        REPOSITORY,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Generate acronym list.
    """

    acronyms_command(root)


# ============================================================
# Bibliography
# ============================================================

@app.command()
def bibliography(
    root: Path = typer.Option(
        REPOSITORY,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Generate bibliography.
    """

    bibliography_command(root)


# ============================================================
# Knowledge
# ============================================================

@app.command()
def knowledge(
    root: Path = typer.Option(
        REPOSITORY,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Analyze repository knowledge.
    """

    knowledge_command(root)


# ============================================================
# Build
# ============================================================

@app.command()
def build(
    root: Path = typer.Option(
        REPOSITORY,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Generate all BridgeLab documents.
    """

    build_command(root)


# ============================================================
# Main
# ============================================================

def main():

    app()


if __name__ == "__main__":

    main()
