"""
BridgeLab Toolkit
Global Configuration
"""

from pathlib import Path

# ============================================================
# Toolkit Information
# ============================================================

TOOLKIT_NAME = "BridgeLab Editorial Toolkit"

VERSION = "1.0.0"

# ============================================================
# Repository
# ============================================================

# BridgeLab root directory.
# Since the toolkit resides inside the BridgeLab project,
# ROOT is the parent directory of the toolkit.

TOOLKIT_ROOT = Path(__file__).resolve().parent

ROOT = TOOLKIT_ROOT.parent

# ============================================================
# Output Directories
# ============================================================

OUTPUT = TOOLKIT_ROOT / "output"

REPORTS = TOOLKIT_ROOT / "reports"

TESTS = TOOLKIT_ROOT / "tests"

# ============================================================
# Generated Files
# ============================================================

JSON_DATABASE = OUTPUT / "articles.json"

STATISTICS_JSON = OUTPUT / "statistics.json"

STATISTICS_TEXT = OUTPUT / "statistics.txt"

VALIDATION_JSON = OUTPUT / "validation.json"

VALIDATION_TEXT = OUTPUT / "validation.txt"

# ============================================================
# Repository Rules
# ============================================================

MARKDOWN_EXTENSION = ".md"

IGNORE_DIRECTORIES = {

    ".git",

    ".github",

    ".idea",

    ".vscode",

    "__pycache__",

    ".pytest_cache",

    ".mypy_cache",

    ".venv",

    "venv",

    "node_modules",

    "build",

    "dist",

    "output",

    "reports",

}

# ============================================================
# Metadata Rules
# ============================================================

REQUIRED_METADATA = [

    "title",

    "description",

]

DEFAULT_DIFFICULTY = "Intermediate"

DEFAULT_STATUS = "draft"

# ============================================================
# Heading Rules
# ============================================================

REQUIRED_HEADINGS = [

    "Overview",

    "Summary",

]

# ============================================================
# Supported Index Names
# ============================================================

INDEX_FILES = {

    "index.md",

    "bidding-index.md",

    "conventions-index.md",

    "duplicate-bridge-index.md",

    "opening-bids-index.md",

    "responses-index.md",

    "relay-index.md",

    "slam-bidding-index.md",

    "transfers-index.md",

}

# ============================================================
# Report Formatting
# ============================================================

REPORT_WIDTH = 100

INDENT = 4
