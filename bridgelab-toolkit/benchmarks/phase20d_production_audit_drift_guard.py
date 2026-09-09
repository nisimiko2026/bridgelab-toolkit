"""Behavior-neutral drift guard for reviewed Phase 20 production baselines."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from benchmarks.phase13_coverage_closure_audit import (
    run_phase13_coverage_closure_audit,
)
from benchmarks.phase20b_route_reachability_audit import (
    OwnershipClassification,
    RouteReachabilityAudit,
    run_route_reachability_audit,
)
from benchmarks.phase20c_abstention_taxonomy_audit import (
    AbstentionCategory,
    AbstentionTaxonomyAudit,
    run_abstention_taxonomy_audit,
)
from bridge.declarer_recommendation import DeclarerTechnique
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY


class DriftClass(str, Enum):
    STRUCTURAL_ROUTE_DRIFT = "STRUCTURAL_ROUTE_DRIFT"
    POLICY_GATING_DRIFT = "POLICY_GATING_DRIFT"
    ORDINARY_BENCHMARK_DRIFT = "ORDINARY_BENCHMARK_DRIFT"
    ABSTENTION_TAXONOMY_DRIFT = "ABSTENTION_TAXONOMY_DRIFT"
    PRODUCTION_REGISTRY_DRIFT = "PRODUCTION_REGISTRY_DRIFT"
    RECOMMENDATION_CLOSURE_RECORD_DRIFT = (
        "RECOMMENDATION_CLOSURE_RECORD_DRIFT"
    )


class BaselineStatus(str, Enum):
    HARD_INVARIANT = "HARD_INVARIANT"
    PHASE_BASELINE = "PHASE_BASELINE"
    INTENTIONAL_CHANGE_REQUIRES_BASELINE_UPDATE = (
        "INTENTIONAL_CHANGE_REQUIRES_BASELINE_UPDATE"
    )
    DOCUMENT_ONLY = "DOCUMENT_ONLY"
    HISTORICAL_BASELINE_ONLY = "HISTORICAL_BASELINE_ONLY"


@dataclass(frozen=True, slots=True)
class StructuralExpectedBaseline:
    route_count: int = 45
    unique_route_ids: int = 45
    unique_exact_prefixes: int = 45
    structurally_matched_routes: int = 45
    policy_gated_routes: int = 19
    invalid_prefixes: int = 0
    shadowed_routes: int = 0
    unreachable_routes: int = 0
    missing_owners: int = 0
    duplicate_route_ids: int = 0
    ambiguous_owners: int = 0
    duplicate_exact_prefixes: int = 0
    unique_owner_count: int = 7
    shared_owner_expected_count: int = 38
    route_ids: tuple[str, ...] = (
        "sayc.2over1.opener.1h.2c", "sayc.2over1.opener.1h.2d",
        "sayc.2over1.opener.1s.2c", "sayc.2over1.opener.1s.2d",
        "sayc.advancer.takeout.after.1c", "sayc.advancer.takeout.after.1d",
        "sayc.advancer.takeout.after.1h", "sayc.advancer.takeout.after.1s",
        "sayc.opener.1c.1d", "sayc.opener.1c.1h", "sayc.opener.1c.1s",
        "sayc.opener.1d.1h", "sayc.opener.1d.1s", "sayc.opener.1h.1s",
        "sayc.opener.1h.2h", "sayc.opener.1nt.jacoby.2d",
        "sayc.opener.1nt.jacoby.2h", "sayc.opener.1nt.stayman",
        "sayc.opener.1s.2s", "sayc.opener.2c.2d.balanced",
        "sayc.opener.2nt.jacoby.3d", "sayc.opener.2nt.jacoby.3h",
        "sayc.opener.2nt.stayman", "sayc.opener.2nt.texas.4d",
        "sayc.opener.2nt.texas.4h", "sayc.opening",
        "sayc.overcall.direct.after.1c", "sayc.overcall.direct.after.1d",
        "sayc.overcall.direct.after.1h", "sayc.overcall.direct.after.1s",
        "sayc.responder.1nt.jacoby.hearts.continuation",
        "sayc.responder.1nt.jacoby.spades.continuation",
        "sayc.responder.1nt.stayman.after.2h",
        "sayc.responder.1nt.stayman.after.2s", "sayc.response.1c",
        "sayc.response.1d", "sayc.response.1h", "sayc.response.1nt.jacoby",
        "sayc.response.1s", "sayc.response.2c.waiting",
        "sayc.response.2nt.jacoby", "sayc.support_double.1c.1h.1s",
        "sayc.support_double.1d.1h.1s", "sayc.support_double.1d.1s.2c",
        "sayc.support_double.1h.1s.2d",
    )
    route_prefixes: tuple[tuple[str, ...], ...] = (
        (), ("1C",), ("1C", "P"), ("1C", "P", "1D", "P"),
        ("1C", "P", "1H", "1S"), ("1C", "P", "1H", "P"),
        ("1C", "P", "1S", "P"), ("1C", "X", "P"), ("1D",),
        ("1D", "P"), ("1D", "P", "1H", "1S"),
        ("1D", "P", "1H", "P"), ("1D", "P", "1S", "2C"),
        ("1D", "P", "1S", "P"), ("1D", "X", "P"), ("1H",),
        ("1H", "P"), ("1H", "P", "1S", "2D"),
        ("1H", "P", "1S", "P"), ("1H", "P", "2C", "P"),
        ("1H", "P", "2D", "P"), ("1H", "P", "2H", "P"),
        ("1H", "X", "P"), ("1NT", "P"),
        ("1NT", "P", "2C", "P"), ("1NT", "P", "2C", "P", "2H", "P"),
        ("1NT", "P", "2C", "P", "2S", "P"),
        ("1NT", "P", "2D", "P"), ("1NT", "P", "2D", "P", "2H", "P"),
        ("1NT", "P", "2H", "P"), ("1NT", "P", "2H", "P", "2S", "P"),
        ("1S",), ("1S", "P"), ("1S", "P", "2C", "P"),
        ("1S", "P", "2D", "P"), ("1S", "P", "2S", "P"),
        ("1S", "X", "P"), ("2C", "P"), ("2C", "P", "2D", "P"),
        ("2NT", "P"), ("2NT", "P", "3C", "P"),
        ("2NT", "P", "3D", "P"), ("2NT", "P", "3H", "P"),
        ("2NT", "P", "4D", "P"), ("2NT", "P", "4H", "P"),
    )
    policy_dependencies: tuple[str, ...] = (
        "jacoby_continuation_strength", "offensive_hand",
        "opponent_suit_shortness", "playing_strength",
        "stayman_continuation_strength", "stayman_dual_major_response",
        "stopper", "suit_quality", "support_double_eligibility",
        "takeout_advancer_strength",
    )


@dataclass(frozen=True, slots=True)
class BehavioralExpectedBaseline:
    corpus_size: int = 10_000
    seed_start: int = 1
    seed_end: int = 10_000
    production_calls: int = 7_871
    completed_auctions: int = 761
    abstentions: int = 9_239
    category_counts: tuple[tuple[str, int], ...] = (
        ("NO_ROUTE_MATCH", 1_936),
        ("ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN", 123),
        ("ROUTE_MATCH_RULE_ABSTAIN", 7_180),
    )
    policy_route_counts: tuple[tuple[str, int], ...] = (
        ("sayc.responder.1nt.jacoby.hearts.continuation", 62),
        ("sayc.responder.1nt.jacoby.spades.continuation", 61),
    )


@dataclass(frozen=True, slots=True)
class RegistryExpectedBaseline:
    probability_question_types: tuple[str, ...] = ("KnownCardCountQuestion",)
    restricted_choice_registered: bool = False
    vacant_places_registered: bool = False
    declarer_techniques: tuple[str, ...] = ("simple-unblock-king",)
    defensive_algorithms: int = 0
    opening_lead_algorithms: int = 0


@dataclass(frozen=True, slots=True)
class ProductionAuditBaseline:
    structural: StructuralExpectedBaseline = StructuralExpectedBaseline()
    behavioral: BehavioralExpectedBaseline = BehavioralExpectedBaseline()
    registry: RegistryExpectedBaseline = RegistryExpectedBaseline()
    recommendation_closure_record: int = 4
    natural_one_notrump_status: BaselineStatus = BaselineStatus.DOCUMENT_ONLY


DEFAULT_BASELINE = ProductionAuditBaseline()


@dataclass(frozen=True, slots=True)
class StructuralObservation:
    values: StructuralExpectedBaseline
    registration_order: tuple[str, ...]
    priorities: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ProductionObservations:
    structural: StructuralObservation
    behavioral: BehavioralExpectedBaseline
    registry: RegistryExpectedBaseline
    recommendation_closure_record: int
    top_stopped_prefixes: tuple[tuple[tuple[str, ...], int], ...]
    behavioral_classified_total: int
    behavioral_unique_seed_count: int
    behavioral_categories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DriftFinding:
    drift_class: DriftClass
    field: str
    expected: object
    observed: object
    authority: str
    baseline_status: BaselineStatus

    def format(self) -> str:
        return (
            f"{self.drift_class.value}: {self.field}; expected={self.expected!r}; "
            f"observed={self.observed!r}; authority={self.authority}; "
            f"status={self.baseline_status.value}"
        )


@dataclass(frozen=True, slots=True)
class ProductionAuditDriftGuardResult:
    observations: ProductionObservations
    findings: tuple[DriftFinding, ...]

    @property
    def passed(self) -> bool:
        return not self.findings


def _observe_structural(audit: RouteReachabilityAudit) -> StructuralObservation:
    owners = Counter(entry.ownership for entry in audit.inventory)
    dependencies = tuple(
        sorted({item for entry in audit.inventory for item in entry.policy_dependencies})
    )
    values = StructuralExpectedBaseline(
        route_count=audit.route_count,
        unique_route_ids=audit.unique_route_ids,
        unique_exact_prefixes=audit.unique_exact_prefixes,
        structurally_matched_routes=audit.structurally_matched_routes,
        policy_gated_routes=audit.policy_gated_routes,
        invalid_prefixes=audit.invalid_prefixes,
        shadowed_routes=audit.shadowed_routes,
        unreachable_routes=audit.unreachable_routes,
        missing_owners=audit.missing_owners,
        duplicate_route_ids=audit.duplicate_route_ids,
        ambiguous_owners=audit.ambiguous_owners,
        duplicate_exact_prefixes=audit.duplicate_exact_prefixes,
        unique_owner_count=owners[OwnershipClassification.UNIQUE_OWNER],
        shared_owner_expected_count=owners[
            OwnershipClassification.SHARED_OWNER_EXPECTED
        ],
        route_ids=tuple(sorted(entry.route_id for entry in audit.inventory)),
        route_prefixes=tuple(sorted(entry.auction_prefix for entry in audit.inventory)),
        policy_dependencies=dependencies,
    )
    return StructuralObservation(
        values,
        tuple(entry.route_id for entry in audit.inventory),
        tuple((entry.route_id, entry.priority) for entry in audit.inventory),
    )


def _observe_behavioral(audit: AbstentionTaxonomyAudit) -> BehavioralExpectedBaseline:
    return BehavioralExpectedBaseline(
        corpus_size=audit.corpus_size,
        seed_start=audit.seeds[0] if audit.seeds else audit.start_seed,
        seed_end=audit.seeds[-1] if audit.seeds else audit.start_seed - 1,
        production_calls=audit.production_calls,
        completed_auctions=audit.completed_auctions,
        abstentions=audit.abstentions,
        category_counts=audit.category_counts,
        policy_route_counts=audit.policy_route_counts,
    )


def collect_observations(
    structural_audit: RouteReachabilityAudit,
    behavioral_audit: AbstentionTaxonomyAudit,
) -> ProductionObservations:
    closure = run_phase13_coverage_closure_audit()
    probability_types = DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types
    source_coverage = closure.source_coverage
    registry = RegistryExpectedBaseline(
        probability_question_types=probability_types,
        restricted_choice_registered="RestrictedChoiceQuestion" in probability_types,
        vacant_places_registered="VacantPlacesQuestion" in probability_types,
        declarer_techniques=tuple(item.value for item in DeclarerTechnique),
        defensive_algorithms=int(source_coverage["defensive_techniques"]),
        opening_lead_algorithms=int(source_coverage["opening_lead_techniques"]),
    )
    return ProductionObservations(
        _observe_structural(structural_audit),
        _observe_behavioral(behavioral_audit),
        registry,
        int(closure.benchmark["recommendations_total"]),
        behavioral_audit.stopped_prefix_counts[:9],
        behavioral_audit.classified_total,
        len({item.seed for item in behavioral_audit.observations}),
        tuple(sorted({item.category.value for item in behavioral_audit.observations})),
    )


def _finding(
    drift_class: DriftClass,
    field: str,
    expected: object,
    observed: object,
    authority: str,
    status: BaselineStatus = BaselineStatus.PHASE_BASELINE,
) -> DriftFinding:
    return DriftFinding(drift_class, field, expected, observed, authority, status)


def compare_baseline(
    expected: ProductionAuditBaseline,
    observed: ProductionObservations,
) -> tuple[DriftFinding, ...]:
    findings: list[DriftFinding] = []

    structural_policy_fields = {"policy_gated_routes", "policy_dependencies"}
    for field in StructuralExpectedBaseline.__dataclass_fields__:
        wanted = getattr(expected.structural, field)
        actual = getattr(observed.structural.values, field)
        if wanted == actual:
            continue
        drift_class = (
            DriftClass.POLICY_GATING_DRIFT
            if field in structural_policy_fields
            else DriftClass.STRUCTURAL_ROUTE_DRIFT
        )
        findings.append(_finding(drift_class, field, wanted, actual, "Phase20B"))

    live_structural = observed.structural.values
    hard_structural = (
        (
            "route_id_uniqueness",
            live_structural.route_count,
            live_structural.unique_route_ids,
        ),
        (
            "exact_prefix_uniqueness",
            live_structural.route_count,
            live_structural.unique_exact_prefixes,
        ),
        ("invalid_prefixes", 0, live_structural.invalid_prefixes),
        ("missing_owners", 0, live_structural.missing_owners),
        ("ambiguous_owners", 0, live_structural.ambiguous_owners),
    )
    for field, wanted, actual in hard_structural:
        if wanted != actual:
            findings.append(
                _finding(
                    DriftClass.STRUCTURAL_ROUTE_DRIFT,
                    field,
                    wanted,
                    actual,
                    "Phase20B-live-structural-invariant",
                    BaselineStatus.HARD_INVARIANT,
                )
            )

    taxonomy_fields = {"category_counts", "policy_route_counts"}
    for field in BehavioralExpectedBaseline.__dataclass_fields__:
        wanted = getattr(expected.behavioral, field)
        actual = getattr(observed.behavioral, field)
        if wanted != actual:
            drift_class = (
                DriftClass.ABSTENTION_TAXONOMY_DRIFT
                if field in taxonomy_fields
                else DriftClass.ORDINARY_BENCHMARK_DRIFT
            )
            findings.append(_finding(drift_class, field, wanted, actual, "Phase20C"))

    category_total = sum(count for _, count in observed.behavioral.category_counts)
    if category_total != observed.behavioral.abstentions:
        findings.append(
            _finding(
                DriftClass.ABSTENTION_TAXONOMY_DRIFT,
                "category_exhaustiveness",
                observed.behavioral.abstentions,
                category_total,
                "Phase20C",
                BaselineStatus.HARD_INVARIANT,
            )
        )
    expected_categories = tuple(sorted(category.value for category in AbstentionCategory))
    hard_behavioral = (
        (
            "classified_total",
            observed.behavioral.abstentions,
            observed.behavioral_classified_total,
        ),
        (
            "unique_classified_seeds",
            observed.behavioral_classified_total,
            observed.behavioral_unique_seed_count,
        ),
        ("category_membership", expected_categories, observed.behavioral_categories),
    )
    for field, wanted, actual in hard_behavioral:
        if wanted != actual:
            findings.append(
                _finding(
                    DriftClass.ABSTENTION_TAXONOMY_DRIFT,
                    field,
                    wanted,
                    actual,
                    "Phase20C",
                    BaselineStatus.HARD_INVARIANT,
                )
            )

    for field in RegistryExpectedBaseline.__dataclass_fields__:
        wanted = getattr(expected.registry, field)
        actual = getattr(observed.registry, field)
        if wanted != actual:
            findings.append(
                _finding(
                    DriftClass.PRODUCTION_REGISTRY_DRIFT,
                    field,
                    wanted,
                    actual,
                    "production-registry-or-Phase13-closure",
                )
            )

    if expected.recommendation_closure_record != observed.recommendation_closure_record:
        findings.append(
            _finding(
                DriftClass.RECOMMENDATION_CLOSURE_RECORD_DRIFT,
                "recommendation_closure_record",
                expected.recommendation_closure_record,
                observed.recommendation_closure_record,
                "Phase13-closure-record",
                BaselineStatus.HISTORICAL_BASELINE_ONLY,
            )
        )
    return tuple(
        sorted(
            findings,
            key=lambda item: (
                item.drift_class.value, item.field, repr(item.expected), repr(item.observed)
            ),
        )
    )


def run_production_audit_drift_guard(
    expected: ProductionAuditBaseline = DEFAULT_BASELINE,
    *,
    structural_audit: RouteReachabilityAudit | None = None,
    behavioral_audit: AbstentionTaxonomyAudit | None = None,
) -> ProductionAuditDriftGuardResult:
    structural = structural_audit or run_route_reachability_audit()
    behavioral = behavioral_audit or run_abstention_taxonomy_audit()
    observations = collect_observations(structural, behavioral)
    return ProductionAuditDriftGuardResult(
        observations, compare_baseline(expected, observations)
    )


def _print_summary(result: ProductionAuditDriftGuardResult) -> None:
    observed = result.observations
    structural = observed.structural.values
    behavioral = observed.behavioral
    registry = observed.registry
    print("PHASE 20D PRODUCTION/AUDIT DRIFT GUARD")
    print(f"structural baseline: {'PASS' if not any(x.drift_class in {DriftClass.STRUCTURAL_ROUTE_DRIFT, DriftClass.POLICY_GATING_DRIFT} for x in result.findings) else 'FAIL'}")
    print(f"behavioral baseline: {'PASS' if not any(x.drift_class in {DriftClass.ORDINARY_BENCHMARK_DRIFT, DriftClass.ABSTENTION_TAXONOMY_DRIFT} for x in result.findings) else 'FAIL'}")
    print(f"registry baseline: {'PASS' if not any(x.drift_class is DriftClass.PRODUCTION_REGISTRY_DRIFT for x in result.findings) else 'FAIL'}")
    print(f"routes = {structural.route_count}")
    print(f"policy-gated routes = {structural.policy_gated_routes}")
    print(f"corpus = {behavioral.corpus_size}")
    print(f"production calls = {behavioral.production_calls}")
    print(f"completed auctions = {behavioral.completed_auctions}")
    print(f"abstentions = {behavioral.abstentions}")
    print("taxonomy:")
    for category, count in behavioral.category_counts:
        print(f"{category} = {count}")
    print("probability registry:")
    print(f"{', '.join(registry.probability_question_types)} only")
    print("declarer:")
    print("SIMPLE_UNBLOCK_KING only")
    print(f"Restricted Choice registered = {str(registry.restricted_choice_registered).lower()}")
    print(f"Vacant Places registered = {str(registry.vacant_places_registered).lower()}")
    print(f"recommendation closure record = {observed.recommendation_closure_record}")
    print(f"status = {BaselineStatus.HISTORICAL_BASELINE_ONLY.value}")
    print(f"Natural 1NT status = {BaselineStatus.DOCUMENT_ONLY.value}")
    print(f"drift findings = {len(result.findings)}")
    for finding in result.findings:
        print(finding.format())
    print(f"guard result = {'PASS' if result.passed else 'FAIL'}")


if __name__ == "__main__":
    _print_summary(run_production_audit_drift_guard())
