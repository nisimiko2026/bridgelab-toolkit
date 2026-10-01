"""Canonical, provider-neutral records for external bridge corpora.

This module is deliberately free of bidding-system inference.  Provenance and
unknown metadata are preserved so external observations can be used as evidence
without silently becoming BridgeLab policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .auction import Auction, Contract
from .deals import Deal
from .models import Card, Seat, Vulnerability

@dataclass(frozen=True, slots=True)
class SourceProvenance:
    provider: str
    source: str
    record_id: str | None = None
    language: str | None = None
    notation: str | None = None
    provider_version: str | None = None
    transformations: tuple[str, ...] = ()
    raw_reference: str | None = None

@dataclass(frozen=True, slots=True)
class CanonicalBoardRecord:
    provenance: SourceProvenance
    dealer: Seat
    vulnerability: Vulnerability
    deal: Deal | None = None
    auction: Auction | None = None
    contract: Contract | None = None
    opening_lead: Card | None = None
    tricks: int | None = None
    board_number: int | None = None
    ns_system: str | None = None
    ew_system: str | None = None

    def __post_init__(self) -> None:
        if self.auction is not None and self.auction.dealer is not self.dealer:
            raise ValueError("auction dealer conflicts with board dealer")
        if self.tricks is not None and not 0 <= self.tricks <= 13:
            raise ValueError("tricks must be between 0 and 13")
