import subprocess
from dataclasses import FrozenInstanceError

import pytest

from benchmarks.phase21b_provenance_coverage_audit import (
    GIT_ROOT,
    ArtifactPresenceState,
    AuthorityState,
    ProductionElementType,
    ProvenanceLinkState,
    VerificationState,
    _manifest_entries,
    run_audit,
)
from bridge.declarer_recommendation import UNBLOCK_SOURCE, DeclarerTechnique
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY
from bridge.sayc_route_configuration import create_standard_sayc_router
from core.provenance import ProvenanceValidator


@pytest.fixture(scope="module")
def audit():
    return run_audit()


def test_records_are_immutable(audit):
    with pytest.raises(FrozenInstanceError):
        audit.audit_status = "OTHER"
    with pytest.raises(FrozenInstanceError):
        audit.production_entries[0].element_id = "other"


def test_repeated_inventory_is_deterministic(audit):
    assert run_audit() == audit


def test_primary_inventory_has_reviewed_47_elements(audit):
    assert len(audit.production_entries) == 47
    identities = {(item.element_type, item.element_id) for item in audit.production_entries}
    assert len(identities) == 47


def test_every_live_route_is_represented_exactly_once(audit):
    live = {route.route_id for route in create_standard_sayc_router().routes}
    represented = [item.element_id for item in audit.production_entries if item.element_type is ProductionElementType.BIDDING_ROUTE]
    assert len(represented) == 45
    assert set(represented) == live


def test_probability_registry_is_represented_once(audit):
    entries = [item for item in audit.production_entries if item.element_type is ProductionElementType.PROBABILITY_ENGINE]
    assert [item.element_id for item in entries] == list(DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types)
    assert len(entries) == 1


def test_declarer_registry_is_represented_once(audit):
    entries = [item for item in audit.production_entries if item.element_type is ProductionElementType.DECLARER_TECHNIQUE]
    assert [item.element_id for item in entries] == [DeclarerTechnique.SIMPLE_UNBLOCK_KING.value]


def test_empty_algorithm_registries_add_no_primary_entries(audit):
    types = [item.element_type for item in audit.production_entries]
    assert ProductionElementType.DEFENSIVE_ALGORITHM not in types
    assert ProductionElementType.OPENING_LEAD_ALGORITHM not in types


def test_route_rule_edges_match_live_router(audit):
    live = [(route.route_id, rule.rule_id) for route in create_standard_sayc_router().routes for rule in route.engine.rules]
    observed = [(edge.route_id, edge.rule_id) for edge in audit.route_rule_edges]
    assert observed == live
    assert len(observed) == 134
    assert len({rule_id for _, rule_id in observed}) == 92


def test_many_to_many_route_rule_relationships_are_preserved(audit):
    route_counts = {}
    rule_routes = {}
    for edge in audit.route_rule_edges:
        route_counts[edge.route_id] = route_counts.get(edge.route_id, 0) + 1
        rule_routes.setdefault(edge.rule_id, set()).add(edge.route_id)
    assert max(route_counts.values()) > 1
    assert max(map(len, rule_routes.values())) > 1


def test_routes_are_runtime_conditional_without_inferred_sources(audit):
    routes = [item for item in audit.production_entries if item.element_type is ProductionElementType.BIDDING_ROUTE]
    assert all(item.link_state is ProvenanceLinkState.RUNTIME_CONDITIONAL for item in routes)
    assert all(item.source_ids == () for item in routes)


def test_declarer_direct_link_does_not_claim_authority(audit):
    entry = next(item for item in audit.production_entries if item.element_type is ProductionElementType.DECLARER_TECHNIQUE)
    assert entry.link_state is ProvenanceLinkState.DIRECT
    assert entry.source_ids
    assert entry.artifact_state is ArtifactPresenceState.PRESENT
    assert entry.verification_state is VerificationState.PATH_TRACKED
    assert entry.authority_state is AuthorityState.UNKNOWN
    assert entry.coverage_state.value == "NOT_ESTABLISHED"
    relative = f"knowledge/{UNBLOCK_SOURCE.article_id}.md"
    assert (GIT_ROOT / relative).is_file()
    assert subprocess.run(
        ("git", "-C", str(GIT_ROOT), "ls-files", "--error-unmatch", "--", relative),
        check=False,
        capture_output=True,
    ).returncode == 0


def test_probability_engine_has_no_inferred_link(audit):
    entry = next(item for item in audit.production_entries if item.element_type is ProductionElementType.PROBABILITY_ENGINE)
    assert entry.link_state is ProvenanceLinkState.NO_LINK
    assert entry.source_ids == ()


def test_manifest_inventory_is_unique_and_blob_verified(audit):
    manifests = [item for item in audit.source_artifacts if item.source_kind == "PROVENANCE_MANIFEST_ARTIFACT"]
    assert len(manifests) == 11
    assert len({item.manifest_id for item in manifests}) == 11
    assert all(item.verification_state is VerificationState.BLOB_VERIFIED for item in manifests)
    assert all(item.artifact_presence is ArtifactPresenceState.HISTORICAL_ONLY for item in manifests)
    assert all(item.category == "artifact" for item in manifests)
    live_manifests = _manifest_entries()
    assert {item.manifest_id for item in manifests} == {
        item.logical_id for item in live_manifests
    }
    validator = ProvenanceValidator(GIT_ROOT)
    assert all(validator.resolve_and_validate(item).is_authorized for item in live_manifests)


def test_git_verification_is_distinct_from_authority(audit):
    manifests = [item for item in audit.source_artifacts if item.verification_state is VerificationState.BLOB_VERIFIED]
    assert manifests
    assert all(item.authority_state is AuthorityState.HISTORICAL_RECORD for item in manifests)
    knowledge = [item for item in audit.source_artifacts if item.source_kind == "KNOWLEDGE_SOURCE_REFERENCE"]
    assert knowledge
    assert all(item.authority_state is AuthorityState.UNKNOWN for item in knowledge)


def test_deferred_capabilities_are_excluded_from_production(audit):
    deferred = {item.capability_id for item in audit.deferred_capabilities}
    primary = {item.element_id.upper() for item in audit.production_entries}
    assert {"RESTRICTED_CHOICE", "VACANT_PLACES", "NATURAL_1NT_RESPONSES", "SAFETY_PLAY"} <= deferred
    assert deferred.isdisjoint(primary)


def test_reviewed_baselines_and_audit_status_pass(audit):
    primary = dict(audit.primary_summary)
    sources = dict(audit.source_summary)
    diagnostics = dict(audit.diagnostics)
    assert primary["primary_production_elements"] == 47
    assert primary["bidding_routes"] == 45
    assert sources["manifest_entries"] == 11
    assert sources["manifest_artifacts_authorized"] == 11
    assert sources["manifest_source_category"] == 0
    assert diagnostics["route_rule_edges"] == 134
    assert diagnostics["unique_rule_ids"] == 92
    assert diagnostics["unique_rule_objects"] == 98
    assert audit.audit_status == "PASS"
