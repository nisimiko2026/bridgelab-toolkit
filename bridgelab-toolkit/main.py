"""
BridgeLab Toolkit

Main entry point for the BridgeLab Editorial Toolkit.
"""

from pathlib import Path

import typer

from config import ROOT
from commands.scan import run as scan_command

# ---------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------

app = typer.Typer(
    help="BridgeLab Editorial Toolkit",
    add_completion=False,
    no_args_is_help=True,
)


# ---------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Future Commands
# ---------------------------------------------------------------------

# @app.command()
# def metadata():
#     """Validate metadata."""
#     pass


# @app.command()
# def audit():
#     """Audit repository."""
#     pass


# @app.command()
# def glossary():
#     """Generate glossary."""
#     pass


# @app.command()
# def crossrefs():
#     """Generate cross references."""
#     pass


# @app.command()
# def build():
#     """Run complete toolkit."""
#     pass


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    app()


if __name__ == "__main__":

    main()
