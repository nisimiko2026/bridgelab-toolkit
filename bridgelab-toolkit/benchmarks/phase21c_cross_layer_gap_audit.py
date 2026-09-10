"""Static cross-layer representation and observability audit for BridgeLab.

The audit describes software surfaces only.  It does not judge bridge theory,
source authority, or whether an intentionally absent capability should exist.
"""

from __future__ import annotations

import ast
import inspect
from collections import Counter
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path

from benchmarks import phase21b_provenance_coverage_audit as phase21b_provenance
from benchmarks.phase20b_route_reachability_audit import run_route_reachability_audit
from benchmarks.phase21a_policy_visibility_audit import (
    PolicyRequirementState,
    StaticRoutePolicyVisibility,
    _static_route,
)
from benchmarks.phase21b_provenance_coverage_audit import (
    DeferredCapabilityStatus,
    ProductionElementType,
    ProductionProvenanceEntry,
    ProvenanceLinkState,
)
from bridge.full_deal_analysis import full_deal_analysis_to_dict
from bridge.full_deal_application import (
    FullDealApplicationRequest,
    application_request_to_full_deal_input,
    full_deal_application_request_from_dict,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE20_CLOSURE = PROJECT_ROOT / "bridgelab_phase20_final_closure_record.md"


class LayerPresenceState(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    PARTIAL = "PARTIAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class InputRepresentationState(str, Enum):
    TYPED_AND_JSON = "TYPED_AND_JSON"
    TYPED_ONLY = "TYPED_ONLY"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class ReachabilityState(str, Enum):
    PUBLICLY_REACHABLE = "PUBLICLY_REACHABLE"
    REQUIRES_EXPLICIT_DEPENDENCY = "REQUIRES_EXPLICIT_DEPENDENCY"
    NOT_REACHABLE = "NOT_REACHABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class RuntimeVisibilityState(str, Enum):
    OBSERVABLE = "OBSERVABLE"
    PARTIAL = "PARTIAL"
    NOT_OBSERVED = "NOT_OBSERVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class OutputVisibilityState(str, Enum):
    PRESENT = "PRESENT"
    PARTIAL = "PARTIAL"
    ABSENT = "ABSENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class GapType(str, Enum):
    NO_STRUCTURAL_GAP = "NO_STRUCTURAL_GAP"
    EXPECTED_ABSENCE = "EXPECTED_ABSENCE"
    PUBLIC_JSON_INPUT_GAP = "PUBLIC_JSON_INPUT_GAP"
    PUBLIC_OUTPUT_IDENTITY_GAP = "PUBLIC_OUTPUT_IDENTITY_GAP"
    POLICY_OBSERVABILITY_GAP = "POLICY_OBSERVABILITY_GAP"
    PROVENANCE_OBSERVABILITY_GAP = "PROVENANCE_OBSERVABILITY_GAP"
    KNOWN_LEGACY_TEST_DRIFT = "KNOWN_LEGACY_TEST_DRIFT"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    UNKNOWN = "UNKNOWN"


class EvidenceKind(str, Enum):
    STATIC = "STATIC"
    DERIVED = "DERIVED"
    DYNAMIC = "DYNAMIC"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


@dataclass(frozen=True, slots=True)
class CrossLayerCapabilityEntry:
    element_type: ProductionElementType
    element_id: str
    route_id: str | None
    engine_type: str
    registration_state: LayerPresenceState
    rule_ownership_state: LayerPresenceState
    typed_input_state: InputRepresentationState
    json_cli_input_state: InputRepresentationState
    typed_reachability_state: ReachabilityState
    json_cli_reachability_state: ReachabilityState
    runtime_visibility_state: RuntimeVisibilityState
    policy_requirement_state: PolicyRequirementState | None
    policy_visibility_state: OutputVisibilityState
    provenance_visibility_state: ProvenanceLinkState
    public_output_state: OutputVisibilityState
    documentation_state: LayerPresenceState
    gap_types: tuple[GapType, ...]
    evidence_ids: tuple[str, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class ExpectedAbsenceEntry:
    capability_id: str
    classification: str
    gap_type: GapType
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CrossLayerGapAudit:
    entries: tuple[CrossLayerCapabilityEntry, ...]
    expected_absences: tuple[ExpectedAbsenceEntry, ...]
    phase21a_routes: tuple[StaticRoutePolicyVisibility, ...]
    summary: tuple[tuple[str, int], ...]
    gap_counts: tuple[tuple[str, int], ...]
    evidence_kinds: tuple[tuple[str, EvidenceKind], ...]
    legacy_drift: GapType
    limitations: tuple[str, ...]
    audit_status: str


def _phase21a_static_routes() -> tuple[StaticRoutePolicyVisibility, ...]:
    """Reuse Phase 21A's static conversion without its dynamic benchmark."""
    structural = run_route_reachability_audit()
    return tuple(_static_route(entry) for entry in structural.inventory)


def _typed_request_fields() -> frozenset[str]:
    return frozenset(item.name for item in fields(FullDealApplicationRequest))


def _typed_consumer_fields() -> frozenset[str]:
    """Return request fields actually consumed by the application dispatcher."""
    tree = ast.parse(inspect.getsource(application_request_to_full_deal_input))
    return frozenset(
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "request"
    )


def _json_parser_fields() -> frozenset[str]:
    tree = ast.parse(inspect.getsource(full_deal_application_request_from_dict))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "supported" for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        if isinstance(value, set) and all(isinstance(item, str) for item in value):
            return frozenset(value)
    return frozenset()


def _serializer_keys() -> frozenset[str]:
    tree = ast.parse(inspect.getsource(full_deal_analysis_to_dict))
    keys: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.add(key.value)
    return frozenset(keys)


def _documentation_consistent() -> bool:
    try:
        text = PHASE20_CLOSURE.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return False
    required = (
        "Routes: 45",
        "Registered probability engines: 1",
        "KnownCardCountQuestion",
        "Defensive algorithms: 0",
        "Opening-lead algorithms: 0",
        "Declarer production techniques: 1",
        "Restricted Choice registered: false",
        "Vacant Places registered: false",
        "Natural 1NT: `DOCUMENT_ONLY`",
    )
    return all(marker in text for marker in required)


def _input_state(
    entry: ProductionProvenanceEntry,
    typed_fields: frozenset[str],
    consumer_fields: frozenset[str],
    json_fields: frozenset[str],
) -> InputRepresentationState:
    if entry.element_type is ProductionElementType.BIDDING_ROUTE:
        typed, json = "bidding" in typed_fields, "bidding" in json_fields
    elif entry.element_type is ProductionElementType.DECLARER_TECHNIQUE:
        typed, json = "declarer_play" in typed_fields, "declarer_play" in json_fields
    elif entry.element_type is ProductionElementType.PROBABILITY_ENGINE:
        typed = "probability_requests" in typed_fields
        json = "probability_requests" in json_fields
    else:
        return InputRepresentationState.NOT_APPLICABLE
    typed = typed and (
        "bidding" in consumer_fields
        if entry.element_type is ProductionElementType.BIDDING_ROUTE
        else "declarer_play" in consumer_fields
        if entry.element_type is ProductionElementType.DECLARER_TECHNIQUE
        else "probability_requests" in consumer_fields
    )
    if typed and json:
        return InputRepresentationState.TYPED_AND_JSON
    if typed:
        return InputRepresentationState.TYPED_ONLY
    return InputRepresentationState.UNKNOWN


def _evidence_ids(
    entry: ProductionProvenanceEntry,
    policy: StaticRoutePolicyVisibility | None,
) -> tuple[str, ...]:
    evidence = [f"phase21b:element:{entry.element_type.value}:{entry.element_id}"]
    if entry.route_id is not None:
        evidence.extend(
            (
                f"phase21b:route-rules:{entry.route_id}",
                f"phase21a:route:{entry.route_id}",
                "app:typed-field:bidding",
                "app:json-parser:supported-fields",
                "serializer:subsystem:trace",
                "serializer:explicit-production-element-identity:absent",
            )
        )
        if policy is not None and policy.policy_requirement is PolicyRequirementState.POLICY_GATED:
            evidence.append(f"phase21a:policy-dependencies:{entry.route_id}")
    elif entry.element_type is ProductionElementType.DECLARER_TECHNIQUE:
        evidence.extend(("app:typed-field:declarer_play", "serializer:subsystem:trace", "serializer:explicit-production-element-identity:absent"))
    elif entry.element_type is ProductionElementType.PROBABILITY_ENGINE:
        evidence.extend(("app:typed-field:probability_requests", "app:json-field:probability_requests", "serializer:probability_results", "serializer:explicit-engine-identity:absent"))
    evidence.append("closure:phase20:production-invariants")
    return tuple(evidence)


def _entry(
    production: ProductionProvenanceEntry,
    policy: StaticRoutePolicyVisibility | None,
    typed_fields: frozenset[str],
    consumer_fields: frozenset[str],
    json_fields: frozenset[str],
    serializer_keys: frozenset[str],
    documentation_consistent: bool,
) -> CrossLayerCapabilityEntry:
    input_state = _input_state(production, typed_fields, consumer_fields, json_fields)
    is_route = production.element_type is ProductionElementType.BIDDING_ROUTE
    is_probability = production.element_type is ProductionElementType.PROBABILITY_ENGINE
    ownership = LayerPresenceState.PRESENT if is_route else LayerPresenceState.NOT_APPLICABLE
    typed_reachability = (
        ReachabilityState.REQUIRES_EXPLICIT_DEPENDENCY
        if is_route
        else ReachabilityState.PUBLICLY_REACHABLE
    )
    json_reachability = (
        ReachabilityState.PUBLICLY_REACHABLE
        if input_state is InputRepresentationState.TYPED_AND_JSON
        else ReachabilityState.NOT_REACHABLE
    )
    policy_requirement = None if policy is None else policy.policy_requirement
    policy_visibility = (
        OutputVisibilityState.PARTIAL
        if policy_requirement is PolicyRequirementState.POLICY_GATED
        else OutputVisibilityState.NOT_APPLICABLE
    )
    required_output_fields = (
        {"status", "mode", "formula", "explanation", "trace", "evidence"}
        if is_probability
        else {"stage", "status", "action", "explanation", "trace"}
    )
    output_fields_present = required_output_fields <= serializer_keys
    public_output = OutputVisibilityState.PARTIAL if output_fields_present else OutputVisibilityState.UNKNOWN
    gaps = []
    if input_state is InputRepresentationState.TYPED_ONLY:
        gaps.append(GapType.PUBLIC_JSON_INPUT_GAP)
    if "engine_type" not in serializer_keys:
        gaps.append(GapType.PUBLIC_OUTPUT_IDENTITY_GAP)
    if policy_visibility is OutputVisibilityState.PARTIAL:
        gaps.append(GapType.POLICY_OBSERVABILITY_GAP)
    if production.link_state in {
        ProvenanceLinkState.RUNTIME_CONDITIONAL,
        ProvenanceLinkState.NO_LINK,
    }:
        gaps.append(GapType.PROVENANCE_OBSERVABILITY_GAP)
    if not gaps:
        gaps.append(GapType.NO_STRUCTURAL_GAP)
    notes = (
        "JSON/CLI input absence is an interface observability gap, not a production failure."
        if input_state is InputRepresentationState.TYPED_ONLY
        else "Current registered capability is represented by the JSON/CLI input contract."
    )
    if is_probability:
        notes += " NO_LINK means no production-attached provenance, not no documentation."
    notes += (
        " PUBLIC_OUTPUT_IDENTITY_GAP means explicit production-element or engine-class "
        "identity is not directly serialized; trace, stage, action, and technique evidence "
        "may still expose narrower identity information."
    )
    return CrossLayerCapabilityEntry(
        production.element_type,
        production.element_id,
        production.route_id,
        production.engine_type,
        LayerPresenceState.PRESENT,
        ownership,
        input_state,
        input_state,
        typed_reachability,
        json_reachability,
        RuntimeVisibilityState.NOT_OBSERVED,
        policy_requirement,
        policy_visibility,
        production.link_state,
        public_output,
        LayerPresenceState.PRESENT if documentation_consistent else LayerPresenceState.UNKNOWN,
        tuple(gaps),
        _evidence_ids(production, policy),
        notes,
    )


def _expected_absences(
    deferred: tuple[DeferredCapabilityStatus, ...],
) -> tuple[ExpectedAbsenceEntry, ...]:
    return tuple(
        ExpectedAbsenceEntry(
            item.capability_id,
            item.classification,
            GapType.EXPECTED_ABSENCE,
            (f"phase21b:deferred:{item.capability_id}",),
        )
        for item in deferred
    )


def _count(values: list[str]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(Counter(values).items()))


def run_audit() -> CrossLayerGapAudit:
    provenance = phase21b_provenance.run_audit()
    phase21a_routes = _phase21a_static_routes()
    policy_by_route = {item.route_id: item for item in phase21a_routes}
    typed_fields = _typed_request_fields()
    consumer_fields = _typed_consumer_fields()
    json_fields = _json_parser_fields()
    serializer_keys = _serializer_keys()
    documentation_consistent = _documentation_consistent()
    entries = tuple(
        _entry(
            item,
            policy_by_route.get(item.route_id or ""),
            typed_fields,
            consumer_fields,
            json_fields,
            serializer_keys,
            documentation_consistent,
        )
        for item in provenance.production_entries
    )
    expected_absences = _expected_absences(provenance.deferred_capabilities)
    gaps = [gap.value for item in entries for gap in item.gap_types]
    summary = tuple(
        sorted(
            {
                "primary_entries": len(entries),
                "route_entries": sum(item.element_type is ProductionElementType.BIDDING_ROUTE for item in entries),
                "probability_entries": sum(item.element_type is ProductionElementType.PROBABILITY_ENGINE for item in entries),
                "declarer_entries": sum(item.element_type is ProductionElementType.DECLARER_TECHNIQUE for item in entries),
                "typed_input_representable": sum(item.typed_input_state in {InputRepresentationState.TYPED_AND_JSON, InputRepresentationState.TYPED_ONLY} for item in entries),
                "json_cli_input_representable": sum(item.json_cli_input_state is InputRepresentationState.TYPED_AND_JSON for item in entries),
                "typed_publicly_reachable": sum(item.typed_reachability_state is ReachabilityState.PUBLICLY_REACHABLE for item in entries),
                "typed_requires_dependency": sum(item.typed_reachability_state is ReachabilityState.REQUIRES_EXPLICIT_DEPENDENCY for item in entries),
                "json_cli_publicly_reachable": sum(item.json_cli_reachability_state is ReachabilityState.PUBLICLY_REACHABLE for item in entries),
                "json_cli_not_reachable": sum(item.json_cli_reachability_state is ReachabilityState.NOT_REACHABLE for item in entries),
                "runtime_not_observed": sum(item.runtime_visibility_state is RuntimeVisibilityState.NOT_OBSERVED for item in entries),
                "policy_audit_visible": sum(item.policy_requirement_state is PolicyRequirementState.POLICY_GATED for item in entries),
                "policy_not_applicable": sum(item.policy_visibility_state is OutputVisibilityState.NOT_APPLICABLE for item in entries),
                "public_output_partial": sum(item.public_output_state is OutputVisibilityState.PARTIAL for item in entries),
                "documentation_present": sum(item.documentation_state is LayerPresenceState.PRESENT for item in entries),
                "expected_deferred_absences": len(expected_absences),
                "route_rule_edges": len(provenance.route_rule_edges),
                "unique_rule_ids": len({edge.rule_id for edge in provenance.route_rule_edges}),
            }.items()
        )
    )
    evidence_kinds = (
        ("app-schema", EvidenceKind.STATIC),
        ("closure-record", EvidenceKind.STATIC),
        ("cross-layer-join", EvidenceKind.DERIVED),
        ("phase21a-events", EvidenceKind.DYNAMIC),
        ("phase21a-event-counts", EvidenceKind.DIAGNOSTIC_ONLY),
        ("phase21a-static-routes", EvidenceKind.STATIC),
        ("phase21b-provenance", EvidenceKind.STATIC),
        ("public-serializer", EvidenceKind.STATIC),
    )
    expected = {
        "entries": 47,
        "routes": 45,
        "probability": 1,
        "declarer": 1,
        "phase21a_routes": 45,
        "typed": 47,
    }
    observed = {
        "entries": len(entries),
        "routes": sum(item.element_type is ProductionElementType.BIDDING_ROUTE for item in entries),
        "probability": sum(item.element_type is ProductionElementType.PROBABILITY_ENGINE for item in entries),
        "declarer": sum(item.element_type is ProductionElementType.DECLARER_TECHNIQUE for item in entries),
        "phase21a_routes": len(phase21a_routes),
        "typed": sum(item.typed_input_state in {InputRepresentationState.TYPED_AND_JSON, InputRepresentationState.TYPED_ONLY} for item in entries),
    }
    json_representable = sum(
        item.json_cli_input_state is InputRepresentationState.TYPED_AND_JSON
        for item in entries
    )
    json_not_reachable = sum(
        item.json_cli_reachability_state is ReachabilityState.NOT_REACHABLE
        for item in entries
    )
    valid = (
        observed == expected
        and json_representable + json_not_reachable == len(entries)
        and all(
            (
                item.json_cli_input_state
                is InputRepresentationState.TYPED_AND_JSON
            )
            == (
                item.json_cli_reachability_state
                is ReachabilityState.PUBLICLY_REACHABLE
            )
            for item in entries
        )
        and len({(item.element_type, item.element_id) for item in entries}) == len(entries)
        and all(item.evidence_ids for item in entries)
        and all(item.gap_types for item in entries)
        and documentation_consistent
    )
    return CrossLayerGapAudit(
        entries,
        expected_absences,
        phase21a_routes,
        summary,
        _count(gaps),
        evidence_kinds,
        GapType.KNOWN_LEGACY_TEST_DRIFT,
        (
            "Layer agreement does not establish bridge correctness.",
            "JSON/CLI input scope is narrower than the typed application request.",
            "NOT_OBSERVED means not observed by Phase 21C; it never implies structurally unreachable or absence of evidence elsewhere.",
            "PUBLIC_OUTPUT_IDENTITY_GAP concerns explicit production-element or engine-class identity, not all trace identity.",
            "Provenance visibility does not establish source authority.",
            "Expected deferred absence is not a production defect.",
        ),
        "PASS" if valid else "FAIL",
    )


def _print_counts(title: str, counts: tuple[tuple[str, int], ...]) -> None:
    print(title)
    for key, value in counts:
        print(f"{key} = {value}")


def main() -> int:
    audit = run_audit()
    _print_counts("CROSS-LAYER COVERAGE", audit.summary)
    print("PUBLIC INPUT REACHABILITY")
    for key, value in audit.summary:
        if key.startswith(("typed_", "json_cli_")):
            print(f"{key} = {value}")
    print("PUBLIC OUTPUT VISIBILITY")
    print(f"public_output_partial = {dict(audit.summary)['public_output_partial']}")
    print("identity gap = explicit production-element/engine-class identity is not directly serialized; trace identity may still exist")
    print("POLICY VISIBILITY")
    print(f"policy_audit_visible = {dict(audit.summary)['policy_audit_visible']}")
    print("policy gap = audit-visible policy metadata/state is not explicitly serialized")
    print("PROVENANCE VISIBILITY")
    for state, count in _count([item.provenance_visibility_state.value for item in audit.entries]):
        print(f"{state} = {count}")
    print("provenance gaps indicate incomplete public/static observability, not invalid provenance")
    print("DOCUMENTATION CONSISTENCY")
    print(f"documentation_present = {dict(audit.summary)['documentation_present']}")
    print("EXPECTED / DEFERRED ABSENCES")
    for item in audit.expected_absences:
        print(f"{item.capability_id} = {item.classification}; {item.gap_type.value}")
    _print_counts("GAP SUMMARY", audit.gap_counts)
    print(f"legacy drift = {audit.legacy_drift.value}")
    print("LIMITATIONS")
    for limitation in audit.limitations:
        print(f"- {limitation}")
    print("DISCLAIMER")
    print("Cross-layer consistency measures software representation and observability; it does not establish bridge-theory correctness.")
    print(f"audit status = {audit.audit_status}")
    return 0 if audit.audit_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
