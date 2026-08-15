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
    YAML metadata extracted from a BridgeLab article.
    """

    title: str = ""
    description: str = ""

    category: str = ""
    subcategory: str = ""
    difficulty: str = ""

    tags: list[str] = field(default_factory=list)
    systems: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    acronyms: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)

    last_updated: str = ""
    status: str = ""


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
    relative_path: Path
    directory: str

    metadata: Metadata = field(default_factory=Metadata)

    headings: list[Heading] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    words: int = 0
    lines: int = 0
    characters: int = 0

    def __str__(self) -> str:

        return (
            f"{self.metadata.title or self.filename} "
            f"({self.relative_path})"
        )


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
    One cross-reference entry.
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
    Cross references for one article.
    """

    article: str

    prerequisites: list[CrossReferenceItem] = field(default_factory=list)

    related_topics: list[CrossReferenceItem] = field(default_factory=list)

    related_systems: list[CrossReferenceItem] = field(default_factory=list)

    advanced_topics: list[CrossReferenceItem] = field(default_factory=list)


# ============================================================
# Knowledge Entity
# ============================================================

@dataclass(slots=True)
class Entity:
    """
    Knowledge entity extracted from the encyclopedia.
    """

    name: str

    category: str

    article: str

    frequency: int = 1


# ============================================================
# Validation Issue
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
