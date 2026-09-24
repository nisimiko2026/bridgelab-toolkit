"""Phase 30J typed, source-grounded 2/1 opening ownership matrix."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.partnership_profiles import (
    AgreementResolution as Resolution, AgreementSelection,
    AgreementSourceScope as Scope, PartnershipProfile, ResolvedAgreement,
    resolve_partnership_profile,
)
from bridge.profile_compiler import CompilationAction as Action, compile_profile_plan
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.two_over_one_opening_execution_boundary import (
    OpeningExecutionBoundaryState as State, OpeningExecutionBoundary,
    TwoOverOneOpeningExecutionBoundaryAudit,
    audit_two_over_one_opening_execution_boundary,
)


FAMILIES = (
    "opening.1c", "opening.1d", "opening.1h", "opening.1s", "opening.1nt",
    "opening.2c", "opening.2d", "opening.2h", "opening.2s", "opening.2nt",
    "opening.three_level", "opening.three_level.six_minor",
)
REPLACED = ("opening.2d", "opening.2h", "opening.2s", "opening.2nt")


def _plan(profile, base=()):
    return compile_profile_plan(
        resolve_partnership_profile(profile, base_agreements=base),
        base_agreements=base,
    )


@pytest.fixture(scope="module")
def declared_base():
    # Opaque structural comparison data only. These IDs claim no native 2/1
    # weak-two or 2NT meaning or opening implementation.
    return tuple(ResolvedAgreement(family, f"opaque_base_{family.split('.')[-1]}",
                                   Resolution.ENABLE, Scope.SYSTEM)
                 for family in REPLACED)


@pytest.fixture(scope="module")
def audits(declared_base):
    nisim = _plan(NISIM_NILY_PROFILE)
    nisim_with_base = _plan(NISIM_NILY_PROFILE, declared_base)
    peer = PartnershipProfile("phase30j-peer", "30J.test", SystemProfile.TWO_OVER_ONE_GF, ())
    peer_without_base = _plan(peer)
    peer_with_base = _plan(peer, declared_base)
    return (
        (nisim, audit_two_over_one_opening_execution_boundary(nisim)),
        (nisim_with_base, audit_two_over_one_opening_execution_boundary(nisim_with_base)),
        (peer_without_base, audit_two_over_one_opening_execution_boundary(peer_without_base)),
        (peer_with_base, audit_two_over_one_opening_execution_boundary(peer_with_base)),
    )


def test_exact_states_family_ids_and_deterministic_immutable_records(audits):
    plan, audit = audits[0]
    assert tuple(item.value for item in State) == (
        "BASE_EXECUTABLE", "BASE_SOURCE_PARTIAL", "PROFILE_OVERRIDE", "UNSUPPORTED")
    assert isinstance(audit, TwoOverOneOpeningExecutionBoundaryAudit)
    assert {item.family for item in audit.boundaries} == set(FAMILIES)
    assert len(audit.boundaries) == len(FAMILIES)
    assert all(isinstance(item, OpeningExecutionBoundary) and item.evidence and item.reason
               for item in audit.boundaries)
    assert all(item.production_adopted is False for item in audit.boundaries)
    assert audit.profile_id == plan.profile_id and audit.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert json.loads(audit.to_json()) == audit.to_dict()
    assert audit.to_json() == audit_two_over_one_opening_execution_boundary(plan).to_json()
    with pytest.raises(FrozenInstanceError):
        audit.safe_opening_execution_ready = True
    with pytest.raises(FrozenInstanceError):
        audit.boundaries[0].state = State.BASE_EXECUTABLE
    with pytest.raises(ValueError, match="exactly once"):
        replace(audit, boundaries=audit.boundaries + (audit.boundaries[0],))
    with pytest.raises(ValueError, match="complete source and implementation"):
        replace(audit.boundary("opening.1c"), state=State.BASE_EXECUTABLE)
    assert audit.production_bidding_changed is False and audit.production_adopted is False


def test_only_two_over_one_gf_is_accepted():
    sayc = _plan(PartnershipProfile("sayc-peer", "1", SystemProfile.SAYC, ()))
    with pytest.raises(ValueError, match="TWO_OVER_ONE_GF"):
        audit_two_over_one_opening_execution_boundary(sayc)
    with pytest.raises(TypeError):
        audit_two_over_one_opening_execution_boundary(None)


@pytest.mark.parametrize("family", REPLACED)
def test_nisim_replacement_ownership_with_or_without_base_catalog(audits, family):
    default_plan, default_audit = audits[0]
    structural_plan, structural_audit = audits[1]
    direct = default_plan.directive(family)
    structural = structural_plan.directive(family)
    assert direct.action is Action.ADD
    assert direct.effective_resolution is Resolution.REPLACE
    assert structural.action is Action.REPLACE
    assert structural.effective_resolution is Resolution.REPLACE
    for plan, audit in ((default_plan, default_audit), (structural_plan, structural_audit)):
        boundary = audit.boundary(family)
        assert boundary.state is State.PROFILE_OVERRIDE
        assert boundary.compiled_action is plan.directive(family).action
        assert boundary.effective_resolution is Resolution.REPLACE
        assert boundary.effective_treatment_id == plan.directive(family).effective_treatment_id
        assert not boundary.implementation_available
        assert "base reuse" in boundary.reason
    if family == "opening.2d":
        assert default_audit.boundary(family).effective_treatment_id == "multi_2d"


def test_remove_add_keep_and_no_directive_ownership(declared_base, audits):
    removed = PartnershipProfile(
        "removed", "1", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("opening.2d", Resolution.DISABLE),),
    )
    removed_plan = _plan(removed, declared_base)
    removed_boundary = audit_two_over_one_opening_execution_boundary(removed_plan).boundary("opening.2d")
    assert removed_plan.directive("opening.2d").action is Action.REMOVE
    assert removed_boundary.state is State.PROFILE_OVERRIDE
    added = PartnershipProfile(
        "added", "1", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("opening.2d", Resolution.ENABLE, "profile_2d"),),
    )
    added_plan = _plan(added)
    added_boundary = audit_two_over_one_opening_execution_boundary(added_plan).boundary("opening.2d")
    assert added_plan.directive("opening.2d").action is Action.ADD
    assert added_boundary.state is State.UNSUPPORTED
    assert added_boundary.effective_resolution is Resolution.ENABLE
    keep_plan, keep_audit = audits[3]
    assert keep_plan.directive("opening.2d").action is Action.KEEP
    assert keep_audit.boundary("opening.2d").state is State.UNSUPPORTED
    no_directive_plan, no_directive_audit = audits[2]
    assert no_directive_plan.directive("opening.2d") is None
    assert no_directive_audit.boundary("opening.2d").state is State.UNSUPPORTED


def test_partnership_isolation_and_pilot_overlay(audits):
    nisim = audits[0][1]
    peer = audits[2][1]
    for family in REPLACED:
        assert nisim.boundary(family).state is State.PROFILE_OVERRIDE
        assert peer.boundary(family).state is State.UNSUPPORTED
    pilot = nisim.boundary("opening.three_level.six_minor")
    assert pilot.compiled_action is Action.ADD
    assert pilot.effective_resolution is Resolution.ENABLE
    assert pilot.effective_treatment_id == "nisim_nily_six_minor_preempt"
    assert pilot.state is State.UNSUPPORTED
    assert any("profile-owned" in evidence for evidence in pilot.evidence)
    assert peer.boundary(pilot.family).compiled_action is None
    assert peer.boundary(pilot.family).state is State.UNSUPPORTED


def test_one_level_source_partial_and_unsupported_openings(audits):
    nisim = audits[0][1]
    for family in ("opening.1c", "opening.1d", "opening.1h", "opening.1s", "opening.1nt"):
        boundary = nisim.boundary(family)
        assert boundary.state is State.BASE_SOURCE_PARTIAL
        assert boundary.source_complete is False
        assert boundary.implementation_available is False
        assert any("2-over-1.md#Opening Requirements" in item for item in boundary.evidence)
    assert "3+" in nisim.boundary("opening.1c").reason
    assert "4+" in nisim.boundary("opening.1d").reason
    assert "12–21" in nisim.boundary("opening.1h").reason
    assert "12–21" in nisim.boundary("opening.1s").reason
    assert "14–16" in nisim.boundary("opening.1nt").reason
    assert "16–18" in nisim.boundary("opening.1nt").reason
    for family in ("opening.2c", "opening.three_level", "opening.three_level.six_minor"):
        assert nisim.boundary(family).state is State.UNSUPPORTED
    peer = audits[2][1]
    for family in ("opening.2d", "opening.2h", "opening.2s", "opening.2nt"):
        assert peer.boundary(family).state is State.UNSUPPORTED
    assert all(item.state is not State.BASE_EXECUTABLE for item in nisim.boundaries)


def test_source_anchors_are_present_in_canonical_article():
    source = Path(__file__).resolve().parents[2] / "knowledge" / "bidding" / "systems" / "2-over-1.md"
    article = source.read_text(encoding="utf-8")
    for excerpt in (
        "# System Requirements", "# Opening Requirements", "## 1♣", "## 1♦",
        "## 1♥", "## 1♠", "## 1NT", "14-16", "16-18", "Approximately:",
    ):
        assert excerpt in article
    # These source sections describe a 2NT response/rebid, not a 2NT opening.
    assert "Jacoby 2NT" in article
    assert "# Partnership Agreements" in article


def test_counts_readiness_and_recommendation_are_derived(audits):
    current = audits[0][1]
    assert (current.base_executable_count, current.base_source_partial_count,
            current.profile_override_count, current.unsupported_count) == (0, 5, 4, 3)
    assert sum((current.base_executable_count, current.base_source_partial_count,
                current.profile_override_count, current.unsupported_count)) == len(current.boundaries)
    assert current.safe_opening_execution_ready is False
    assert current.recommended_next_phase == "30K_EXPLICIT_TWO_OVER_ONE_OPENING_CONTRACT"
    # The computed property responds to a hypothetical complete future base
    # implementation, without changing today's source/implementation findings.
    future = replace(current, boundaries=tuple(
        boundary if boundary.state is State.PROFILE_OVERRIDE
        or boundary.family == "opening.three_level.six_minor" else
        replace(boundary, state=State.BASE_EXECUTABLE,
                source_complete=True, implementation_available=True)
        for boundary in current.boundaries))
    assert future.safe_opening_execution_ready is True
    assert future.recommended_next_phase == "30K_OPENING_EXECUTION_INTEGRATION"


def test_route_context_and_audit_only_static_guards():
    before = tuple(route.route_id for route in create_standard_sayc_router().routes)
    source = Path(__file__).resolve().parents[1] / "bridge" / "two_over_one_opening_execution_boundary.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    after = tuple(route.route_id for route in create_standard_sayc_router().routes)
    assert len(before) == len(after) == 45 and before == after
    assert not any(marker in route_id.casefold() for route_id in after
                   for marker in ("nisim", "30j"))
    assert tuple(item.name for item in fields(SystemContext)) == ("system", "options")
    assert tuple(item.name for item in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system")
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not imports.intersection({"sayc", "sayc_route_configuration", "engine_router",
                                     "bidding_engine", "deal_simulator", "evaluation", "models"})
    definitions = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not definitions.intersection({
        "Call", "RuleDecision", "BiddingEngineResult", "EngineRoute", "BiddingEngine",
        "BaseSystemExecutor", "create_sayc_opening_engine", "create_profile_router",
    })
