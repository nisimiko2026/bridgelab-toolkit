"""
BridgeLab Toolkit
Core data models

Author: BridgeLab
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# ------------------------------------------------------------
# YAML Metadata
# ------------------------------------------------------------

@dataclass(slots=True)
class Metadata:
    """YAML metadata extracted from an article."""

    title: str = ""

    description: str = ""

    category: str = ""

    subcategory: str = ""

    difficulty: str = ""

    tags: list[str] = field(default_factory=list)

    systems: list[str] = field(default_factory=list)

    last_updated: str = ""


# ------------------------------------------------------------
# Heading
# ------------------------------------------------------------

@dataclass(slots=True)
class Heading:
    """Single markdown heading."""

    level: int

    title: str


# ------------------------------------------------------------
# Article
# ------------------------------------------------------------

@dataclass(slots=True)
class Article:
    """
    Represents one markdown article.
    """

    # Stable internal identifier

    id: str

    # File information

    filename: str

    path: Path

    relative_path: Path

    directory: str

    # Metadata

    metadata: Metadata = field(default_factory=Metadata)

    # Markdown structure

    headings: list[Heading] = field(default_factory=list)

    # Statistics

    word_count: int = 0

    line_count: int = 0

    size_bytes: int = 0

    # Links

    outgoing_links: list[str] = field(default_factory=list)

    incoming_links: list[str] = field(default_factory=list)

    # Validation

    warnings: list[str] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.metadata.title

    @property
    def category(self) -> str:
        return self.metadata.category

    @property
    def subcategory(self) -> str:
        return self.metadata.subcategory

    def __str__(self):

        return f"{self.title} ({self.relative_path})"
