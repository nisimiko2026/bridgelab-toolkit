"""Phase 30G shadow composition of profile ownership and base handoff."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.base_system_composition import (
    BaseSystemCompositionAssessment,
    BaseSystemCompositionCapability,
    BaseSystemCompositionDisposition,
    BaseSystemContinuationRequest,
    compose_profile_opening_with_base,
)
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    AgreementSourceScope,
    PartnershipProfile,
    ResolvedAgreement,
    resolve_partnership_profile,
)
from bridge.profile_compiler import CompilationAction, compile_profile_plan
from bridge.profile_opening_adapter import (
    ProfileOpeningAssessment,
    ProfileOpeningDisposition,
    evaluate_profile_opening_shadow,
)
from bridge.profile_opening_current_readiness_audit import build_current_profile_opening_readiness_audit
from bridge.runtime_partnership_selection import (
    TablePartnershipPlans,
    evaluate_selected_profile_opening_shadow,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.treatment_bindings import NISIM_NILY_SIX_MINOR_BINDING


FAMILY = "opening.three_level.six_minor"
HAND = "7.84.KQJT96.9742"


@pytest.fixture
def base_agreements():
    # Structural comparison fixture, not a complete 2/1 production system.
    return tuple(
        ResolvedAgreement(family, treatment, AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM)
        for family, treatment in (
            ("opening.1nt", "standard_15_17"),
            ("opening.2d", "natural_weak_two"),
            ("opening.2h", "natural_weak_two"),
            ("opening.2s", "natural_weak_two"),
            ("opening.2nt", "natural_2nt"),
        )
    )


def _plan(profile, base_agreements=()):
    resolved = resolve_partnership_profile(profile, base_agreements=base_agreements)
    return compile_profile_plan(resolved, base_agreements=base_agreements)


@pytest.fixture
def plans(base_agreements):
    nisim = _plan(NISIM_NILY_PROFILE, base_agreements)
    peer_profile = PartnershipProfile(
        "phase30g-peer", "30G.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    return nisim, _plan(peer_profile, base_agreements)


def _synthetic_assessment(
    plan, family, *, disposition=ProfileOpeningDisposition.NO_BINDING,
    supported_call=None, binding=None, policy_assessment=None,
):
    directive = plan.directive(family)
    return ProfileOpeningAssessment(
        profile_id=plan.profile_id,
        profile_version=plan.profile_version,
        base_system=plan.base_system,
        family=family,
        effective_treatment_id=None if directive is None else directive.effective_treatment_id,
        disposition=disposition,
        acting_seat=Seat.NORTH,
        opening_position=1,
        vulnerability=Vulnerability.EW,
        binding=binding,
        policy_assessment=policy_assessment,
        supported_call=supported_call,
        reason="Test-only structural ownership witness; no convention evaluated.",
    )


def test_exact_dispositions_immutable_records_and_stable_serialization(plans):
    assert tuple(item.value for item in BaseSystemCompositionDisposition) == (
        "PARTNERSHIP_CALL", "BASE_SYSTEM_CONTINUATION",
        "PROFILE_OVERRIDE_BLOCKS_BASE", "UNRESOLVED",
    )
    nisim, peer = plans
    result = compose_profile_opening_with_base(peer, _synthetic_assessment(peer, FAMILY))
    assert isinstance(result, BaseSystemCompositionAssessment)
    request = result.base_continuation
    assert isinstance(request, BaseSystemContinuationRequest)
    assert request.contract_version == result.composition_version == "30G.1"
    assert result.production_adopted is False
    with pytest.raises(FrozenInstanceError):
        result.partnership_call = "P"
    with pytest.raises(FrozenInstanceError):
        request.base_system = SystemProfile.SAYC
    with pytest.raises(ValueError):
        replace(result, production_adopted=True)
    assert json.loads(result.to_json()) == result.to_dict()
    assert json.loads(request.to_json()) == request.to_dict()
    assert result.to_json() == compose_profile_opening_with_base(
        peer, _synthetic_assessment(peer, FAMILY)
    ).to_json()
    assert nisim.base_system is result.base_system is SystemProfile.TWO_OVER_ONE_GF


def test_nisim_added_six_minor_supported_call_owns_first_seat(plans):
    nisim, peer = plans
    assert nisim.directive(FAMILY).action is CompilationAction.ADD
    table = TablePartnershipPlans(nisim, peer)
    selected = evaluate_selected_profile_opening_shadow(
        table, hand=Hand.parse(HAND), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW,
    )
    assert selected.selection.plan is nisim
    assert selected.assessment.disposition is ProfileOpeningDisposition.SUPPORTED_CALL
    assert selected.assessment.supported_call == "3D"
    composed = compose_profile_opening_with_base(selected.selection.plan, selected.assessment)
    assert composed.compilation_action is CompilationAction.ADD
    assert composed.profile_disposition is ProfileOpeningDisposition.SUPPORTED_CALL
    assert composed.composition_disposition is BaseSystemCompositionDisposition.PARTNERSHIP_CALL
    assert composed.partnership_call == "3D"
    assert composed.base_continuation is None


@pytest.mark.parametrize("hand,calls,vulnerability", [
    ("7.84.QJT986.9742", (), Vulnerability.NONE),
    (HAND, ("P", "P", "P"), Vulnerability.EW),
    ("7.84.KQJT986.742", (), Vulnerability.EW),
])
def test_added_treatment_evaluated_abstention_requests_declared_base(
    plans, hand, calls, vulnerability
):
    nisim, _ = plans
    assessment = evaluate_profile_opening_shadow(
        nisim, hand=Hand.parse(hand), auction=Auction(Seat.NORTH, calls),
        vulnerability=vulnerability,
    )
    assert assessment.disposition is ProfileOpeningDisposition.ABSTAIN
    assert assessment.binding == NISIM_NILY_SIX_MINOR_BINDING
    assert assessment.policy_assessment is not None
    result = compose_profile_opening_with_base(nisim, assessment)
    assert result.composition_disposition is BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION
    assert result.partnership_call is None
    assert result.base_continuation.base_system is nisim.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert result.base_continuation.profile_id == nisim.profile_id
    assert result.base_continuation.family == FAMILY
    assert result.partnership_call != "P"


def test_peer_without_six_minor_directive_requests_its_own_base(plans):
    nisim, peer = plans
    assert peer.directive(FAMILY) is None
    table = TablePartnershipPlans(nisim, peer)
    selected = evaluate_selected_profile_opening_shadow(
        table, hand=Hand.parse(HAND), auction=Auction(Seat.EAST),
        vulnerability=Vulnerability.EW,
    )
    assert selected.selection.plan is peer
    assert selected.assessment.disposition is ProfileOpeningDisposition.NO_BINDING
    result = compose_profile_opening_with_base(peer, selected.assessment)
    assert result.compilation_action is None
    assert result.composition_disposition is BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION
    assert result.base_continuation.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert result.partnership_call is None
    reversed_table = TablePartnershipPlans(peer, nisim)
    reversed_selected = evaluate_selected_profile_opening_shadow(
        reversed_table, hand=Hand.parse(HAND), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW,
    )
    assert reversed_selected.selection.plan is peer
    assert compose_profile_opening_with_base(peer, reversed_selected.assessment).base_continuation.base_system is SystemProfile.TWO_OVER_ONE_GF


def test_keep_preserves_base_meaning_without_partnership_call(plans):
    nisim, peer = plans
    for plan in (nisim, peer):
        directive = plan.directive("opening.1nt")
        assert directive.action is CompilationAction.KEEP
        assessment = _synthetic_assessment(plan, "opening.1nt")
        result = compose_profile_opening_with_base(plan, assessment)
        assert result.compilation_action is CompilationAction.KEEP
        assert result.composition_disposition is BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION
        assert result.base_continuation.base_system is plan.base_system
        assert result.partnership_call is None


@pytest.mark.parametrize("family,effective", [
    ("opening.2d", "multi_2d"),
    ("opening.2h", "nisim_nily_5h_5minor"),
])
def test_canonical_replacement_never_resurrects_base_treatment(plans, family, effective):
    nisim, _ = plans
    directive = nisim.directive(family)
    assert directive.action is CompilationAction.REPLACE
    assert directive.effective_treatment_id == effective
    assert directive.base_treatment_id == "natural_weak_two"
    assessment = _synthetic_assessment(nisim, family)
    result = compose_profile_opening_with_base(nisim, assessment)
    assert result.compilation_action is CompilationAction.REPLACE
    assert result.composition_disposition is BaseSystemCompositionDisposition.PROFILE_OVERRIDE_BLOCKS_BASE
    assert result.partnership_call is result.base_continuation is None
    assert result.partnership_call != "P"
    # A hypothetical future replacement evaluator's explicit call would own it.
    supported = _synthetic_assessment(
        nisim, family, disposition=ProfileOpeningDisposition.SUPPORTED_CALL,
        supported_call="2D" if family == "opening.2d" else "2H",
    )
    owned = compose_profile_opening_with_base(nisim, supported)
    assert owned.composition_disposition is BaseSystemCompositionDisposition.PARTNERSHIP_CALL
    assert owned.base_continuation is None


def test_replace_abstention_blocks_base_even_if_synthetic_assessment_is_evaluated(plans):
    nisim, _ = plans
    assessment = _synthetic_assessment(
        nisim, "opening.2d", disposition=ProfileOpeningDisposition.ABSTAIN
    )
    result = compose_profile_opening_with_base(nisim, assessment)
    assert result.composition_disposition is BaseSystemCompositionDisposition.PROFILE_OVERRIDE_BLOCKS_BASE
    assert result.base_continuation is None


def test_synthetic_remove_blocks_base_and_produces_no_call(base_agreements):
    profile = PartnershipProfile(
        "phase30g-remove", "30G.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("opening.2d", AgreementResolution.DISABLE),),
    )
    plan = _plan(profile, base_agreements)
    assert plan.directive("opening.2d").action is CompilationAction.REMOVE
    result = compose_profile_opening_with_base(
        plan, _synthetic_assessment(plan, "opening.2d")
    )
    assert result.compilation_action is CompilationAction.REMOVE
    assert result.composition_disposition is BaseSystemCompositionDisposition.PROFILE_OVERRIDE_BLOCKS_BASE
    assert result.partnership_call is result.base_continuation is None


def test_selected_add_without_binding_is_unresolved_not_base_fallback():
    profile = PartnershipProfile(
        "phase30g-unbound", "30G.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection(FAMILY, AgreementResolution.ENABLE,
                            "unimplemented_six_minor"),),
    )
    plan = _plan(profile)
    assert plan.directive(FAMILY).action is CompilationAction.ADD
    assessment = evaluate_profile_opening_shadow(
        plan, hand=Hand.parse(HAND), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW,
    )
    assert assessment.disposition is ProfileOpeningDisposition.NO_BINDING
    assert assessment.effective_treatment_id == "unimplemented_six_minor"
    result = compose_profile_opening_with_base(plan, assessment)
    assert result.composition_disposition is BaseSystemCompositionDisposition.UNRESOLVED
    assert result.partnership_call is result.base_continuation is None


def test_add_abstain_without_confirmed_evaluation_is_unresolved(plans):
    nisim, _ = plans
    forged = _synthetic_assessment(nisim, FAMILY, disposition=ProfileOpeningDisposition.ABSTAIN)
    result = compose_profile_opening_with_base(nisim, forged)
    assert result.composition_disposition is BaseSystemCompositionDisposition.UNRESOLVED
    assert result.base_continuation is None


def test_mismatched_profile_system_family_and_treatment_are_rejected(plans):
    nisim, peer = plans
    assessment = evaluate_profile_opening_shadow(
        nisim, hand=Hand.parse(HAND), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW,
    )
    with pytest.raises(ValueError, match="does not belong"):
        compose_profile_opening_with_base(peer, assessment)
    with pytest.raises(ValueError, match="does not belong"):
        compose_profile_opening_with_base(nisim, replace(assessment, base_system=SystemProfile.SAYC))
    with pytest.raises(ValueError, match="does not belong"):
        compose_profile_opening_with_base(nisim, replace(assessment, profile_version="other"))
    with pytest.raises(ValueError, match="treatment does not match"):
        compose_profile_opening_with_base(nisim, replace(assessment, family="opening.2d"))
    with pytest.raises(ValueError, match="treatment does not match"):
        compose_profile_opening_with_base(nisim, replace(assessment, effective_treatment_id="other"))
    with pytest.raises(ValueError, match="binding does not match"):
        compose_profile_opening_with_base(
            nisim, replace(assessment, family="opening.2d", effective_treatment_id="multi_2d")
        )


def test_result_invariants_reject_invalid_ownership_claims(plans):
    nisim, peer = plans
    base = compose_profile_opening_with_base(peer, _synthetic_assessment(peer, FAMILY))
    with pytest.raises(ValueError):
        replace(base, composition_disposition=BaseSystemCompositionDisposition.PARTNERSHIP_CALL)
    with pytest.raises(ValueError):
        replace(base, partnership_call="P")
    with pytest.raises(ValueError):
        replace(base, base_continuation=replace(base.base_continuation,
                                                base_system=SystemProfile.SAYC))
    with pytest.raises(ValueError):
        replace(base, composition_disposition=BaseSystemCompositionDisposition.UNRESOLVED)
    with pytest.raises(ValueError):
        replace(base, composition_disposition=BaseSystemCompositionDisposition.PARTNERSHIP_CALL,
                partnership_call="P")
    with pytest.raises(ValueError):
        replace(base, compilation_action=CompilationAction.REPLACE)
    supported_pass = _synthetic_assessment(
        nisim, FAMILY, disposition=ProfileOpeningDisposition.SUPPORTED_CALL,
        supported_call="P",
    )
    with pytest.raises(ValueError, match="Pass"):
        compose_profile_opening_with_base(nisim, supported_pass)
    assert nisim.base_system is peer.base_system


def test_composition_is_pure_and_capability_is_shadow_only(plans):
    nisim, peer = plans
    assessment = evaluate_profile_opening_shadow(
        nisim, hand=Hand.parse(HAND), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW,
    )
    before = (nisim.to_json(), peer.to_json(), assessment.to_json(),
              NISIM_NILY_SIX_MINOR_BINDING.to_json())
    first = compose_profile_opening_with_base(nisim, assessment)
    second = compose_profile_opening_with_base(nisim, assessment)
    assert first == second and first.to_json() == second.to_json()
    assert before == (nisim.to_json(), peer.to_json(), assessment.to_json(),
                      NISIM_NILY_SIX_MINOR_BINDING.to_json())
    capability = BaseSystemCompositionCapability()
    assert capability.phase == "30G" and capability.version == "30G.1"
    assert capability.composition_contract_ready is True
    assert capability.base_continuation_request_ready is True
    assert capability.base_execution_ready is False
    assert capability.production_bidding_changed is capability.production_adopted is False
    assert json.loads(capability.to_json()) == capability.to_dict()
    with pytest.raises(FrozenInstanceError):
        capability.base_execution_ready = True
    with pytest.raises(ValueError):
        replace(capability, base_execution_ready=True)
    with pytest.raises(ValueError):
        replace(capability, production_adopted=True)


def test_historical_audit_router_context_and_simulator_remain_unchanged(plans):
    nisim, peer = plans
    profile_before = NISIM_NILY_PROFILE.to_json()
    plan_before = nisim.to_json()
    audit_before = build_current_profile_opening_readiness_audit().to_json()
    before_router = create_standard_sayc_router()
    before_ids = tuple(route.route_id for route in before_router.routes)
    compose_profile_opening_with_base(peer, _synthetic_assessment(peer, FAMILY))
    after_router = create_standard_sayc_router()
    after_ids = tuple(route.route_id for route in after_router.routes)
    assert len(before_ids) == len(after_ids) == 45 and before_ids == after_ids
    assert not any("nisim" in route_id.casefold() or "30g" in route_id.casefold()
                   for route_id in after_ids)
    hand = Hand.parse(HAND)
    context = BiddingContext.create(
        hand=hand, auction=Auction(Seat.NORTH), vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )
    assert after_router.evaluate(context).recommended_call.serialize() == "2D"
    assert after_router.match(BiddingContext.create(
        hand=hand, auction=Auction(Seat.NORTH, ("P", "P")),
        vulnerability=Vulnerability.EW, system=SystemContext("SAYC"),
    )) is None
    assert NISIM_NILY_PROFILE.to_json() == profile_before
    assert nisim.to_json() == plan_before
    assert NISIM_NILY_SIX_MINOR_BINDING.production_adopted is False
    assert build_current_profile_opening_readiness_audit().to_json() == audit_before
    assert tuple(item.name for item in fields(SystemContext)) == ("system", "options")
    assert tuple(item.name for item in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )


def test_composition_module_has_no_router_engine_policy_or_context_dependency():
    path = Path(__file__).resolve().parents[1] / "bridge" / "base_system_composition.py"
    source = path.read_text()
    tree = ast.parse(source)
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    forbidden = (
        "sayc_route_configuration", "engine_router", "bidding_engine", "deal_analysis",
        "full_deal_analysis", "full_deal_application", "deal_simulator",
        "treatment_bindings", "six_minor_preempt_policy", "bidding_rules",
    )
    assert not any(module and any(name in module for name in forbidden) for module in imports)
    assert "create_standard_sayc_router" not in source
    assert "SystemContext" not in source and "BiddingContext" not in source
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in {"EngineRoute", "BiddingEngine", "RuleDecision",
                                        "BiddingEngineResult"} for node in ast.walk(tree))
