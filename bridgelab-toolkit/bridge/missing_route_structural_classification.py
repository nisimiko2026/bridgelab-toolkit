"""A9.6.1 structural classification of A9.6 production missing routes.

Diagnostic only: no route/rule/policy changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .production_gap_evidence import EvidenceClass, classify_production_gap_evidence


class MissingRouteStructuralFamily(str, Enum):
    RESPONSE_TO_TWO_LEVEL_OPENING = "response-to-two-level-opening"
    RESPONSE_TO_THREE_LEVEL_OPENING = "response-to-three-level-opening"
    OPENER_REBID_AFTER_ONE_LEVEL_RESPONSE = "opener-rebid-after-one-level-response"
    RESPONDER_REBID_AFTER_OPENER_REBID = "responder-rebid-after-opener-rebid"
    LATER_CONTINUATION = "later-continuation"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class StructuralMissingRouteCase:
    seed: int
    auction: str
    depth: int
    seat: int
    family: MissingRouteStructuralFamily
    basis: str


@dataclass(frozen=True, slots=True)
class StructuralMissingRouteGroup:
    family: MissingRouteStructuralFamily
    count: int
    share: float
    seeds: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class StructuralMissingRouteReport:
    runs: int
    missing_route_population: int
    cases: tuple[StructuralMissingRouteCase, ...]
    groups: tuple[StructuralMissingRouteGroup, ...]


def _calls(auction: str) -> tuple[str, ...]:
    if not auction.strip():
        return ()
    # Auction.serialize() is space-separated in the observed A9.6 output.
    # Also tolerate commas for diagnostic fixtures.
    return tuple(auction.replace(",", " ").upper().split())


def _is_one_level_bid(call: str) -> bool:
    return len(call) >= 2 and call[0] == "1" and call[1:] in {"C","D","H","S","NT"}


def _classify_auction(auction: str) -> tuple[MissingRouteStructuralFamily, str]:
    c = _calls(auction)

    # After an uncontested 2-level opening and opponent Pass:
    # e.g. 2S P, 2H P, 2D P.
    if len(c) == 2 and c[0] in {"2C","2D","2H","2S","2NT"} and c[1] == "P":
        return (
            MissingRouteStructuralFamily.RESPONSE_TO_TWO_LEVEL_OPENING,
            "Exact prefix is an uncontested response turn after a two-level opening.",
        )

    # After an uncontested 3-level opening and opponent Pass.
    if len(c) == 2 and c[0] in {"3C","3D","3H","3S","3NT"} and c[1] == "P":
        return (
            MissingRouteStructuralFamily.RESPONSE_TO_THREE_LEVEL_OPENING,
            "Exact prefix is an uncontested response turn after a three-level opening.",
        )

    # 1X P response P -> opener's rebid turn.
    if (
        len(c) == 4
        and _is_one_level_bid(c[0])
        and c[1] == "P"
        and c[3] == "P"
    ):
        return (
            MissingRouteStructuralFamily.OPENER_REBID_AFTER_ONE_LEVEL_RESPONSE,
            "Exact prefix is opener's rebid turn after a one-level opening and response.",
        )

    # 1X P response P opener-rebid P -> responder's rebid turn.
    if (
        len(c) == 6
        and _is_one_level_bid(c[0])
        and c[1] == "P"
        and c[3] == "P"
        and c[5] == "P"
    ):
        return (
            MissingRouteStructuralFamily.RESPONDER_REBID_AFTER_OPENER_REBID,
            "Exact prefix is responder's rebid turn after opener's rebid.",
        )

    if len(c) >= 6:
        return (
            MissingRouteStructuralFamily.LATER_CONTINUATION,
            "Exact prefix is a later auction continuation not covered by the reviewed structural families.",
        )

    return (
        MissingRouteStructuralFamily.OTHER,
        "No reviewed A9.6.1 structural pattern matched this missing route.",
    )


def classify_missing_route_structure(*, start_seed: int = 1, count: int = 1000):
    source = classify_production_gap_evidence(start_seed=start_seed, count=count)
    raw = tuple(
        x.case for x in source.cases
        if x.evidence_class is EvidenceClass.MISSING_ROUTE
    )

    cases = []
    for x in raw:
        family, basis = _classify_auction(x.diagnostic.auction)
        cases.append(
            StructuralMissingRouteCase(
                seed=x.seed,
                auction=x.diagnostic.auction,
                depth=x.depth,
                seat=x.stopped_seat,
                family=family,
                basis=basis,
            )
        )
    cases = tuple(cases)

    buckets = {f: [] for f in MissingRouteStructuralFamily}
    for x in cases:
        buckets[x.family].append(x.seed)

    total = len(cases)
    groups = tuple(
        StructuralMissingRouteGroup(
            family=f,
            count=len(buckets[f]),
            share=0.0 if total == 0 else len(buckets[f]) / total,
            seeds=tuple(buckets[f]),
        )
        for f in MissingRouteStructuralFamily
        if buckets[f]
    )

    assert sum(g.count for g in groups) == total
    return StructuralMissingRouteReport(
        runs=source.runs,
        missing_route_population=total,
        cases=cases,
        groups=groups,
    )
