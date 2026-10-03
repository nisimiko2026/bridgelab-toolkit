"""A8.11 production abstention extraction.

Replays only the terminal production abstention context from the existing
SAYC coverage benchmark.  It does not change production bidding behavior and
does not reinterpret an abstention as a policy or engine defect.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .abstention_diagnostics import (
    AbstentionDiagnostic,
    AbstentionReason,
    evaluate_with_abstention_diagnostic,
)
from .auction import Auction
from .auction_simulation import SimulationStopReason
from .bidding_rules import BiddingContext, SystemContext
from .models import Seat, Vulnerability
from .sayc_coverage_benchmark import run_sayc_coverage_benchmark
from .sayc_route_configuration import create_standard_sayc_router


@dataclass(frozen=True, slots=True)
class ProductionAbstentionCase:
    seed: int
    deal: str
    stopped_seat: Seat
    auction: str
    depth: int
    diagnostic: AbstentionDiagnostic

    @property
    def replay_key(self) -> str:
        return f"sayc-production@1:seed:{self.seed}"


@dataclass(frozen=True, slots=True)
class ProductionGapGroup:
    reason: AbstentionReason
    route_id: str | None
    auction: str
    count: int
    seeds: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ProductionGapExtractionReport:
    start_seed: int
    runs: int
    completed: int
    abstained: int
    cases: tuple[ProductionAbstentionCase, ...]
    groups: tuple[ProductionGapGroup, ...]
    reason_counts: tuple[tuple[AbstentionReason, int], ...]

    def count(self, reason: AbstentionReason) -> int:
        return dict(self.reason_counts).get(reason, 0)


def _rebuild_auction(dealer: Seat, calls) -> Auction:
    auction = Auction(dealer)
    for call in calls:
        auction.add(call)
    return auction


def extract_production_abstentions(
    *, start_seed: int = 1, count: int = 1000
) -> ProductionGapExtractionReport:
    """Run current production coverage and diagnose each terminal abstention."""
    coverage = run_sayc_coverage_benchmark(start_seed=start_seed, count=count)

    cases: list[ProductionAbstentionCase] = []
    for batch_case in coverage.batch.cases:
        result = batch_case.result
        if result.stop_reason is not SimulationStopReason.NO_RECOMMENDATION:
            continue

        seat = result.stopped_seat
        assert seat is not None

        # Passive E/W fixtures always recommend Pass.  A terminal
        # NO_RECOMMENDATION in this benchmark must therefore be a production
        # N/S stop; keep this invariant explicit.
        if seat not in (Seat.NORTH, Seat.SOUTH):
            raise AssertionError(
                f"unexpected fixture-seat abstention at seed {batch_case.deal.seed}"
            )

        auction = _rebuild_auction(result.dealer, result.calls_added)
        context = BiddingContext.create(
            hand=batch_case.deal.mapping[seat],
            auction=auction,
            vulnerability=coverage.batch.vulnerability,
            system=SystemContext("SAYC"),
        )
        router = create_standard_sayc_router()
        diagnosed = evaluate_with_abstention_diagnostic(router, context)

        if diagnosed.result.has_recommendation or diagnosed.abstention is None:
            raise AssertionError(
                f"replayed terminal context no longer abstains at seed {batch_case.deal.seed}"
            )

        cases.append(
            ProductionAbstentionCase(
                seed=batch_case.deal.seed,
                deal=batch_case.deal.serialize(),
                stopped_seat=seat,
                auction=auction.serialize(),
                depth=len(result.steps),
                diagnostic=diagnosed.abstention,
            )
        )

    reason_counter = Counter(x.diagnostic.reason for x in cases)
    buckets: dict[tuple[AbstentionReason, str | None, str], list[int]] = {}
    for item in cases:
        key = (item.diagnostic.reason, item.diagnostic.route_id, item.auction)
        buckets.setdefault(key, []).append(item.seed)

    # Stable semantic ordering, never frequency ranking.
    groups = tuple(
        ProductionGapGroup(reason, route_id, auction, len(seeds), tuple(seeds))
        for (reason, route_id, auction), seeds in sorted(
            buckets.items(),
            key=lambda kv: (
                kv[0][0].value,
                kv[0][1] or "",
                kv[0][2],
            ),
        )
    )
    reason_counts = tuple(
        (reason, reason_counter.get(reason, 0)) for reason in AbstentionReason
    )

    if len(cases) != coverage.metrics.abstained:
        raise AssertionError("diagnosed abstention count differs from production benchmark")

    return ProductionGapExtractionReport(
        start_seed=start_seed,
        runs=count,
        completed=coverage.metrics.completed,
        abstained=coverage.metrics.abstained,
        cases=tuple(cases),
        groups=groups,
        reason_counts=reason_counts,
    )
