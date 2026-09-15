"""Read-only diagnostics for early full-auction abstentions."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum

from .deal_analysis import AbstentionCode, AnalysisStatus
from .deal_simulator import AuctionOutcome, FullAuctionBatchResult
from .deals import generate_deal
from .evaluation import evaluate_hand


HCP_BANDS = ("0-5", "6-9", "10-11", "12", "13", "14", "15-17", "18-19", "20-21", "22+")


def hcp_band(hcp: int) -> str:
    for maximum, label in ((5, "0-5"), (9, "6-9"), (11, "10-11"),
                           (12, "12"), (13, "13"), (14, "14"),
                           (17, "15-17"), (19, "18-19"), (21, "20-21")):
        if hcp <= maximum:
            return label
    return "22+"


class DiagnosticCategory(str, Enum):
    NO_ROUTE = "no-route"
    RULE_ABSTAINED_UNEXPLAINED = "rule-abstained-unexplained"
    POLICY_REQUIRED = "policy-required"
    SOURCE_INSUFFICIENT = "source-insufficient"
    UNKNOWN = "unknown"


def classify(code: str | None) -> DiagnosticCategory:
    if code == AbstentionCode.NO_ROUTE.value:
        return DiagnosticCategory.NO_ROUTE
    if code == AbstentionCode.RULE_ABSTAINED.value:
        # AuctionStep does not retain rejected RuleDecision explanations.
        return DiagnosticCategory.RULE_ABSTAINED_UNEXPLAINED
    if code == AbstentionCode.POLICY_REQUIRED.value:
        return DiagnosticCategory.POLICY_REQUIRED
    if code == AbstentionCode.SOURCE_INSUFFICIENT.value:
        return DiagnosticCategory.SOURCE_INSUFFICIENT
    return DiagnosticCategory.UNKNOWN


@dataclass(frozen=True, slots=True)
class RepresentativeCase:
    deal_index: int
    auction_before: tuple[str, ...]
    seat: str
    vulnerability: str
    hand: str
    hcp: int
    suit_lengths: tuple[int, int, int, int]
    shape_class: str
    abstention_code: str | None
    category: DiagnosticCategory
    route_id: str | None
    rule_id: str | None
    sources: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"deal_index": self.deal_index, "auction_before": list(self.auction_before),
                "seat": self.seat, "vulnerability": self.vulnerability,
                "hand": self.hand, "hcp": self.hcp,
                "suit_lengths": list(self.suit_lengths), "shape_class": self.shape_class,
                "abstention_code": self.abstention_code, "category": self.category.value,
                "route_id": self.route_id, "rule_id": self.rule_id,
                "sources": list(self.sources)}


@dataclass(frozen=True, slots=True)
class DiagnosticGroup:
    name: str
    count: int
    hcp_histogram: tuple[tuple[int, int], ...]
    hcp_bands: tuple[tuple[str, int], ...]
    shapes: tuple[tuple[str, int], ...]
    shape_classes: tuple[tuple[str, int], ...]
    abstention_codes: tuple[tuple[str, int], ...]
    categories: tuple[tuple[str, int], ...]
    routes: tuple[tuple[str, int], ...]
    rules: tuple[tuple[str, int], ...]
    pass_candidates: int
    representatives: tuple[RepresentativeCase, ...]

    def to_dict(self) -> dict:
        result = {"name": self.name, "count": self.count,
                  "pass_candidates": self.pass_candidates,
                  "representatives": [case.to_dict() for case in self.representatives]}
        for key in ("hcp_histogram", "hcp_bands", "shapes", "shape_classes",
                    "abstention_codes", "categories", "routes", "rules"):
            result[key] = [[name, count] for name, count in getattr(self, key)]
        return result


@dataclass(frozen=True, slots=True)
class AbstentionAuditReport:
    seed: int
    total_abstains: int
    depth0: DiagnosticGroup
    depth1_count: int
    depth1_groups: tuple[DiagnosticGroup, ...]
    other_depth_count: int
    reproduction_failures: tuple[int, ...]

    def to_dict(self) -> dict:
        return {"seed": self.seed, "total_abstains": self.total_abstains,
                "depth0": self.depth0.to_dict(), "depth1_count": self.depth1_count,
                "depth1_groups": [group.to_dict() for group in self.depth1_groups],
                "other_depth_count": self.other_depth_count,
                "reproduction_failures": list(self.reproduction_failures)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


def _ranked(counter: Counter) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counter.items(), key=lambda item: (-item[1], str(item[0]))))


def _group(name: str, cases: list[RepresentativeCase], *, opening: bool = False) -> DiagnosticGroup:
    hcp = Counter(case.hcp for case in cases)
    bands = Counter(hcp_band(case.hcp) for case in cases)
    shapes = Counter("-".join(map(str, sorted(case.suit_lengths, reverse=True))) for case in cases)
    classes = Counter(case.shape_class for case in cases)
    codes = Counter(case.abstention_code or "unknown" for case in cases)
    categories = Counter(case.category.value for case in cases)
    routes = Counter(case.route_id or "none" for case in cases)
    rules = Counter(case.rule_id or "none" for case in cases)
    selected = sorted(cases, key=lambda case: case.deal_index)[:3]
    if opening:
        # Three per diagnostic HCP stratum; no hand is chosen manually.
        selected = []
        for lower, upper in ((0, 9), (10, 13), (14, 40)):
            selected.extend(sorted((case for case in cases if lower <= case.hcp <= upper),
                                   key=lambda case: case.deal_index)[:3])
    return DiagnosticGroup(
        name, len(cases), tuple(sorted(hcp.items())),
        tuple((band, bands[band]) for band in HCP_BANDS), _ranked(shapes),
        _ranked(classes), _ranked(codes), _ranked(categories), _ranked(routes),
        _ranked(rules),
        sum(case.hcp <= 11 and max(case.suit_lengths) <= 5 for case in cases) if opening else 0,
        tuple(selected),
    )


def build_abstention_audit(batch: FullAuctionBatchResult) -> AbstentionAuditReport:
    """Use recorded stops as authority and reproduce only acting-hand facts."""
    depth0: list[RepresentativeCase] = []
    depth1: dict[str, list[RepresentativeCase]] = defaultdict(list)
    failures: list[int] = []
    other = 0
    for auction in batch.auctions:
        if auction.outcome is not AuctionOutcome.ABSTAIN:
            continue
        if not auction.steps or auction.steps[-1].status is not AnalysisStatus.ABSTAIN:
            raise ValueError(f"deal {auction.deal_index}: missing canonical ABSTAIN step")
        step = auction.steps[-1]
        depth = len(step.auction_before)
        if depth > 1:
            other += 1
            continue
        hand = generate_deal(batch.seed + auction.deal_index).hand(step.seat)
        if hand.serialize() != step.hand or tuple(auction.final_calls) != step.auction_before:
            failures.append(auction.deal_index)
            continue
        evaluation = evaluate_hand(hand)
        case = RepresentativeCase(
            auction.deal_index, step.auction_before, step.seat.value,
            auction.vulnerability.value, hand.serialize(), evaluation.hcp,
            evaluation.suit_lengths, evaluation.shape_class.value,
            step.abstention_code, classify(step.abstention_code),
            step.route_id, step.rule_id, step.sources,
        )
        if depth == 0:
            depth0.append(case)
        else:
            depth1[step.auction_before[0]].append(case)
    if failures:
        raise ValueError(f"canonical acting-hand reproduction failed for deals {failures}")
    groups = tuple(_group(name, depth1[name]) for name in sorted(depth1))
    if len(depth0) + sum(group.count for group in groups) + other != batch.abstain:
        raise ValueError("audit populations do not reconcile with Phase 29G ABSTAIN count")
    return AbstentionAuditReport(batch.seed, batch.abstain, _group("()", depth0, opening=True),
                                 sum(group.count for group in groups), groups, other, ())
