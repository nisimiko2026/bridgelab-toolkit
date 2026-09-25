"""Phase 30L partnership binding with Phase 29S consistency witnesses."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_opening_contract_binding import (
    OpeningBindingState as State, OpeningContractBinding,
    NisimNilyOpeningContractBinding, NisimNilyOpeningBindingCapability,
    bind_nisim_nily_opening_contract, capability_for_nisim_nily_opening_binding,
)
from bridge.nisim_nily_opening_policy import build_nisim_nily_opening_policy
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.opening_policy_consolidation_audit import (
    Classification, State as CheckState, assess_opening_policy,
)
from bridge.partnership_profiles import PartnershipProfile, resolve_partnership_profile
from bridge.profile_compiler import compile_profile_plan
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.two_over_one_opening_contract import build_two_over_one_opening_contract
from bridge.two_over_one_opening_execution_boundary import audit_two_over_one_opening_execution_boundary


EXPECTED = {
    "one_level_strength_policy", "minor_length_policy", "minor_selection_precedence",
    "equal_minor_precedence", "five_five_major_precedence", "one_notrump_range",
    "one_notrump_five_card_major_policy", "one_notrump_shape_policy",
    "suit_vs_notrump_precedence", "strong_hand_precedence",
}


@pytest.fixture(scope="module")
def bound():
    plan = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
    contract = build_two_over_one_opening_contract()
    before = plan.to_json(), contract.to_json()
    result = bind_nisim_nily_opening_contract(plan, contract)
    assert before == (plan.to_json(), contract.to_json())
    return plan, contract, result


def _make(shape, patterns):
    groups = []
    for length, honors in zip(shape, patterns):
        spots = "".join(rank for rank in "23456789T" if rank not in honors)
        groups.append(honors + spots[:length - len(honors)] or "-")
    return Hand.parse(".".join(groups))


def _assess(shape, patterns, *, passes=0):
    return assess_opening_policy(
        _make(shape, patterns), auction=Auction(Seat.NORTH, ("P",) * passes),
        vulnerability=Vulnerability.NONE,
    )


def _check(assessment, family):
    return next(item for item in assessment.checks if item.family == family)


def test_exact_schema_immutable_records_and_determinism(bound):
    plan, contract, result = bound
    assert tuple(item.value for item in State) == ("BOUND", "PARTIAL", "UNRESOLVED")
    assert isinstance(result, NisimNilyOpeningContractBinding)
    assert result.profile_id == plan.profile_id and result.profile_version == plan.profile_version
    assert result.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert result.base_contract_version == contract.contract_version == "30K.1"
    assert set(result.base_required_bindings) == EXPECTED == set(contract.required_bindings)
    assert {item.binding_id for item in result.bindings} == EXPECTED
    assert len(result.bindings) == len(EXPECTED) == 10
    assert tuple(item.binding_id for item in result.bindings) == tuple(sorted(EXPECTED))
    assert json.loads(result.to_json()) == result.to_dict()
    assert result.to_json() == bind_nisim_nily_opening_contract(plan).to_json()
    assert all(isinstance(item, OpeningContractBinding) and item.provenance
               and json.loads(item.to_json()) == item.to_dict()
               for item in result.bindings)
    with pytest.raises(FrozenInstanceError):
        result.ready_for_production = True
    with pytest.raises(FrozenInstanceError):
        result.bindings[0].state = State.BOUND
    with pytest.raises(ValueError, match="exactly once"):
        replace(result, bindings=result.bindings + (result.bindings[0],))
    with pytest.raises(ValueError, match="exactly once"):
        replace(result, bindings=result.bindings[:-1])


def test_base_contract_change_is_rejected(bound):
    plan, contract, result = bound
    nt = contract.family("opening.1nt")
    changed = replace(contract, families=tuple(
        replace(item, required_bindings=tuple(
            key for key in nt.required_bindings if key != "one_notrump_shape_policy"))
        if item.family == nt.family else item for item in contract.families))
    assert "one_notrump_shape_policy" not in changed.required_bindings
    with pytest.raises(ValueError, match="changed unexpectedly"):
        bind_nisim_nily_opening_contract(plan, changed)
    # A malformed future contract must also fail closed for an extra or
    # duplicated requirement, even if its frozen internals were bypassed.
    for ids in (contract.required_bindings + ("unexpected",),
                contract.required_bindings + (contract.required_bindings[0],)):
        forged = replace(contract)
        object.__setattr__(forged, "required_bindings", ids)
        with pytest.raises(ValueError, match="changed unexpectedly"):
            bind_nisim_nily_opening_contract(plan, forged)
    assert result.base_required_bindings == contract.required_bindings


def test_partnership_b_and_wrong_system_are_rejected(bound):
    plan, _, _ = bound
    peer = PartnershipProfile("phase30l-peer", "30L.test", SystemProfile.TWO_OVER_ONE_GF, ())
    peer_plan = compile_profile_plan(resolve_partnership_profile(peer))
    with pytest.raises(ValueError, match="Nisim"):
        bind_nisim_nily_opening_contract(peer_plan)
    wrong = replace(plan, base_system=SystemProfile.SAYC)
    with pytest.raises(ValueError, match="Nisim"):
        bind_nisim_nily_opening_contract(wrong)
    with pytest.raises(TypeError):
        bind_nisim_nily_opening_contract(None)
    missing = replace(plan, directives=tuple(d for d in plan.directives
                                            if d.family != "opening.2d"))
    with pytest.raises(ValueError, match="canonical Nisim"):
        bind_nisim_nily_opening_contract(missing)


def test_strength_binding_supersedes_historical_rule20_scope(bound):
    b = bound[2].binding("one_level_strength_policy")
    assert b.state is State.BOUND
    assert dict(b.parameters) == {
        "normal_hcp_min": 12, "rule20_min_score": 20,
        "rule20_can_establish_opening_strength": True,
        "failed_rule20_implies_pass": False,
    }
    assert b.current_authority == "PHASE29S"
    assert b.historical_authority == "PHASE29M" and b.supersedes_historical_scope
    historical = build_nisim_nily_opening_policy()
    assert historical.rule20_primary_hcp == 11
    twelve = _assess((4, 3, 3, 3), ("", "AKQ", "K", ""))
    assert twelve.hcp == 12 and _check(twelve, "natural_strength").state is CheckState.POSITIVE
    ten_rule20 = _assess((5, 5, 2, 1), ("AK", "QJ", "", ""))
    assert ten_rule20.hcp == 10 and ten_rule20.rule20 == 20
    assert _check(ten_rule20, "natural_strength").state is CheckState.POSITIVE
    failed = _assess((5, 3, 3, 2), ("AKQ", "Q", "", ""))
    assert failed.hcp == 11 and failed.rule20 == 19
    assert failed.classification is Classification.UNRESOLVED
    assert failed.supported_call is None


def test_minor_bindings_record_exact_subcases_and_remainder(bound):
    result = bound[2]
    for key in ("minor_length_policy", "minor_selection_precedence", "equal_minor_precedence"):
        b = result.binding(key)
        assert b.state is State.PARTIAL
        assert b.resolved_aspects and b.unresolved_aspects
        assert b.current_authority == "PHASE29S"
    equal = result.binding("equal_minor_precedence")
    assert dict(equal.parameters) == {
        "resolved_equal_lengths": "5,6", "preferred_call": "1D",
        "requires_opening_eligibility": True,
    }
    assert equal.historical_authority == "PHASE29M" and equal.supersedes_historical_scope
    historical = {p.policy_id: p for p in build_nisim_nily_opening_policy().propositions}
    assert historical["equal-minors-5-5"].status.value == "UNRESOLVED"
    assert _assess((1, 2, 5, 5), ("", "", "AKQ", "K")).supported_call == "1D"
    assert _assess((1, 0, 6, 6), ("", "", "AKQ", "K")).supported_call == "1D"
    ordinary = _assess((2, 3, 4, 4), ("", "AKQ", "K", ""))
    assert ordinary.hcp == 12 and ordinary.supported_call is None
    assert _check(ordinary, "natural_choice").state is CheckState.NEGATIVE
    assert "better minor" in equal.limitations.casefold()


def test_exact_five_five_major_binding_does_not_extrapolate(bound):
    b = bound[2].binding("five_five_major_precedence")
    assert b.state is State.BOUND
    assert dict(b.parameters) == {
        "spades_length": 5, "hearts_length": 5,
        "preferred_call": "1S", "requires_opening_eligibility": True,
    }
    witness = _assess((5, 5, 2, 1), ("AK", "QJ", "", ""))
    assert witness.supported_call == "1S"
    assert "6-6" in b.limitations


def test_positional_notrump_range_and_five_card_major(bound):
    result = bound[2]
    ranges = result.binding("one_notrump_range")
    assert ranges.state is State.BOUND
    assert dict(ranges.parameters) == {
        "position_1_min": 15, "position_1_max": 17,
        "position_2_min": 15, "position_2_max": 17,
        "position_3_min": 14, "position_3_max": 17,
        "position_4_min": 14, "position_4_max": 17,
    }
    assert "no vulnerability adjustment" in ranges.limitations
    major = result.binding("one_notrump_five_card_major_policy")
    assert major.state is State.BOUND
    assert dict(major.parameters) == {
        "five_card_major_allowed_in_canonical_balanced": True,
        "exactly_nine_major_cards_allowed": False,
    }
    first_fifteen = _assess((5, 3, 3, 2), ("AK", "AQ", "Q", ""))
    first_fourteen = _assess((5, 3, 3, 2), ("AK", "AQ", "J", ""))
    third_fourteen = _assess((5, 3, 3, 2), ("AK", "AQ", "J", ""), passes=2)
    nine_majors = _assess((5, 4, 2, 2), ("AK", "AQ", "Q", ""))
    assert _check(first_fifteen, "one_nt").state is CheckState.POSITIVE
    assert first_fifteen.supported_call == "1NT"
    assert _check(first_fourteen, "one_nt").state is CheckState.NEGATIVE
    assert _check(third_fourteen, "one_nt").state is CheckState.POSITIVE
    assert third_fourteen.supported_call == "1NT"
    assert _check(nine_majors, "one_nt").state is CheckState.NEGATIVE


def test_shape_suit_nt_and_strong_precedence_remain_partial(bound):
    result = bound[2]
    for key in ("one_notrump_shape_policy", "suit_vs_notrump_precedence",
                "strong_hand_precedence"):
        b = result.binding(key)
        assert b.state is State.PARTIAL and b.resolved_aspects and b.unresolved_aspects
    shape = result.binding("one_notrump_shape_policy")
    assert dict(shape.parameters) == {"canonical_balanced_subset_accepted": True}
    broader = _assess((3, 2, 6, 2), ("AK", "AQ", "Q", ""))
    assert _check(broader, "one_nt").state is CheckState.UNKNOWN
    precedence = result.binding("suit_vs_notrump_precedence")
    assert dict(precedence.parameters)["requires_strong_opening_negative"] is True
    strong = result.binding("strong_hand_precedence")
    assert dict(strong.parameters)["strong_2c_hcp_route_min"] == 23
    resolved = _assess((5, 3, 3, 2), ("AKQ", "AK", "A", "K"))
    assert resolved.hcp == 23 and resolved.supported_call == "2C"
    uncertain = _assess((5, 3, 3, 2), ("AJ", "AKQ", "A", "A"))
    assert uncertain.hcp == 22
    assert _check(uncertain, "strong_2c").state is CheckState.UNKNOWN
    assert uncertain.classification is Classification.OPENING_SUPPORTED
    assert uncertain.supported_call is None
    assert "SAYC" in strong.limitations and "22+" in strong.limitations


def test_counts_readiness_recommendation_and_capability(bound):
    result = bound[2]
    assert (result.bound_count, result.partial_count, result.unresolved_count) == (4, 6, 0)
    assert result.bound_count == sum(item.state is State.BOUND for item in result.bindings)
    assert result.partial_count == sum(item.state is State.PARTIAL for item in result.bindings)
    assert result.unresolved_count == sum(item.state is State.UNRESOLVED for item in result.bindings)
    assert result.all_required_bindings_resolved is all(
        item.state is State.BOUND for item in result.bindings)
    assert not result.all_required_bindings_resolved
    assert not result.ready_for_shadow_execution and not result.ready_for_production
    assert not result.production_bidding_changed and not result.production_adopted
    assert result.recommended_next_phase == "30M_NISIM_NILY_OPENING_BINDING_GAP_AUDIT"
    capability = capability_for_nisim_nily_opening_binding(result)
    assert isinstance(capability, NisimNilyOpeningBindingCapability)
    assert capability.base_contract_loaded and capability.partnership_identity_validated
    assert capability.binding_schema_ready and capability.historical_supersession_traced
    assert not capability.all_required_bindings_resolved and not capability.shadow_execution_ready
    assert not capability.production_bidding_changed and not capability.production_adopted
    assert json.loads(capability.to_json()) == capability.to_dict()
    with pytest.raises(FrozenInstanceError):
        capability.production_adopted = True
    all_bound = replace(result, bindings=tuple(
        replace(item, state=State.BOUND, unresolved_aspects=())
        for item in result.bindings))
    assert all_bound.all_required_bindings_resolved
    assert all_bound.recommended_next_phase == "30M_NISIM_NILY_OPENING_SHADOW_ENGINE"
    assert not all_bound.ready_for_shadow_execution  # Phase 30K has no executor.


def test_prior_contracts_routes_and_static_import_guard(bound):
    plan, contract, result = bound
    base_before = contract.to_json()
    boundary_before = audit_two_over_one_opening_execution_boundary(plan).to_json()
    before = tuple(route.route_id for route in create_standard_sayc_router().routes)
    source = Path(__file__).resolve().parents[1] / "bridge" / "nisim_nily_opening_contract_binding.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    after = tuple(route.route_id for route in create_standard_sayc_router().routes)
    assert len(before) == len(after) == 45 and before == after
    assert not any(marker in route_id.casefold() for route_id in after
                   for marker in ("nisim", "30l"))
    assert base_before == build_two_over_one_opening_contract().to_json()
    assert boundary_before == audit_two_over_one_opening_execution_boundary(plan).to_json()
    assert tuple(item.name for item in fields(SystemContext)) == ("system", "options")
    assert tuple(item.name for item in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system")
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not imports.intersection({
        "sayc", "sayc_route_configuration", "engine_router", "bidding_engine",
        "deal_simulator", "evaluation", "models", "auction",
        "opening_policy_consolidation_audit", "nisim_nily_opening_policy",
    })
    definitions = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not definitions.intersection({
        "Hand", "Auction", "Call", "RuleDecision", "BiddingEngineResult",
        "BiddingEngine", "EngineRoute", "evaluate", "recommend", "choose_opening",
        "opening_call",
    })
    assert "Draft" not in " ".join(p for b in result.bindings for p in b.provenance)
    assert all("PASS" not in str(dict(b.parameters)).upper()
               or b.binding_id == "one_level_strength_policy" for b in result.bindings)
