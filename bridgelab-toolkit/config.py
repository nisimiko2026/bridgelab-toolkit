"""
BridgeLab Toolkit

Main entry point for the BridgeLab Editorial Toolkit.
"""

from pathlib import Path

import typer

from config import ROOT

from commands.scan import run as scan_command
from commands.metadata import run as metadata_command
from commands.crossrefs import run as crossrefs_command


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
        ROOT,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Scan the BridgeLab repository.
    """

    scan_command(root)


# ============================================================
# Metadata
# ============================================================

@app.command()
def metadata(
    root: Path = typer.Option(
        ROOT,
        "--root",
        "-r",
        help="BridgeLab repository root",
    ),
):
    """
    Validate metadata.
    """

    metadata_command(root)


# ============================================================
# Cross References
# ============================================================

@app.command()
def crossrefs(
    root: Path = typer.Option(
        ROOT,
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
# Future Commands
# ============================================================

# @app.command()
# def glossary():
#     pass


# @app.command()
# def bibliography():
#     pass


# @app.command()
# def audit():
#     pass


# @app.command()
# def statistics():
#     pass


# @app.command()
# def build():
#     pass


# ============================================================
# Main
# ============================================================

def main():

    app()


if __name__ == "__main__":

    main()
