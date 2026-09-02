"""Deterministic, descriptive document-role classification."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import PurePath, PurePosixPath


class DocumentRole(str, Enum):
    """Structural role derived solely from a canonical relative path."""

    ARTICLE = "article"
    SECTION_INDEX = "section_index"
    DOMAIN_INDEX = "domain_index"


def classify_document_role(relative_path: str | PurePath) -> DocumentRole:
    """Classify a Markdown document from its canonical relative path."""

    raw_path = str(relative_path)
    if not raw_path or "\x00" in raw_path:
        raise ValueError("Document path must be a non-empty relative path")

    canonical = raw_path.replace("\\", "/")
    if (
        canonical.startswith("/")
        or canonical.endswith("/")
        or re.match(r"^[A-Za-z]:", canonical)
    ):
        raise ValueError("Document path must be relative")

    components = canonical.split("/")
    if any(component in {"", ".", ".."} for component in components):
        raise ValueError("Document path must be canonical and traversal-free")

    path = PurePosixPath(*components)
    if path.suffix.casefold() != ".md":
        raise ValueError("Document path must identify a Markdown file")

    stem = path.stem.casefold()
    structural = (
        stem == "index"
        or stem.startswith("index-")
        or stem.endswith("-index")
    )
    if not structural:
        return DocumentRole.ARTICLE
    if len(path.parts) == 2:
        return DocumentRole.DOMAIN_INDEX
    return DocumentRole.SECTION_INDEX
