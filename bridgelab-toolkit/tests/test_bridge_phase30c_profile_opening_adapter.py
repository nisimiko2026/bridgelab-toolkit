"""Phase 30C: profile-aware six-minor opening pilot remains shadow-only."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.nisim_nily_six_minor_preempt_policy import (
    SixMinorDecision,
    assess_six_minor_three_level_preempt,
)
from bridge.opening_policy_six_minor_integration_audit import assess_opening_policy_with_six_minor
from bridge.opening_six_minor_production_adoption_audit import build_six_minor_production_adoption_audit
from bridge.partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    PartnershipProfile,
    resolve_partnership_profile,
)
from bridge.profile_compiler import compile_profile_plan
from bridge.profile_opening_adapter import (
    ProfileOpeningAssessment,
    ProfileOpeningDisposition,
    evaluate_profile_opening_shadow,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.treatment_bindings import NISIM_NILY_SIX_MINOR_BINDING


FAMILY = "opening.three_level.six_minor"
HAND = "7.84.KQJT96.9742"


def _plan(profile=NISIM_NILY_PROFILE):
    resolved = resolve_partnership_profile(profile)
    return compile_profile_plan(resolved)


def _assess(plan=None, *, hand=HAND, calls=(), vulnerability=Vulnerability.EW):
    return evaluate_profile_opening_shadow(
        _plan() if plan is None else plan,
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=vulnerability,
    )


def test_typed_frozen_result_metadata_and_stable_serialization():
    assert tuple(item.value for item in ProfileOpeningDisposition) == (
        "NO_BINDING", "SUPPORTED_CALL", "ABSTAIN"
    )
    plan = _plan()
    result = _assess(plan)
    assert isinstance(result, ProfileOpeningAssessment)
    assert (result.profile_id, result.profile_version, result.base_system) == (
        plan.profile_id, plan.profile_version, plan.base_system
    )
    assert result.family == FAMILY
    assert result.effective_treatment_id == "nisim_nily_six_minor_preempt"
    assert result.adapter_version == "30C.1"
    assert result.production_adopted is False
    with pytest.raises(FrozenInstanceError):
        result.supported_call = "P"
    with pytest.raises(ValueError):
        replace(result, production_adopted=True)
    assert result.to_json() == _assess(plan).to_json()
    serialized = json.loads(result.to_json())
    assert serialized == result.to_dict()
    assert serialized["disposition"] == "SUPPORTED_CALL"
    assert serialized["binding"]["implementation_kind"] == "POLICY_ASSESSOR"
    assert serialized["policy_assessment"]["decision"] == "THREE_LEVEL"


@pytest.mark.parametrize(
    "calls,seat,position,decision,disposition,call",
    [
        ((), Seat.NORTH, 1, SixMinorDecision.THREE_LEVEL,
         ProfileOpeningDisposition.SUPPORTED_CALL, "3D"),
        (("P", "P"), Seat.SOUTH, 3, SixMinorDecision.THREE_LEVEL,
         ProfileOpeningDisposition.SUPPORTED_CALL, "3D"),
        (("P", "P", "P"), Seat.WEST, 4, SixMinorDecision.NO_THREE_LEVEL,
         ProfileOpeningDisposition.ABSTAIN, None),
    ],
)
def test_auction_derived_seat_and_exact_policy_result(
    calls, seat, position, decision, disposition, call
):
    auction = Auction(Seat.NORTH, calls)
    hand = Hand.parse(HAND)
    result = evaluate_profile_opening_shadow(
        _plan(), hand=hand, auction=auction, vulnerability=Vulnerability.EW
    )
    direct = assess_six_minor_three_level_preempt(
        hand, seat=seat, vulnerability=Vulnerability.EW, opening_position=position
    )
    assert result.acting_seat is seat is auction.next_seat
    assert result.opening_position == position
    assert result.policy_assessment == direct
    assert direct.decision is decision
    assert (result.disposition, result.supported_call) == (disposition, call)
    assert result.binding == NISIM_NILY_SIX_MINOR_BINDING
    assert result.production_adopted is direct.production_adopted is False


def test_second_seat_a_plus_witness_uses_phase29t_threshold():
    hand = Hand.parse("7.84.AQJT96.9742")
    auction = Auction(Seat.NORTH, ("P",))
    direct = assess_six_minor_three_level_preempt(
        hand, seat=Seat.EAST, vulnerability=Vulnerability.EW, opening_position=2
    )
    result = evaluate_profile_opening_shadow(
        _plan(), hand=hand, auction=auction, vulnerability=Vulnerability.EW
    )
    assert result.acting_seat is auction.next_seat is Seat.EAST
    assert result.opening_position == 2
    assert direct.decision is SixMinorDecision.THREE_LEVEL
    assert result.policy_assessment == direct
    assert (result.disposition, result.supported_call) == (
        ProfileOpeningDisposition.SUPPORTED_CALL, direct.preferred_call
    )


@pytest.mark.parametrize(
    "hand,vulnerability,decision,disposition,call",
    [
        ("7.K4.KQJT96.A742", Vulnerability.EW, SixMinorDecision.ONE_LEVEL,
         ProfileOpeningDisposition.SUPPORTED_CALL, "1D"),
        ("7.84.QJT986.9742", Vulnerability.NONE, SixMinorDecision.NO_THREE_LEVEL,
         ProfileOpeningDisposition.ABSTAIN, None),
        ("7.84.KQJT986.742", Vulnerability.EW, SixMinorDecision.NOT_APPLICABLE,
         ProfileOpeningDisposition.ABSTAIN, None),
    ],
)
def test_rule20_negative_and_not_applicable_preserve_policy(
    hand, vulnerability, decision, disposition, call
):
    result = _assess(hand=hand, vulnerability=vulnerability)
    assert result.policy_assessment.decision is decision
    assert (result.disposition, result.supported_call) == (disposition, call)
    assert result.supported_call != "P"


def test_other_partnership_isolation_and_same_treatment_portability():
    other = PartnershipProfile(
        "isolation-partnership-b", "30C.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    no_binding = _assess(_plan(other), calls=("P", "P"))
    assert no_binding.disposition is ProfileOpeningDisposition.NO_BINDING
    assert no_binding.binding is no_binding.policy_assessment is no_binding.supported_call is None
    abstain = _assess(calls=("P", "P", "P"))
    assert abstain.disposition is ProfileOpeningDisposition.ABSTAIN
    assert abstain.binding is not None and abstain.policy_assessment is not None

    portable = PartnershipProfile(
        "other-pilot-partnership", "30C.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection(FAMILY, AgreementResolution.ENABLE,
                            "nisim_nily_six_minor_preempt"),),
    )
    result = _assess(_plan(portable), calls=("P", "P"))
    assert result.profile_id == portable.profile_id != NISIM_NILY_PROFILE.profile_id
    assert result.binding == NISIM_NILY_SIX_MINOR_BINDING
    assert (result.disposition, result.supported_call) == (
        ProfileOpeningDisposition.SUPPORTED_CALL, "3D"
    )


@pytest.mark.parametrize("treatment,parameters", [
    ("unimplemented_six_minor", ()),
    ("nisim_nily_six_minor_preempt", (("unhandled", "value"),)),
])
def test_unsupported_effective_treatment_fails_closed(treatment, parameters):
    profile = PartnershipProfile(
        "unsupported-pilot-partnership", "30C.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection(FAMILY, AgreementResolution.ENABLE, treatment, parameters),),
    )
    result = _assess(_plan(profile))
    assert result.effective_treatment_id == treatment
    assert result.disposition is ProfileOpeningDisposition.NO_BINDING
    assert result.binding is result.policy_assessment is result.supported_call is None


@pytest.mark.parametrize("calls", [
    ("1C",), ("1D",), ("1H",), ("1S",), ("2C",), ("1C", "P"),
    ("P", "P", "P", "P"),
])
def test_auction_must_be_live_and_unopened(calls):
    with pytest.raises(ValueError, match="live, unopened Pass-only"):
        _assess(calls=calls)


@pytest.mark.parametrize("field,value", [
    ("plan", None), ("hand", None), ("auction", None), ("vulnerability", None),
])
def test_canonical_inputs_are_required(field, value):
    args = dict(
        plan=_plan(), hand=Hand.parse(HAND), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW,
    )
    args[field] = value
    with pytest.raises(TypeError):
        evaluate_profile_opening_shadow(**args)


def test_repeated_evaluation_does_not_mutate_inputs_or_binding():
    plan = _plan()
    hand = Hand.parse(HAND)
    auction = Auction(Seat.NORTH, ("P", "P"))
    before = (plan.to_json(), hand.serialize(), auction.serialize(),
              NISIM_NILY_SIX_MINOR_BINDING.to_json(), NISIM_NILY_PROFILE.to_json())
    first = evaluate_profile_opening_shadow(
        plan, hand=hand, auction=auction, vulnerability=Vulnerability.EW
    )
    second = evaluate_profile_opening_shadow(
        plan, hand=hand, auction=auction, vulnerability=Vulnerability.EW
    )
    assert first == second and first.to_json() == second.to_json()
    assert before == (plan.to_json(), hand.serialize(), auction.serialize(),
                      NISIM_NILY_SIX_MINOR_BINDING.to_json(), NISIM_NILY_PROFILE.to_json())
    assert plan.to_json() == _plan().to_json()


def test_no_router_engine_rule_imports_or_objects_in_adapter():
    source = (Path(__file__).resolve().parents[1] / "bridge" / "profile_opening_adapter.py").read_text()
    tree = ast.parse(source)
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any(module and any(name in module for name in (
        "engine_router", "sayc_route_configuration", "bidding_engine", "bidding_rules"
    )) for module in imports)
    for forbidden in ("EngineRoute", "BiddingEngine", "BiddingEngineResult", "RuleDecision",
                      "SystemContext", "BiddingContext", "create_standard_sayc_router",
                      "create_sayc_opening_engine"):
        assert forbidden not in source
    result = _assess()
    assert isinstance(result, ProfileOpeningAssessment)
    assert result.binding == NISIM_NILY_SIX_MINOR_BINDING


def test_production_diagnostics_and_route_inventory_are_unchanged():
    before = create_standard_sayc_router()
    before_ids = tuple(route.route_id for route in before.routes)
    hand = Hand.parse(HAND)
    first_auction = Auction(Seat.NORTH)
    third_auction = Auction(Seat.NORTH, ("P", "P"))
    first_context = BiddingContext.create(
        hand=hand, auction=first_auction, vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )
    third_context = BiddingContext.create(
        hand=hand, auction=third_auction, vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )
    assert before.evaluate(first_context).recommended_call.serialize() == "2D"
    assert before.match(third_context) is None
    assert _assess().supported_call == "3D"
    assert _assess(calls=("P", "P")).supported_call == "3D"
    after = create_standard_sayc_router()
    after_ids = tuple(route.route_id for route in after.routes)
    assert len(before_ids) == len(after_ids) == 45
    assert before_ids == after_ids
    assert not any("nisim" in value.casefold() or "30c" in value.casefold()
                   for value in after_ids)
    assert after.evaluate(first_context).recommended_call.serialize() == "2D"
    assert after.match(third_context) is None
    assert tuple(field.name for field in fields(SystemContext)) == ("system", "options")
    assert tuple(field.name for field in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )
    assert NISIM_NILY_SIX_MINOR_BINDING.production_adopted is False
    assert assess_opening_policy_with_six_minor(
        hand, auction=third_auction, vulnerability=Vulnerability.EW
    ).production_adopted is False
    audit = build_six_minor_production_adoption_audit()
    assert audit.production_changed is False
    assert audit.ready_for_production is False
