"""
BridgeLab Toolkit
Configuration
"""

import os
from pathlib import Path


# ============================================================
# Project Paths
# ============================================================

PROJECT = Path(__file__).resolve().parent

ROOT = PROJECT


# ============================================================
# Repository
# ============================================================

# BridgeLab Markdown repository

REPOSITORY = Path(
    os.environ.get(
        "BRIDGELAB_REPOSITORY",
        ROOT.parent / "knowledge",
    )
).expanduser().resolve()


# ============================================================
# Output
# ============================================================

OUTPUT = ROOT / "output"

DOCS = OUTPUT / "docs"

REPORTS = OUTPUT / "reports"


# ============================================================
# Repository Data
# ============================================================

JSON_DATABASE = OUTPUT / "repository.json"

STATISTICS_JSON = OUTPUT / "statistics.json"


# ============================================================
# Validation Reports
# ============================================================

METADATA_JSON = REPORTS / "metadata_validation.json"

CROSS_REFERENCE_JSON = REPORTS / "cross_references.json"

KNOWLEDGE_JSON = REPORTS / "knowledge_validation.json"


# ============================================================
# Generated Documents
# ============================================================

GLOSSARY = DOCS / "glossary.md"

ACRONYMS = DOCS / "acronyms.md"

BIBLIOGRAPHY = DOCS / "bibliography.md"


# ============================================================
# Create Output Directories
# ============================================================

OUTPUT.mkdir(
    parents=True,
    exist_ok=True,
)

DOCS.mkdir(
    parents=True,
    exist_ok=True,
)

REPORTS.mkdir(
    parents=True,
    exist_ok=True,
)
