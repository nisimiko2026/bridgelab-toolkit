"""A9.6 missing-route classification.

This layer is diagnostic only. It classifies production NO_ROUTE cases without
changing routing, bidding rules, recommendations, or partnership policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .production_gap_evidence import (
    EvidenceClass,
    classify_production_gap_evidence,
)
from .evidence_review_contract import ReviewClassification


class MissingRouteFamily(str, Enum):
    LATER_SEAT_OPENING = "later-seat-opening"
    OTHER_MISSING_ROUTE = "other-missing-route"


@dataclass(frozen=True, slots=True)
class MissingRouteCase:
    seed: int
    auction: str
    depth: int
    seat: int
    family: MissingRouteFamily
    classification: ReviewClassification
    basis: str


@dataclass(frozen=True, slots=True)
class MissingRouteGroup:
    family: MissingRouteFamily
    classification: ReviewClassification
    count: int
    seeds: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class MissingRouteClassificationReport:
    runs: int
    abstained: int
    missing_route_population: int
    cases: tuple[MissingRouteCase, ...]
    groups: tuple[MissingRouteGroup, ...]


def _calls(auction: str) -> tuple[str, ...]:
    # Existing serialized auctions are comma-separated in current production
    # artifacts; tolerate whitespace and the empty prefix.
    if not auction.strip():
        return ()
    return tuple(x.strip().upper() for x in auction.split(",") if x.strip())


def _later_seat_opening_prefix(auction: str) -> bool:
    calls = _calls(auction)
    return calls in (("P", "P"), ("P", "P", "P"))


def _classify(case) -> MissingRouteCase:
    diagnostic = case.diagnostic
    auction = diagnostic.auction

    if _later_seat_opening_prefix(auction):
        return MissingRouteCase(
            seed=case.seed,
            auction=auction,
            depth=case.depth,
            seat=case.stopped_seat,
            family=MissingRouteFamily.LATER_SEAT_OPENING,
            classification=ReviewClassification.CORE_GAP,
            basis=(
                "No production route owns the exact later-seat opening prefix "
                "P-P or P-P-P. A9.5 now contains explicit opening-policy evidence "
                "for this structural route family; this classification does not "
                "select a bid or change production behavior."
            ),
        )

    return MissingRouteCase(
        seed=case.seed,
        auction=auction,
        depth=case.depth,
        seat=case.stopped_seat,
        family=MissingRouteFamily.OTHER_MISSING_ROUTE,
        classification=ReviewClassification.INSUFFICIENT_EVIDENCE,
        basis=(
            "The exact auction has no production route, but A9.6 has insufficient "
            "reviewed evidence to infer the missing system, convention, treatment, "
            "partnership agreement, or bridge judgment."
        ),
    )


def classify_missing_routes(*, start_seed: int = 1, count: int = 1000):
    source = classify_production_gap_evidence(
        start_seed=start_seed, count=count
    )
    raw = tuple(
        x.case for x in source.cases
        if x.evidence_class is EvidenceClass.MISSING_ROUTE
    )
    cases = tuple(_classify(x) for x in raw)

    buckets = {}
    for x in cases:
        key = (x.family, x.classification)
        buckets.setdefault(key, []).append(x.seed)

    groups = tuple(
        MissingRouteGroup(family, classification, len(seeds), tuple(seeds))
        for (family, classification), seeds in sorted(
            buckets.items(), key=lambda kv: (kv[0][0].value, kv[0][1].value)
        )
    )

    assert len(cases) == len(raw)
    assert sum(x.count for x in groups) == len(cases)

    return MissingRouteClassificationReport(
        runs=source.runs,
        abstained=source.abstained,
        missing_route_population=len(raw),
        cases=cases,
        groups=groups,
    )
