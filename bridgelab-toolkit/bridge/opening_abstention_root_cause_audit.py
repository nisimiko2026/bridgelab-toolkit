"""Audit existing SAYC opening decisions without changing production behavior."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .auction import Auction
from .bidding_rules import BiddingContext, SystemContext
from .deal_analysis import AnalysisStatus
from .deal_simulator import AuctionOutcome, FullAuctionBatchResult
from .deals import generate_deal
from .evaluation import evaluate_hand, high_card_points
from .models import Hand
from .sayc_route_configuration import create_standard_sayc_router


class OpeningRootCause(str, Enum):
    CONTROLLED_EQUAL_MAJOR_BOUNDARY = "controlled-equal-major-boundary"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class OpeningRuleTrace:
    rule_id: str
    status: str
    candidate: str | None
    explanation: str
    sources: tuple[str, ...]
    priority: int

    def to_dict(self) -> dict:
        return {"rule_id": self.rule_id, "status": self.status,
                "candidate": self.candidate, "explanation": self.explanation,
                "sources": list(self.sources), "priority": self.priority}


@dataclass(frozen=True, slots=True)
class OpeningRootCauseCase:
    deal_index: int
    dealer: str
    vulnerability: str
    hand: str
    hcp: int
    suit_lengths: tuple[int, int, int, int]
    shape_class: str
    auction_before: tuple[str, ...]
    production_status: str
    production_abstention_code: str | None
    route_id: str | None
    rule_trace: tuple[OpeningRuleTrace, ...]
    root_cause: OpeningRootCause
    note: str

    def to_dict(self) -> dict:
        return {"deal_index": self.deal_index, "dealer": self.dealer,
                "vulnerability": self.vulnerability, "hand": self.hand,
                "hcp": self.hcp, "suit_lengths": list(self.suit_lengths),
                "shape_class": self.shape_class,
                "auction_before": list(self.auction_before),
                "production_status": self.production_status,
                "production_abstention_code": self.production_abstention_code,
                "route_id": self.route_id,
                "rule_trace": [trace.to_dict() for trace in self.rule_trace],
                "root_cause": self.root_cause.value, "note": self.note}


@dataclass(frozen=True, slots=True)
class OpeningRootCauseReport:
    seed: int
    depth0_abstains: int
    strong_depth0_count: int
    strong_cases: tuple[OpeningRootCauseCase, ...]

    def to_dict(self) -> dict:
        return {"seed": self.seed, "depth0_abstains": self.depth0_abstains,
                "strong_depth0_count": self.strong_depth0_count,
                "strong_cases": [case.to_dict() for case in self.strong_cases]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


def _trace_case(batch: FullAuctionBatchResult, auction, router) -> OpeningRootCauseCase:
    step = auction.steps[-1]
    hand = generate_deal(batch.seed + auction.deal_index).hand(auction.dealer)
    if step.seat is not auction.dealer or step.hand != hand.serialize():
        raise ValueError(f"deal {auction.deal_index}: canonical dealer hand mismatch")
    context = BiddingContext.create(
        hand=hand, auction=Auction(auction.dealer),
        vulnerability=auction.vulnerability, system=SystemContext("SAYC"),
    )
    match = router.match(context)
    if match is None or match.route_id != step.route_id:
        raise ValueError(f"deal {auction.deal_index}: opening route mismatch")
    result = router.evaluate(context)
    if result.has_recommendation:
        raise ValueError(f"deal {auction.deal_index}: rule trace contradicts production ABSTAIN")
    evaluation = evaluate_hand(hand)
    trace = tuple(
        OpeningRuleTrace(
            decision.rule_id,
            "recommendation" if decision.applicable else "not-applicable",
            None if decision.candidate is None else decision.candidate.serialize(),
            decision.explanation,
            tuple(source.serialize() for source in decision.sources),
            decision.priority,
        ) for decision in result.decisions
    )
    # This diagnosis describes the actual controlled predicates, never a new bid.
    equal_majors = (
        12 <= evaluation.hcp <= 21
        and evaluation.suit_lengths[0] == evaluation.suit_lengths[1] >= 5
        and any(item.rule_id == "sayc.opening.1h" and "strictly longer" in item.explanation for item in trace)
        and any(item.rule_id == "sayc.opening.1s" and "strictly longer" in item.explanation for item in trace)
        and all(not item.candidate for item in trace)
    )
    cause = (OpeningRootCause.CONTROLLED_EQUAL_MAJOR_BOUNDARY
             if equal_majors else OpeningRootCause.UNKNOWN)
    note = (
        "Both major rules require their suit to be strictly longer than the other major; "
        "minor rules defer when a five-card major exists. The controlled registry has no "
        "equal-major tie treatment."
        if equal_majors else "The existing rule trace does not establish a narrower cause."
    )
    return OpeningRootCauseCase(
        auction.deal_index, auction.dealer.value, auction.vulnerability.value,
        hand.serialize(), evaluation.hcp, evaluation.suit_lengths,
        evaluation.shape_class.value, step.auction_before, step.status.value,
        step.abstention_code, step.route_id, trace, cause, note,
    )


def build_opening_root_cause_report(
    batch: FullAuctionBatchResult, *, minimum_hcp: int = 12,
) -> OpeningRootCauseReport:
    """Find strong opening stops from stored hands; regenerate only those deals."""
    router = create_standard_sayc_router()
    cases: list[OpeningRootCauseCase] = []
    depth0 = 0
    for auction in batch.auctions:
        if auction.outcome is not AuctionOutcome.ABSTAIN:
            continue
        if not auction.steps or auction.steps[-1].status is not AnalysisStatus.ABSTAIN:
            raise ValueError(f"deal {auction.deal_index}: missing ABSTAIN step")
        step = auction.steps[-1]
        if step.auction_before:
            continue
        depth0 += 1
        if high_card_points(Hand.parse(step.hand)) >= minimum_hcp:
            cases.append(_trace_case(batch, auction, router))
    return OpeningRootCauseReport(batch.seed, depth0, len(cases), tuple(cases))
