"""Phase 30O typed decisions and additive binding completion."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.evaluation import evaluate_hand
from bridge.models import Hand
from bridge.nisim_nily_opening_binding_completion import (
    NisimNilyCompletedOpeningBinding, complete_nisim_nily_opening_binding,
)
from bridge.nisim_nily_opening_binding_gap_audit import audit_nisim_nily_opening_binding_gaps
from bridge.nisim_nily_opening_contract_binding import (
    OpeningBindingState as State, bind_nisim_nily_opening_contract,
)
from bridge.nisim_nily_opening_decision_contract import (
    NisimNilyOpeningDecisionContract, StrongTwoClubRoute,
    build_nisim_nily_opening_decision_contract,
)
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.partnership_profiles import PartnershipProfile, resolve_partnership_profile
from bridge.profile_compiler import compile_profile_plan
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.two_over_one_opening_contract import build_two_over_one_opening_contract


@pytest.fixture(scope="module")
def completed():
    plan = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
    binding = bind_nisim_nily_opening_contract(plan)
    gap_audit = audit_nisim_nily_opening_binding_gaps(binding)
    decisions = build_nisim_nily_opening_decision_contract()
    originals = (binding.to_json(), gap_audit.to_json(), decisions.to_json())
    result = complete_nisim_nily_opening_binding(binding, decisions)
    assert originals == (binding.to_json(), gap_audit.to_json(), decisions.to_json())
    return binding, gap_audit, decisions, result


def _make(shape):
    groups = []
    for length in shape:
        groups.append("23456789T"[:length] or "-")
    return Hand.parse(".".join(groups))


def _nt_shape_permitted(decisions, hand):
    """Test-only interpretation of declarative suit-identity constraints."""
    s, h, d, c = evaluate_hand(hand).suit_lengths
    shape = tuple(sorted((s, h, d, c), reverse=True))
    if shape not in decisions.one_notrump_allowed_shapes:
        return False
    if shape in decisions.one_notrump_excluded_shapes:
        return False
    if decisions.one_notrump_exact_nine_major_cards_excluded and s + h == 9:
        return False
    if shape == (5, 4, 2, 2) and decisions.one_notrump_5422_both_majors_excluded:
        if tuple(sorted((s, h), reverse=True)) == (5, 4):
            return False
    if shape == (6, 3, 2, 2) and decisions.one_notrump_6322_six_suit_must_be_minor:
        if d != 6 and c != 6:
            return False
    return True


def test_decision_contract_identity_provenance_immutability_and_serialization(completed):
    _, _, decisions, result = completed
    assert isinstance(decisions, NisimNilyOpeningDecisionContract)
    assert decisions.profile_id == NISIM_NILY_PROFILE.profile_id
    assert decisions.profile_version == NISIM_NILY_PROFILE.version
    assert decisions.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert decisions.decision_version == "30N.1"
    assert (decisions.authority, decisions.phase, decisions.status) == (
        "NISIM_NILY_PARTNERSHIP_DECISION", "30N", "APPROVED")
    assert decisions.approval_provenance and not decisions.production_adopted
    assert "SAYC" not in decisions.approval_provenance
    assert json.loads(decisions.to_json()) == decisions.to_dict()
    assert decisions.to_json() == build_nisim_nily_opening_decision_contract().to_json()
    with pytest.raises(FrozenInstanceError):
        decisions.minor_club_minimum = 4
    with pytest.raises(ValueError, match="minor or major"):
        replace(decisions, equal_minor_3_3_call="1D")
    with pytest.raises(ValueError, match="canonical Nisim"):
        replace(decisions, profile_id="partnership-b")
    with pytest.raises(ValueError, match="notrump shape"):
        replace(decisions, one_notrump_6322_six_suit_must_be_minor=False)
    with pytest.raises(ValueError, match="strong or precedence"):
        replace(decisions, strong_two_club_vs_strong_minor_precedence="2D")
    assert isinstance(result, NisimNilyCompletedOpeningBinding)


def test_minor_and_major_decisions_are_exact(completed):
    _, _, decisions, result = completed
    assert (decisions.minor_club_minimum, decisions.minor_diamond_minimum) == (3, 3)
    assert decisions.unequal_minor_rule == "longer_minor"
    assert (decisions.equal_minor_3_3_call, decisions.equal_minor_4_4_call,
            decisions.equal_minor_5_5_call, decisions.equal_minor_6_6_call) == (
            "1C", "1D", "1D", "1D")
    assert decisions.six_major_five_minor_call_family == "major"
    assert decisions.exact_six_minor_rule20_preserved
    assert dict(result.binding("minor_length_policy").parameters)["club_minimum"] == 3
    assert dict(result.binding("minor_length_policy").parameters)["diamond_minimum"] == 3
    assert dict(result.binding("minor_selection_precedence").parameters)["unequal_minors"] == "longer_minor"
    assert dict(result.binding("minor_selection_precedence").parameters)["six_major_five_minor"] == "major"
    equal = dict(result.binding("equal_minor_precedence").parameters)
    assert tuple(equal[f"equal_{x}"] for x in ("3_3", "4_4", "5_5", "6_6")) == (
        "1C", "1D", "1D", "1D")
    # Hand shapes are witnesses for the scope of decision metadata, not calls
    # generated by the Phase 30O module.
    for shape in ((4, 3, 3, 3), (3, 2, 4, 4), (3, 2, 5, 3), (6, 1, 5, 1)):
        assert evaluate_hand(_make(shape)).suit_lengths == shape
    assert "precede ordinary minor choice" in result.binding("minor_selection_precedence").limitations
    assert all("SAYC" not in x for x in result.binding("minor_length_policy").provenance
               if "Phase 30N" in x)


def test_notrump_shape_set_and_suit_identity(completed):
    binding, _, decisions, result = completed
    assert decisions.one_notrump_allowed_shapes == (
        (4, 3, 3, 3), (4, 4, 3, 2), (5, 3, 3, 2),
        (5, 4, 2, 2), (6, 3, 2, 2))
    assert decisions.one_notrump_excluded_shapes == ((5, 4, 3, 1), (6, 3, 3, 1))
    assert decisions.one_notrump_five_card_major_allowed
    assert decisions.one_notrump_5422_both_majors_excluded
    assert decisions.one_notrump_6322_six_suit_must_be_minor
    assert decisions.one_notrump_exact_nine_major_cards_excluded
    for shape in ((4, 3, 3, 3), (4, 4, 3, 2), (5, 3, 3, 2),
                  (5, 2, 4, 2), (3, 2, 6, 2), (2, 3, 2, 6)):
        assert _nt_shape_permitted(decisions, _make(shape)), shape
    for shape in ((5, 4, 2, 2), (4, 5, 2, 2), (6, 3, 2, 2),
                  (5, 4, 3, 1), (3, 1, 6, 3), (5, 2, 5, 1)):
        assert not _nt_shape_permitted(decisions, _make(shape)), shape
    assert dict(result.binding("one_notrump_shape_policy").parameters)[
        "shape_6322_requires_six_card_minor"] is True
    assert dict(binding.binding("one_notrump_range").parameters) == dict(
        result.binding("one_notrump_range").parameters)
    assert "vulnerability" not in " ".join(
        key for key, _ in result.binding("one_notrump_shape_policy").parameters)


def test_strong_routes_and_precedence_keep_unknown_components(completed):
    _, _, decisions, result = completed
    routes = decisions.strong_two_club_routes
    assert all(isinstance(x, StrongTwoClubRoute) for x in routes)
    assert tuple(x.route_id for x in routes) == (
        "23_plus_hcp", "exact_22_strong_suit", "route3_closed_suit")
    assert (routes[0].hcp_min, routes[0].hcp_max) == (23, None)
    assert (routes[1].hcp_min, routes[1].hcp_max, routes[1].suit_minimum) == (22, 22, 5)
    assert routes[1].qualifying_honor_patterns == ("AK", "AQ", "KQ", "KJT")
    assert (routes[2].hcp_min, routes[2].hcp_max, routes[2].suit_minimum,
            routes[2].qualifying_honor_patterns,
            routes[2].maximum_other_suit_length,
            routes[2].minimum_playing_tricks) == (17, 21, 6, ("AKQ",), 3, 8.5)
    assert routes[2].requires_approved_component_values
    assert decisions.strong_two_club_vs_strong_minor_precedence == "2C"
    strong = result.binding("strong_hand_precedence")
    assert dict(strong.parameters)["strong_2c_over_strong_minor"] == "2C"
    assert dict(strong.parameters)["route3_min_playing_tricks"] == "8.5"
    assert "typed playing-trick component table" in " ".join(result.remaining_dependencies)
    assert result.remaining_dependency_gap_ids == ("strong.playing_trick_route",)
    assert "SAYC" in strong.limitations or "no new values" in strong.limitations


def test_completion_states_counts_and_readiness_are_derived(completed):
    binding, gap_audit, decisions, result = completed
    assert result.to_json() == complete_nisim_nily_opening_binding().to_json()
    assert json.loads(result.to_json()) == result.to_dict()
    assert (result.profile_id, result.profile_version, result.base_system) == (
        binding.profile_id, binding.profile_version, binding.base_system)
    assert (result.base_contract_version, result.phase30l_binding_version,
            result.decision_contract_version, result.completion_version) == (
            "30K.1", "30L.1", "30N.1", "30O.1")
    assert tuple(x.binding_id for x in result.bindings) == binding.base_required_bindings
    assert all(result.binding(x.binding_id).state is State.BOUND for x in binding.bindings)
    assert (result.bound_count, result.partial_count, result.unresolved_count) == (10, 0, 0)
    assert result.all_required_bindings_resolved and result.declarative_contract_complete
    assert result.remaining_decision_gap_ids == ()
    assert not result.ready_for_shadow_execution and not result.ready_for_production
    assert not result.production_bidding_changed and not result.production_adopted
    assert result.recommended_next_phase == (
        "30P_NISIM_NILY_OPENING_EXECUTION_DEPENDENCY_COMPLETION")
    assert binding.partial_count == 6 and gap_audit.decision_required_count == 11
    assert decisions.production_adopted is False
    with pytest.raises(FrozenInstanceError):
        result.bound_count = 9
    with pytest.raises(ValueError, match="exactly once"):
        replace(result, bindings=result.bindings + (result.bindings[0],))
    hypothetical = replace(result, remaining_decision_gap_ids=("new_choice",))
    assert hypothetical.recommended_next_phase == "30P_NISIM_NILY_OPENING_DECISION_COMPLETION"
    executable = replace(result, remaining_dependency_gap_ids=(), remaining_dependencies=(),
                         base_ready_for_execution=True)
    assert executable.ready_for_shadow_execution
    assert executable.recommended_next_phase == "30P_NISIM_NILY_OPENING_SHADOW_ENGINE"
    assert not executable.ready_for_production


def test_historical_binding_and_gap_audit_are_unchanged(completed):
    binding, gap_audit, _, result = completed
    assert binding.to_json() == bind_nisim_nily_opening_contract(
        compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))).to_json()
    assert gap_audit.to_json() == audit_nisim_nily_opening_binding_gaps(binding).to_json()
    assert build_two_over_one_opening_contract().contract_version == result.base_contract_version
    for original in binding.bindings:
        updated = result.binding(original.binding_id)
        if original.state is State.BOUND:
            assert updated is original
        else:
            assert updated is not original and updated.current_authority == "PHASE30N"
            assert updated.provenance != original.provenance
            assert original.state is State.PARTIAL


def test_partnership_b_same_base_system_cannot_receive_decisions(completed):
    _, _, decisions, _ = completed
    other = PartnershipProfile("partnership-b", "30O.test", SystemProfile.TWO_OVER_ONE_GF, ())
    other_plan = compile_profile_plan(resolve_partnership_profile(other))
    with pytest.raises(ValueError, match="Nisim"):
        bind_nisim_nily_opening_contract(other_plan)
    with pytest.raises(ValueError, match="canonical Nisim"):
        replace(decisions, profile_id="partnership-b")
    with pytest.raises(TypeError):
        complete_nisim_nily_opening_binding("partnership-b", decisions)


def test_static_import_and_production_guards(completed):
    _, _, _, result = completed
    root = Path(__file__).resolve().parents[1] / "bridge"
    forbidden = {"models", "auction", "evaluation", "sayc", "sayc_route_configuration",
                 "engine_router", "bidding_engine", "deal_simulator",
                 "opening_policy_consolidation_audit"}
    definitions = set()
    for name in ("nisim_nily_opening_decision_contract.py",
                 "nisim_nily_opening_binding_completion.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        assert not imports.intersection(forbidden)
        definitions.update(node.name for node in ast.walk(tree)
                           if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)))
    assert not definitions.intersection({"Hand", "Auction", "Call", "RuleDecision",
                                         "BiddingEngineResult", "BiddingEngine", "EngineRoute",
                                         "evaluate", "recommend", "choose_opening", "opening_call"})
    route_ids_before = tuple(x.route_id for x in create_standard_sayc_router().routes)
    route_ids_after = tuple(x.route_id for x in create_standard_sayc_router().routes)
    assert len(route_ids_before) == len(route_ids_after) == 45
    assert route_ids_before == route_ids_after
    assert tuple(x.name for x in fields(SystemContext)) == ("system", "options")
    assert tuple(x.name for x in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system")
    assert not result.production_bidding_changed and not result.production_adopted
