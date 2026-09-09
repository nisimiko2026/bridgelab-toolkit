"""Audit-only taxonomy for ordinary SAYC benchmark abstentions.

The categories describe existing software control flow.  They do not assert
that BridgeLab should bid, that a bridge rule is missing, or that a stopped
position is source-ready for implementation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
import re

from bridge.auction import Auction
from bridge.auction_simulation import SimulationStopReason
from bridge.batch_simulation import BatchSimulationCase, BatchSimulationReport
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.sayc_coverage_benchmark import (
    SaycCoverageBenchmarkReport,
    run_sayc_coverage_benchmark,
)
from bridge.sayc_route_configuration import create_standard_sayc_router


_POLICY_REFERENCE = re.compile(r"\bpolicy\b", re.IGNORECASE)


class AbstentionCategory(str, Enum):
    NO_ROUTE_MATCH = "NO_ROUTE_MATCH"
    ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN = (
        "ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN"
    )
    ROUTE_MATCH_RULE_ABSTAIN = "ROUTE_MATCH_RULE_ABSTAIN"


@dataclass(frozen=True, slots=True)
class AbstentionObservation:
    seed: int
    stopped_seat: str
    auction_prefix: tuple[str, ...]
    matched_route_id: str | None
    category: AbstentionCategory
    rejection_rule_ids: tuple[str, ...]
    rejection_explanations: tuple[str, ...]
    stop_reason: str

    @property
    def has_policy_reference(self) -> bool:
        return _has_policy_reference(self.rejection_explanations)


@dataclass(frozen=True, slots=True)
class AbstentionTaxonomyAudit:
    start_seed: int
    corpus_size: int
    seeds: tuple[int, ...]
    production_calls: int
    completed_auctions: int
    abstentions: int
    observations: tuple[AbstentionObservation, ...]
    category_counts: tuple[tuple[str, int], ...]
    stopped_prefix_counts: tuple[tuple[tuple[str, ...], int], ...]
    policy_route_counts: tuple[tuple[str, int], ...]
    route_count: int

    @property
    def classified_total(self) -> int:
        return len(self.observations)

    def count(self, category: AbstentionCategory) -> int:
        return dict(self.category_counts).get(category.value, 0)


def reconstruct_stopped_context(
    case: BatchSimulationCase,
    batch: BatchSimulationReport,
) -> BiddingContext:
    """Reconstruct the exact public context at a NO_RECOMMENDATION stop."""
    result = case.result
    if result.stop_reason is not SimulationStopReason.NO_RECOMMENDATION:
        raise ValueError("case did not stop with NO_RECOMMENDATION")
    if result.stopped_seat is None:
        raise ValueError("NO_RECOMMENDATION case has no stopped seat")

    auction = Auction(result.dealer, tuple(result.final_auction.split()))
    return BiddingContext.create(
        hand=case.deal.mapping[result.stopped_seat],
        auction=auction,
        vulnerability=batch.vulnerability,
        system=SystemContext("SAYC"),
    )


def _has_policy_reference(explanations: tuple[str, ...]) -> bool:
    """Detect only an explicit policy reference in an existing rejection."""
    return any(_POLICY_REFERENCE.search(explanation) for explanation in explanations)


def classify_abstentions(
    report: SaycCoverageBenchmarkReport,
) -> AbstentionTaxonomyAudit:
    """Classify every NO_RECOMMENDATION case in an existing benchmark report."""
    router = create_standard_sayc_router()
    observations: list[AbstentionObservation] = []
    category_counts: Counter[str] = Counter()
    prefix_counts: Counter[tuple[str, ...]] = Counter()
    policy_route_counts: Counter[str] = Counter()

    for case in report.batch.cases:
        if case.result.stop_reason is not SimulationStopReason.NO_RECOMMENDATION:
            continue

        context = reconstruct_stopped_context(case, report.batch)
        prefix = tuple(context.auction.serialize().split())
        match = router.match(context)

        if match is None:
            category = AbstentionCategory.NO_ROUTE_MATCH
            route_id = None
            rule_ids: tuple[str, ...] = ()
            explanations: tuple[str, ...] = ()
        else:
            evaluated = match.engine.evaluate(context)
            if evaluated.has_recommendation:
                raise RuntimeError(
                    "reconstructed NO_RECOMMENDATION context produced a recommendation"
                )
            rejected = tuple(
                decision for decision in evaluated.decisions if not decision.applicable
            )
            rule_ids = tuple(decision.rule_id for decision in rejected)
            explanations = tuple(decision.explanation for decision in rejected)
            route_id = match.route_id
            if _has_policy_reference(explanations):
                category = AbstentionCategory.ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN
                policy_route_counts[route_id] += 1
            else:
                category = AbstentionCategory.ROUTE_MATCH_RULE_ABSTAIN

        observation = AbstentionObservation(
            seed=case.deal.seed,
            stopped_seat=context.seat.value,
            auction_prefix=prefix,
            matched_route_id=route_id,
            category=category,
            rejection_rule_ids=rule_ids,
            rejection_explanations=explanations,
            stop_reason=case.result.stop_reason.value,
        )
        observations.append(observation)
        category_counts[category.value] += 1
        prefix_counts[prefix] += 1

    ordered_categories = tuple(
        (category.value, category_counts[category.value])
        for category in AbstentionCategory
    )
    ordered_prefixes = tuple(
        sorted(prefix_counts.items(), key=lambda item: (-item[1], item[0]))
    )
    ordered_policy_routes = tuple(
        sorted(policy_route_counts.items(), key=lambda item: (-item[1], item[0]))
    )
    metrics = report.metrics
    return AbstentionTaxonomyAudit(
        start_seed=report.batch.start_seed,
        corpus_size=report.batch.count,
        seeds=tuple(case.deal.seed for case in report.batch.cases),
        production_calls=metrics.production_calls,
        completed_auctions=metrics.completed,
        abstentions=metrics.abstained,
        observations=tuple(observations),
        category_counts=ordered_categories,
        stopped_prefix_counts=ordered_prefixes,
        policy_route_counts=ordered_policy_routes,
        route_count=len(router.routes),
    )


def run_abstention_taxonomy_audit(
    *, start_seed: int = 1, count: int = 10_000
) -> AbstentionTaxonomyAudit:
    """Run and classify the unchanged ordinary deterministic benchmark."""
    return classify_abstentions(
        run_sayc_coverage_benchmark(start_seed=start_seed, count=count)
    )


def _prefix_label(prefix: tuple[str, ...]) -> str:
    return " ".join(prefix) if prefix else "<empty auction>"


def _print_summary(audit: AbstentionTaxonomyAudit) -> None:
    print(f"corpus = {audit.corpus_size}")
    print(f"production calls = {audit.production_calls}")
    print(f"completed auctions = {audit.completed_auctions}")
    print(f"abstentions = {audit.abstentions}")
    print()
    for category in AbstentionCategory:
        print(f"{category.value} = {audit.count(category)}")
    print(f"classified total = {audit.classified_total}")
    print()
    print("top stopped prefixes:")
    for prefix, count in audit.stopped_prefix_counts[:9]:
        print(f"{_prefix_label(prefix)} = {count}")
    print("policy-referenced route breakdown:")
    for route_id, count in audit.policy_route_counts:
        print(f"{route_id} = {count}")


if __name__ == "__main__":
    _print_summary(run_abstention_taxonomy_audit())
