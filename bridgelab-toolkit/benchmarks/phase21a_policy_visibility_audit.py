"""Audit-only visibility for policy-gated production route control flow.

The audit joins Phase 20B structural observations with Phase 20C behavioral
observations.  It reports software control flow only; it does not judge bridge
correctness or infer whether a policy was consulted.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from benchmarks.phase20b_route_reachability_audit import (
    RouteInventoryEntry,
    RouteReachabilityAudit,
    run_route_reachability_audit,
)
from benchmarks.phase20c_abstention_taxonomy_audit import (
    AbstentionCategory,
    AbstentionTaxonomyAudit,
    classify_abstentions,
    reconstruct_stopped_context,
)
from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.sayc_coverage_benchmark import (
    SaycCoverageBenchmarkReport,
    run_sayc_coverage_benchmark,
)
from bridge.sayc_route_configuration import create_standard_sayc_router

DISCLAIMER = "Software control-flow visibility only; not bridge correctness."


class PolicyRequirementState(str, Enum):
    NOT_POLICY_GATED = "NOT_POLICY_GATED"
    POLICY_GATED = "POLICY_GATED"


class PolicyObservationState(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    POLICY_REFERENCED = "POLICY_REFERENCED"
    UNKNOWN = "UNKNOWN"


class DecisionOutcome(str, Enum):
    RECOMMEND = "RECOMMEND"
    ABSTAIN = "ABSTAIN"
    NO_ROUTE = "NO_ROUTE"


@dataclass(frozen=True, slots=True)
class StaticRoutePolicyVisibility:
    registration_order: int
    route_id: str
    auction_prefix: tuple[str, ...]
    engine_type: str
    rule_ids: tuple[str, ...]
    ownership: str
    policy_requirement: PolicyRequirementState
    policy_dependencies: tuple[str, ...]
    structural_reachability: str


@dataclass(frozen=True, slots=True)
class PolicyDecisionEvent:
    seed: int
    decision_number: int
    auction_before: tuple[str, ...]
    seat: str
    matched_route_id: str | None
    policy_dependencies: tuple[str, ...]
    policy_observation: PolicyObservationState
    outcome: DecisionOutcome
    recommended_rule_id: str | None
    applicable_rule_ids: tuple[str, ...]
    rejected_rule_ids: tuple[str, ...]
    rejection_explanations: tuple[str, ...]
    system_options: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class RoutePolicySummary:
    route_id: str
    observed: bool
    event_count: int
    recommendation_count: int
    abstention_count: int
    policy_referenced_abstention_count: int
    observation_state_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class PolicyVisibilityAudit:
    routes: tuple[StaticRoutePolicyVisibility, ...]
    events: tuple[PolicyDecisionEvent, ...]
    route_summaries: tuple[RoutePolicySummary, ...]
    no_route_count: int
    taxonomy_counts: tuple[tuple[str, int], ...]
    policy_route_counts: tuple[tuple[str, int], ...]
    dependency_incidences: tuple[tuple[str, int], ...]
    corpus_size: int
    production_calls: int
    completed_auctions: int
    abstentions: int

    @property
    def policy_gated_route_count(self) -> int:
        return sum(
            route.policy_requirement is PolicyRequirementState.POLICY_GATED
            for route in self.routes
        )


def _static_route(entry: RouteInventoryEntry) -> StaticRoutePolicyVisibility:
    requirement = (
        PolicyRequirementState.POLICY_GATED
        if entry.policy_dependencies
        else PolicyRequirementState.NOT_POLICY_GATED
    )
    return StaticRoutePolicyVisibility(
        registration_order=entry.registration_order,
        route_id=entry.route_id,
        auction_prefix=entry.auction_prefix,
        engine_type=entry.engine_type,
        rule_ids=entry.rule_ids,
        ownership=entry.ownership.value,
        policy_requirement=requirement,
        policy_dependencies=entry.policy_dependencies,
        structural_reachability=entry.configuration_reachability.value,
    )


def _context_for_step(case, step, report: SaycCoverageBenchmarkReport) -> BiddingContext:
    auction = Auction(case.result.dealer, tuple(step.auction_before.split()))
    system = SystemContext("SAYC")
    return BiddingContext.create(
        hand=case.deal.mapping[step.seat],
        auction=auction,
        vulnerability=report.batch.vulnerability,
        system=system,
        seat=step.seat,
    )


def _recommendation_events(
    report: SaycCoverageBenchmarkReport,
    routes_by_id: dict[str, StaticRoutePolicyVisibility],
) -> list[PolicyDecisionEvent]:
    router = create_standard_sayc_router()
    events: list[PolicyDecisionEvent] = []
    for case in report.batch.cases:
        for step in case.result.steps:
            if step.rule_id.startswith("benchmark.fixture."):
                continue
            context = _context_for_step(case, step, report)
            match = router.match(context)
            if match is None:
                raise RuntimeError(
                    f"retained recommendation has no route: seed={case.deal.seed}, "
                    f"decision={step.number}"
                )
            route = routes_by_id.get(match.route_id)
            if route is None:
                raise RuntimeError(f"matched route is absent from Phase 20B: {match.route_id}")
            if route.policy_requirement is not PolicyRequirementState.POLICY_GATED:
                continue

            evaluated = match.engine.evaluate(context)
            recommended = evaluated.recommended
            if recommended is None or recommended.rule_id != step.rule_id:
                actual = None if recommended is None else recommended.rule_id
                raise RuntimeError(
                    f"retained recommendation mismatch: seed={case.deal.seed}, "
                    f"decision={step.number}, retained={step.rule_id!r}, "
                    f"evaluated={actual!r}"
                )
            applicable = tuple(
                decision.rule_id for decision in evaluated.decisions if decision.applicable
            )
            rejected = tuple(
                decision for decision in evaluated.decisions if not decision.applicable
            )
            events.append(
                PolicyDecisionEvent(
                    seed=case.deal.seed,
                    decision_number=step.number,
                    auction_before=tuple(step.auction_before.split()),
                    seat=step.seat.value,
                    matched_route_id=match.route_id,
                    policy_dependencies=route.policy_dependencies,
                    policy_observation=PolicyObservationState.UNKNOWN,
                    outcome=DecisionOutcome.RECOMMEND,
                    recommended_rule_id=step.rule_id,
                    applicable_rule_ids=applicable,
                    rejected_rule_ids=tuple(item.rule_id for item in rejected),
                    rejection_explanations=tuple(item.explanation for item in rejected),
                    system_options=context.system.options,
                )
            )
    return events


def _terminal_events(
    report: SaycCoverageBenchmarkReport,
    taxonomy: AbstentionTaxonomyAudit,
    routes_by_id: dict[str, StaticRoutePolicyVisibility],
) -> list[PolicyDecisionEvent]:
    cases_by_seed = {case.deal.seed: case for case in report.batch.cases}
    events: list[PolicyDecisionEvent] = []
    for observation in taxonomy.observations:
        case = cases_by_seed[observation.seed]
        context = reconstruct_stopped_context(case, report.batch)
        if observation.category is AbstentionCategory.NO_ROUTE_MATCH:
            outcome = DecisionOutcome.NO_ROUTE
            dependencies: tuple[str, ...] = ()
            policy_state = PolicyObservationState.NOT_APPLICABLE
        else:
            route = routes_by_id.get(observation.matched_route_id or "")
            if route is None:
                raise RuntimeError(
                    "Phase 20C matched route is absent from Phase 20B: "
                    f"{observation.matched_route_id!r}"
                )
            if route.policy_requirement is not PolicyRequirementState.POLICY_GATED:
                continue
            outcome = DecisionOutcome.ABSTAIN
            dependencies = route.policy_dependencies
            policy_state = (
                PolicyObservationState.POLICY_REFERENCED
                if observation.category
                is AbstentionCategory.ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN
                else PolicyObservationState.UNKNOWN
            )
        events.append(
            PolicyDecisionEvent(
                seed=observation.seed,
                decision_number=len(case.result.steps) + 1,
                auction_before=observation.auction_prefix,
                seat=observation.stopped_seat,
                matched_route_id=observation.matched_route_id,
                policy_dependencies=dependencies,
                policy_observation=policy_state,
                outcome=outcome,
                recommended_rule_id=None,
                applicable_rule_ids=(),
                rejected_rule_ids=observation.rejection_rule_ids,
                rejection_explanations=observation.rejection_explanations,
                system_options=context.system.options,
            )
        )
    return events


def _route_summaries(
    routes: tuple[StaticRoutePolicyVisibility, ...],
    events: tuple[PolicyDecisionEvent, ...],
) -> tuple[RoutePolicySummary, ...]:
    by_route: dict[str, list[PolicyDecisionEvent]] = {
        route.route_id: [] for route in routes
    }
    for event in events:
        if event.matched_route_id is not None:
            by_route[event.matched_route_id].append(event)

    summaries = []
    for route in routes:
        observed = by_route[route.route_id]
        states = Counter(event.policy_observation.value for event in observed)
        summaries.append(
            RoutePolicySummary(
                route_id=route.route_id,
                observed=bool(observed),
                event_count=len(observed),
                recommendation_count=sum(
                    event.outcome is DecisionOutcome.RECOMMEND for event in observed
                ),
                abstention_count=sum(
                    event.outcome is DecisionOutcome.ABSTAIN for event in observed
                ),
                policy_referenced_abstention_count=sum(
                    event.policy_observation
                    is PolicyObservationState.POLICY_REFERENCED
                    for event in observed
                ),
                observation_state_counts=tuple(sorted(states.items())),
            )
        )
    return tuple(summaries)


def build_policy_visibility_audit(
    report: SaycCoverageBenchmarkReport,
    *,
    structural_audit: RouteReachabilityAudit | None = None,
) -> PolicyVisibilityAudit:
    """Build immutable visibility records from one retained benchmark report."""
    structural = structural_audit or run_route_reachability_audit()
    routes = tuple(_static_route(entry) for entry in structural.inventory)
    routes_by_id = {route.route_id: route for route in routes}
    taxonomy = classify_abstentions(report)

    events = _recommendation_events(report, routes_by_id)
    events.extend(_terminal_events(report, taxonomy, routes_by_id))
    ordered_events = tuple(
        sorted(
            events,
            key=lambda event: (
                event.seed,
                event.decision_number,
                event.outcome.value,
                event.matched_route_id or "",
            ),
        )
    )
    dependencies = Counter(
        dependency for route in routes for dependency in route.policy_dependencies
    )
    return PolicyVisibilityAudit(
        routes=routes,
        events=ordered_events,
        route_summaries=_route_summaries(routes, ordered_events),
        no_route_count=taxonomy.count(AbstentionCategory.NO_ROUTE_MATCH),
        taxonomy_counts=taxonomy.category_counts,
        policy_route_counts=taxonomy.policy_route_counts,
        dependency_incidences=tuple(sorted(dependencies.items())),
        corpus_size=taxonomy.corpus_size,
        production_calls=taxonomy.production_calls,
        completed_auctions=taxonomy.completed_auctions,
        abstentions=taxonomy.abstentions,
    )


def run_policy_visibility_audit(
    *, start_seed: int = 1, count: int = 10_000
) -> PolicyVisibilityAudit:
    """Run the ordinary benchmark exactly once and join its retained evidence."""
    report = run_sayc_coverage_benchmark(start_seed=start_seed, count=count)
    return build_policy_visibility_audit(report)


def _print_summary(audit: PolicyVisibilityAudit) -> None:
    gated = tuple(
        route for route in audit.routes
        if route.policy_requirement is PolicyRequirementState.POLICY_GATED
    )
    outcomes = Counter(event.outcome.value for event in audit.events)
    states = Counter(event.policy_observation.value for event in audit.events)

    print("STATIC ROUTE POLICY SUMMARY")
    print(f"routes = {len(audit.routes)}")
    print(f"policy-gated routes = {len(gated)}")
    for dependency, count in audit.dependency_incidences:
        print(f"{dependency} = {count}")
    print("DYNAMIC POLICY EVENT SUMMARY")
    print(f"included dynamic events = {len(audit.events)}")
    for outcome in DecisionOutcome:
        print(f"{outcome.value} = {outcomes[outcome.value]}")
    print("POLICY-REFERENCED ABSTENTION SUMMARY")
    print(f"policy-referenced abstentions = {dict(audit.taxonomy_counts)['ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN']}")
    for route_id, count in audit.policy_route_counts:
        print(f"{route_id} = {count}")
    print("UNKNOWN / UNOBSERVABLE STATE SUMMARY")
    print(
        "POLICY_REFERENCED = "
        f"{states[PolicyObservationState.POLICY_REFERENCED.value]}"
    )
    print(f"UNKNOWN = {states[PolicyObservationState.UNKNOWN.value]}")
    print("PHASE 20 BASELINE CHECK")
    print(f"NO_ROUTE_MATCH = {audit.no_route_count}")
    print(f"ROUTE_MATCH_RULE_ABSTAIN = {dict(audit.taxonomy_counts)['ROUTE_MATCH_RULE_ABSTAIN']}")
    print(f"corpus = {audit.corpus_size}")
    print(f"production calls = {audit.production_calls}")
    print(f"completed auctions = {audit.completed_auctions}")
    print(f"abstentions = {audit.abstentions}")
    baseline_passed = (
        len(audit.routes) == 45
        and audit.policy_gated_route_count == 19
        and audit.no_route_count == 1_936
        and dict(audit.taxonomy_counts)
        == {
            "NO_ROUTE_MATCH": 1_936,
            "ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN": 123,
            "ROUTE_MATCH_RULE_ABSTAIN": 7_180,
        }
        and audit.policy_route_counts
        == (
            ("sayc.responder.1nt.jacoby.hearts.continuation", 62),
            ("sayc.responder.1nt.jacoby.spades.continuation", 61),
        )
        and (audit.production_calls, audit.completed_auctions, audit.abstentions)
        == (7_871, 761, 9_239)
    )
    print(f"audit status = {'PASS' if baseline_passed else 'FAIL'}")
    print("DISCLAIMER")
    print(DISCLAIMER)


if __name__ == "__main__":
    _print_summary(run_policy_visibility_audit())
