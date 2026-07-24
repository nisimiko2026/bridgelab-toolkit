"""
BridgeLab Toolkit
Core Data Models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# ============================================================
# Metadata
# ============================================================

@dataclass(slots=True)
class Metadata:
    """
    Metadata extracted from YAML front matter.
    """

    title: str = ""

    description: str = ""

    category: str = ""

    subcategory: str = ""

    difficulty: str = ""

    tags: list[str] = field(default_factory=list)

    systems: list[str] = field(default_factory=list)

    last_updated: str = ""

    status: str = ""

    aliases: list[str] = field(default_factory=list)


# ============================================================
# Heading
# ============================================================

@dataclass(slots=True)
class Heading:
    """
    Markdown heading.
    """

    level: int

    title: str


# ============================================================
# Article
# ============================================================

@dataclass(slots=True)
class Article:
    """
    BridgeLab article.
    """

    id: str

    filename: str

    path: Path

    relative_path: str

    directory: str

    metadata: Metadata = field(default_factory=Metadata)

    headings: list[Heading] = field(default_factory=list)

    links: list[str] = field(default_factory=list)

    words: int = 0

    lines: int = 0

    characters: int = 0

    def __str__(self):

        return f"{self.metadata.title or self.filename} ({self.relative_path})"


# ============================================================
# Relationship
# ============================================================

@dataclass(slots=True)
class Relationship:
    """
    Relationship between two articles.
    """

    source: str

    target: str

    relation: str

    score: float = 1.0


# ============================================================
# Cross Reference Item
# ============================================================

@dataclass(slots=True)
class CrossReferenceItem:
    """
    Single cross-reference entry.
    """

    article: str

    relation: str

    score: float


# ============================================================
# Cross Reference
# ============================================================

@dataclass(slots=True)
class CrossReference:
    """
    Cross-reference information for one article.
    """

    article: str

    prerequisites: list[CrossReferenceItem] = field(default_factory=list)

    related_topics: list[CrossReferenceItem] = field(default_factory=list)

    related_systems: list[CrossReferenceItem] = field(default_factory=list)

    advanced_topics: list[CrossReferenceItem] = field(default_factory=list)


# ============================================================
# Issue
# ============================================================

@dataclass(slots=True)
class Issue:
    """
    Generic validation/reporting issue.
    """

    severity: str

    article: str

    category: str

    message: str
