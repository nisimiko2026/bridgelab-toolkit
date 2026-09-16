"""Read-only source-readiness audit for an explicit opening Pass."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .auction import Auction, Call
from .deal_simulator import AuctionOutcome, FullAuctionBatchResult
from .evaluation import evaluate_hand
from .models import Hand, Seat


class OpeningPassSupport(str, Enum):
    SOURCE_INSUFFICIENT = "source-insufficient"
    CURRENT_COVERAGE_BOUNDARY = "current-coverage-boundary"


@dataclass(frozen=True, slots=True)
class OpeningPassCase:
    deal_index: int
    dealer: str
    vulnerability: str
    hand: str
    hcp: int
    suit_lengths: tuple[int, int, int, int]
    shape_class: str
    support: OpeningPassSupport
    explanation: str

    def to_dict(self) -> dict:
        return {"deal_index": self.deal_index, "dealer": self.dealer,
                "vulnerability": self.vulnerability, "hand": self.hand,
                "hcp": self.hcp, "suit_lengths": list(self.suit_lengths),
                "shape_class": self.shape_class, "support": self.support.value,
                "explanation": self.explanation}


@dataclass(frozen=True, slots=True)
class PassedOutFinding:
    calls: tuple[str, ...]
    actors: tuple[str, ...]
    complete_after_each: tuple[bool, ...]
    is_passed_out: bool
    final_contract: str | None

    def to_dict(self) -> dict:
        return {"calls": list(self.calls), "actors": list(self.actors),
                "complete_after_each": list(self.complete_after_each),
                "is_passed_out": self.is_passed_out,
                "final_contract": self.final_contract}


@dataclass(frozen=True, slots=True)
class OpeningPassPolicyReport:
    seed: int
    requested_deals: int
    depth0_abstains: int
    diagnostic_screen_count: int
    pass_supported_count: int
    source_insufficient_count: int
    coverage_boundary_count: int
    representatives: tuple[OpeningPassCase, ...]
    passed_out: PassedOutFinding

    def to_dict(self) -> dict:
        return {"seed": self.seed, "requested_deals": self.requested_deals,
                "depth0_abstains": self.depth0_abstains,
                "diagnostic_screen_count": self.diagnostic_screen_count,
                "pass_supported_count": self.pass_supported_count,
                "source_insufficient_count": self.source_insufficient_count,
                "coverage_boundary_count": self.coverage_boundary_count,
                "representatives": [case.to_dict() for case in self.representatives],
                "passed_out": self.passed_out.to_dict()}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


def audit_passed_out_auction(dealer: Seat = Seat.NORTH) -> PassedOutFinding:
    auction = Auction(dealer)
    actors, complete = [], []
    for _ in range(4):
        actors.append(auction.next_seat.value)
        call = Call.parse("P")
        if call not in auction.legal_calls():
            raise ValueError("canonical Auction rejected a legal Pass")
        auction.add(call)
        complete.append(auction.is_complete)
    return PassedOutFinding(
        tuple(call.serialize() for call in auction.calls), tuple(actors),
        tuple(complete), auction.is_passed_out,
        None if auction.final_contract is None else auction.final_contract.serialize(),
    )


def build_opening_pass_policy_report(batch: FullAuctionBatchResult) -> OpeningPassPolicyReport:
    """Classify the Phase 29I screen without treating it as a Pass policy."""
    screen: list[OpeningPassCase] = []
    boundaries: list[OpeningPassCase] = []
    depth0 = 0
    for auction in batch.auctions:
        if auction.outcome is not AuctionOutcome.ABSTAIN or not auction.steps:
            continue
        step = auction.steps[-1]
        if step.auction_before:
            continue
        depth0 += 1
        evaluation = evaluate_hand(Hand.parse(step.hand))
        base = (auction.deal_index, auction.dealer.value, auction.vulnerability.value,
                step.hand, evaluation.hcp, evaluation.suit_lengths,
                evaluation.shape_class.value)
        if evaluation.hcp <= 11 and max(evaluation.suit_lengths) <= 5:
            screen.append(OpeningPassCase(
                *base, OpeningPassSupport.SOURCE_INSUFFICIENT,
                "The repository has no authoritative positive opening-Pass policy for this hand domain.",
            ))
        elif evaluation.hcp >= 12:
            boundaries.append(OpeningPassCase(
                *base, OpeningPassSupport.CURRENT_COVERAGE_BOUNDARY,
                "A stronger unresolved opening boundary must not be consumed by a Pass fallback.",
            ))
    representatives = tuple(sorted(screen, key=lambda item: item.deal_index)[:3] +
                            sorted(boundaries, key=lambda item: item.deal_index)[:3])
    return OpeningPassPolicyReport(
        batch.seed, batch.requested_deals, depth0, len(screen), 0, len(screen),
        len(boundaries), representatives, audit_passed_out_auction(),
    )
