"""Deterministic observation of Phase 29G full-auction stopping records."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json

from .deal_analysis import AnalysisStatus
from .deal_simulator import AuctionOutcome, FullAuctionBatchResult


@dataclass(frozen=True, slots=True, order=True)
class StoppingSignature:
    """Canonical auction history; absolute dealer/seat statistics stay separate."""

    calls: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StoppingExample:
    deal_index: int
    dealer: str
    vulnerability: str
    seat: str
    successful_depth: int
    signature: StoppingSignature
    abstention_code: str | None
    rule_id: str | None
    route_id: str | None
    sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RankedStop:
    signature: StoppingSignature
    count: int
    percent_of_abstains: float
    successful_depth: int
    abstention_codes: tuple[tuple[str, int], ...]
    stopping_seats: tuple[tuple[str, int], ...]
    representative_deal_indexes: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class FullAuctionCoverageReport:
    seed: int
    requested_deals: int
    completed_simulations: int
    complete: int
    abstain: int
    errors: int
    completion_rate: float
    total_decisions: int
    successful_recommendations: int
    abstaining_decisions: int
    error_decisions: int
    ranked_stops: tuple[RankedStop, ...]
    stopping_seats: tuple[tuple[str, int], ...]
    abstention_codes: tuple[tuple[str, int], ...]
    stop_depths: tuple[tuple[int, int], ...]
    stopping_routes: tuple[tuple[str, int], ...]
    stopping_rules: tuple[tuple[str, int], ...]
    successful_routes: tuple[tuple[str, int], ...]
    error_messages: tuple[tuple[str, int], ...]
    examples: tuple[StoppingExample, ...]

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible values without domain-object reprs."""
        return {
            "seed": self.seed,
            "requested_deals": self.requested_deals,
            "completed_simulations": self.completed_simulations,
            "complete": self.complete,
            "abstain": self.abstain,
            "errors": self.errors,
            "completion_rate": self.completion_rate,
            "total_decisions": self.total_decisions,
            "successful_recommendations": self.successful_recommendations,
            "abstaining_decisions": self.abstaining_decisions,
            "error_decisions": self.error_decisions,
            "ranked_stops": [
                {
                    "calls": list(item.signature.calls),
                    "count": item.count,
                    "percent_of_abstains": item.percent_of_abstains,
                    "successful_depth": item.successful_depth,
                    "abstention_codes": [list(pair) for pair in item.abstention_codes],
                    "stopping_seats": [list(pair) for pair in item.stopping_seats],
                    "representative_deal_indexes": list(item.representative_deal_indexes),
                }
                for item in self.ranked_stops
            ],
            "stopping_seats": [list(pair) for pair in self.stopping_seats],
            "abstention_codes": [list(pair) for pair in self.abstention_codes],
            "stop_depths": [list(pair) for pair in self.stop_depths],
            "stopping_routes": [list(pair) for pair in self.stopping_routes],
            "stopping_rules": [list(pair) for pair in self.stopping_rules],
            "successful_routes": [list(pair) for pair in self.successful_routes],
            "error_messages": [list(pair) for pair in self.error_messages],
            "examples": [
                {
                    "deal_index": item.deal_index,
                    "dealer": item.dealer,
                    "vulnerability": item.vulnerability,
                    "seat": item.seat,
                    "successful_depth": item.successful_depth,
                    "calls": list(item.signature.calls),
                    "abstention_code": item.abstention_code,
                    "rule_id": item.rule_id,
                    "route_id": item.route_id,
                    "sources": list(item.sources),
                }
                for item in self.examples
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


def _ranked(counter: Counter[str]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counter.items(), key=lambda pair: (-pair[1], pair[0])))


def build_full_auction_coverage_report(
    batch: FullAuctionBatchResult,
) -> FullAuctionCoverageReport:
    """Summarize recorded decisions; never rerun a simulator or bidding rule."""
    if not isinstance(batch, FullAuctionBatchResult):
        raise TypeError("batch must be FullAuctionBatchResult")
    groups: dict[StoppingSignature, list[StoppingExample]] = defaultdict(list)
    seats: Counter[str] = Counter()
    codes: Counter[str] = Counter()
    depths: Counter[int] = Counter()
    stop_routes: Counter[str] = Counter()
    stop_rules: Counter[str] = Counter()
    routes: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    recommendations = abstains = error_decisions = 0
    examples: list[StoppingExample] = []

    for auction in batch.auctions:
        for step in auction.steps:
            if step.status is AnalysisStatus.RECOMMENDATION:
                recommendations += 1
                if step.route_id:
                    routes[step.route_id] += 1
            elif step.status is AnalysisStatus.ABSTAIN:
                abstains += 1
            elif step.status is AnalysisStatus.ERROR:
                error_decisions += 1
        if auction.outcome is AuctionOutcome.ERROR:
            errors[auction.error or "unknown error"] += 1
        if auction.outcome is not AuctionOutcome.ABSTAIN:
            continue
        step = auction.steps[-1]
        depth = sum(item.status is AnalysisStatus.RECOMMENDATION for item in auction.steps[:-1])
        signature = StoppingSignature(step.auction_before)
        example = StoppingExample(
            auction.deal_index, auction.dealer.value, auction.vulnerability.value,
            step.seat.value, depth, signature, step.abstention_code,
            step.rule_id, step.route_id, step.sources,
        )
        groups[signature].append(example)
        examples.append(example)
        seats[example.seat] += 1
        depths[depth] += 1
        if example.abstention_code:
            codes[example.abstention_code] += 1
        if example.route_id:
            stop_routes[example.route_id] += 1
        if example.rule_id:
            stop_rules[example.rule_id] += 1

    ranked_stops = tuple(
        RankedStop(
            signature=signature,
            count=len(items),
            percent_of_abstains=100 * len(items) / batch.abstain,
            successful_depth=items[0].successful_depth,
            abstention_codes=_ranked(Counter(item.abstention_code for item in items if item.abstention_code)),
            stopping_seats=_ranked(Counter(item.seat for item in items)),
            representative_deal_indexes=tuple(sorted(item.deal_index for item in items)[:3]),
        )
        for signature, items in sorted(
            groups.items(), key=lambda pair: (-len(pair[1]), pair[0].calls)
        )
    )
    return FullAuctionCoverageReport(
        batch.seed, batch.requested_deals, batch.completed_simulations,
        batch.complete, batch.abstain, batch.errors, batch.completion_rate,
        batch.total_steps, recommendations, abstains, error_decisions,
        ranked_stops, _ranked(seats), _ranked(codes),
        tuple(sorted(depths.items())), _ranked(stop_routes), _ranked(stop_rules),
        _ranked(routes), _ranked(errors),
        tuple(sorted(examples, key=lambda item: item.deal_index)),
    )
