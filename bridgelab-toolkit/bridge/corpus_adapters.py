"""Provider boundary for corpus ingestion."""
from __future__ import annotations
from typing import Any, Mapping, Protocol
from .corpus import CanonicalBoardRecord

class CorpusAdapter(Protocol):
    provider_name: str
    def adapt(self, raw: Mapping[str, Any]) -> CanonicalBoardRecord: ...
