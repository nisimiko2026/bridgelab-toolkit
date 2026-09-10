from dataclasses import FrozenInstanceError, fields

import pytest

from benchmarks.phase20b_route_reachability_audit import run_route_reachability_audit
from benchmarks.phase21a_policy_visibility_audit import PolicyRequirementState
from benchmarks.phase21b_provenance_coverage_audit import (
    ProductionElementType,
)
from benchmarks.phase21b_provenance_coverage_audit import (
    run_audit as run_provenance_audit,
)
from benchmarks.phase21c_cross_layer_gap_audit import (
    GapType,
    InputRepresentationState,
    LayerPresenceState,
    OutputVisibilityState,
    ReachabilityState,
    RuntimeVisibilityState,
    _json_parser_fields,
    _serializer_keys,
    _typed_consumer_fields,
    _typed_request_fields,
    run_audit,
)
from bridge.full_deal_application import FullDealApplicationRequest


@pytest.fixture(scope="module")
def audit():
    return run_audit()


def test_records_are_frozen(audit):
    with pytest.raises(FrozenInstanceError):
        audit.audit_status = "OTHER"
    with pytest.raises(FrozenInstanceError):
        audit.entries[0].element_id = "other"


def test_repeated_matrix_is_deterministic(audit):
    assert run_audit() == audit


def test_primary_matrix_reuses_all_47_phase21b_identities(audit):
    provenance = run_provenance_audit()
    expected = {(item.element_type, item.element_id) for item in provenance.production_entries}
    observed = {(item.element_type, item.element_id) for item in audit.entries}
    assert observed == expected
    assert len(observed) == 47


def test_all_45_phase21a_and_live_routes_align(audit):
    live = {item.route_id for item in run_route_reachability_audit().inventory}
    phase21a = {item.route_id for item in audit.phase21a_routes}
    matrix = {item.route_id for item in audit.entries if item.element_type is ProductionElementType.BIDDING_ROUTE}
    assert len(live) == 45
    assert live == phase21a == matrix


def test_probability_and_declarer_appear_once(audit):
    counts = {kind: sum(item.element_type is kind for item in audit.entries) for kind in ProductionElementType}
    assert counts[ProductionElementType.PROBABILITY_ENGINE] == 1
    assert counts[ProductionElementType.DECLARER_TECHNIQUE] == 1


def test_empty_production_families_create_no_false_primary_gaps(audit):
    kinds = {item.element_type for item in audit.entries}
    assert ProductionElementType.DEFENSIVE_ALGORITHM not in kinds
    assert ProductionElementType.OPENING_LEAD_ALGORITHM not in kinds


def test_deferred_capabilities_are_excluded_and_expected(audit):
    deferred = {item.capability_id for item in audit.expected_absences}
    primary = {item.element_id.upper() for item in audit.entries}
    assert deferred.isdisjoint(primary)
    assert all(item.gap_type is GapType.EXPECTED_ABSENCE for item in audit.expected_absences)


def test_typed_input_fields_are_inspected_from_live_dataclass(audit):
    assert _typed_request_fields() == {item.name for item in fields(FullDealApplicationRequest)}
    assert {"bidding", "declarer_play", "probability_requests"} <= _typed_consumer_fields()
    assert dict(audit.summary)["typed_input_representable"] == 47


def test_json_cli_fields_are_inspected_from_live_parser(audit):
    assert _json_parser_fields() == {
        "bidding",
        "deal",
        "requested_stages",
        "probability_requests",
    }
    summary = dict(audit.summary)
    assert summary["json_cli_input_representable"] == 46
    assert summary["json_cli_publicly_reachable"] == 46
    assert summary["json_cli_not_reachable"] == 1
    assert dict(audit.gap_counts)[GapType.PUBLIC_JSON_INPUT_GAP.value] == 1


def test_current_typed_and_json_reachability_by_capability(audit):
    routes = [item for item in audit.entries if item.element_type is ProductionElementType.BIDDING_ROUTE]
    probability = next(
        item
        for item in audit.entries
        if item.element_type is ProductionElementType.PROBABILITY_ENGINE
    )
    declarer = next(
        item
        for item in audit.entries
        if item.element_type is ProductionElementType.DECLARER_TECHNIQUE
    )
    assert all(
        item.typed_input_state is InputRepresentationState.TYPED_AND_JSON
        for item in routes
    )
    assert all(item.typed_reachability_state is ReachabilityState.REQUIRES_EXPLICIT_DEPENDENCY for item in routes)
    assert all(
        item.json_cli_reachability_state is ReachabilityState.PUBLICLY_REACHABLE
        for item in routes
    )
    assert probability.typed_input_state is InputRepresentationState.TYPED_AND_JSON
    assert probability.json_cli_reachability_state is ReachabilityState.PUBLICLY_REACHABLE
    assert declarer.typed_input_state is InputRepresentationState.TYPED_ONLY
    assert declarer.json_cli_reachability_state is ReachabilityState.NOT_REACHABLE


def test_public_output_state_comes_from_live_serializer(audit):
    keys = _serializer_keys()
    assert {"stage", "status", "action", "explanation", "trace", "sources"} <= keys
    assert {"mode", "formula", "evidence", "probability_results"} <= keys
    assert "engine_type" not in keys
    assert "production_element_id" not in keys
    assert all(item.public_output_state is OutputVisibilityState.PARTIAL for item in audit.entries)


def test_runtime_not_observed_is_not_structural_unreachability(audit):
    assert all(item.runtime_visibility_state is RuntimeVisibilityState.NOT_OBSERVED for item in audit.entries)
    assert all(item.typed_reachability_state is not ReachabilityState.NOT_REACHABLE for item in audit.entries)


def test_policy_visibility_reuses_phase21a_static_classification(audit):
    policy_routes = [item for item in audit.entries if item.policy_requirement_state is PolicyRequirementState.POLICY_GATED]
    assert len(policy_routes) == 19
    assert all(item.policy_visibility_state is OutputVisibilityState.PARTIAL for item in policy_routes)
    assert dict(audit.gap_counts)[GapType.POLICY_OBSERVABILITY_GAP.value] == 19


def test_provenance_visibility_reuses_phase21b_states(audit):
    provenance = run_provenance_audit()
    expected = {(item.element_type, item.element_id): item.link_state for item in provenance.production_entries}
    assert all(expected[(item.element_type, item.element_id)] is item.provenance_visibility_state for item in audit.entries)
    assert dict(audit.gap_counts)[GapType.PROVENANCE_OBSERVABILITY_GAP.value] == 46


def test_expected_absence_and_not_applicable_are_distinct(audit):
    assert GapType.EXPECTED_ABSENCE.value not in dict(audit.gap_counts)
    assert LayerPresenceState.ABSENT is not LayerPresenceState.NOT_APPLICABLE
    assert OutputVisibilityState.ABSENT is not OutputVisibilityState.NOT_APPLICABLE


def test_evidence_legacy_and_audit_integrity(audit):
    assert all(item.evidence_ids and item.gap_types for item in audit.entries)
    assert audit.legacy_drift is GapType.KNOWN_LEGACY_TEST_DRIFT
    assert audit.legacy_drift.value not in dict(audit.gap_counts)
    assert audit.audit_status == "PASS"
