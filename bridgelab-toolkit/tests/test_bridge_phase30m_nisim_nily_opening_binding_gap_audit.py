"""Phase 30M gap inventory and historical-evidence consistency tests."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

import bridge.nisim_nily_opening_binding_gap_audit as gap_module
from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.evaluation import ShapeClass, evaluate_hand
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_opening_binding_gap_audit import (
    OpeningBindingGapDisposition as D, OpeningBindingGap,
    NisimNilyOpeningBindingGapAudit, OpeningPartnershipDecisionRequest,
    audit_nisim_nily_opening_binding_gaps,
)
from bridge.nisim_nily_opening_contract_binding import (
    OpeningBindingState, bind_nisim_nily_opening_contract,
)
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.nisim_nily_six_minor_preempt_policy import SixMinorDecision
from bridge.opening_policy_consolidation_audit import (
    Classification, State, approved_playing_tricks, assess_opening_policy,
)
from bridge.opening_policy_six_minor_integration_audit import assess_opening_policy_with_six_minor
from bridge.partnership_profiles import resolve_partnership_profile
from bridge.profile_compiler import compile_profile_plan
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.two_over_one_opening_contract import build_two_over_one_opening_contract


PARTIAL = (
    "equal_minor_precedence", "minor_length_policy", "minor_selection_precedence",
    "one_notrump_shape_policy", "strong_hand_precedence", "suit_vs_notrump_precedence",
)


@pytest.fixture(scope="module")
def evidence():
    plan = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
    binding = bind_nisim_nily_opening_contract(plan)
    before = binding.to_json()
    audit = audit_nisim_nily_opening_binding_gaps(binding)
    assert binding.to_json() == before
    return binding, audit


def _make(shape, patterns):
    groups = []
    for length, honors in zip(shape, patterns):
        spots = "".join(rank for rank in "23456789T" if rank not in honors)
        groups.append(honors + spots[:length - len(honors)] or "-")
    return Hand.parse(".".join(groups))


def _assess(shape, patterns):
    return assess_opening_policy(
        _make(shape, patterns), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.NONE,
    )


def _check(assessment, family):
    return next(item for item in assessment.checks if item.family == family)


def test_exact_enum_schema_immutability_and_serialization(evidence):
    binding, audit = evidence
    assert tuple(item.value for item in D) == (
        "COVERED_BY_APPROVED_EVIDENCE", "PARTNERSHIP_DECISION_REQUIRED",
        "DEPENDENCY_REQUIRED", "OUTSIDE_CURRENT_SCOPE")
    assert isinstance(audit, NisimNilyOpeningBindingGapAudit)
    assert audit.profile_id == binding.profile_id
    assert audit.profile_version == binding.profile_version
    assert audit.base_system is binding.base_system
    assert audit.binding_version == binding.binding_version == "30L.1"
    assert audit.base_contract_version == binding.base_contract_version == "30K.1"
    assert audit.audit_version == "30M.1"
    assert json.loads(audit.to_json()) == audit.to_dict()
    assert audit.to_json() == audit_nisim_nily_opening_binding_gaps().to_json()
    assert all(json.loads(g.to_json()) == g.to_dict() for g in audit.gaps)
    assert all(json.loads(r.to_json()) == r.to_dict() for r in audit.decision_requests)
    with pytest.raises(FrozenInstanceError):
        audit.ready_for_production = True
    with pytest.raises(FrozenInstanceError):
        audit.gaps[0].disposition = D.COVERED_BY_APPROVED_EVIDENCE
    with pytest.raises(FrozenInstanceError):
        audit.decision_requests[0].question = "changed"


def test_exact_six_partial_ids_only_and_fail_closed(evidence):
    binding, audit = evidence
    assert audit.partial_binding_ids == PARTIAL
    assert tuple(sorted(x.binding_id for x in binding.bindings
                        if x.state is OpeningBindingState.PARTIAL)) == PARTIAL
    assert len(audit.gaps) == 31
    assert tuple(g.gap_id for g in audit.gaps) == tuple(sorted(g.gap_id for g in audit.gaps))
    assert {g.binding_id for g in audit.gaps} == set(PARTIAL)
    assert not {g.binding_id for g in audit.gaps}.intersection(
        x.binding_id for x in binding.bindings if x.state is OpeningBindingState.BOUND)
    with pytest.raises(ValueError, match="duplicate gap ID"):
        replace(audit, gaps=audit.gaps + (audit.gaps[0],))
    with pytest.raises(ValueError, match="exactly the six"):
        replace(audit, gaps=tuple(g for g in audit.gaps
                                  if g.binding_id != "minor_length_policy"))
    for altered in (
        tuple(x for x in binding.bindings if x.binding_id != "minor_length_policy"),
        binding.bindings + (replace(binding.binding("one_level_strength_policy"),
                                    state=OpeningBindingState.PARTIAL,
                                    unresolved_aspects=("artificial gap",)),),
    ):
        forged = replace(binding)
        object.__setattr__(forged, "bindings", altered)
        with pytest.raises(ValueError, match="partial binding IDs"):
            audit_nisim_nily_opening_binding_gaps(forged)
    forged = replace(binding)
    object.__setattr__(forged, "base_contract_version", "changed")
    with pytest.raises(ValueError, match="binding evidence changed"):
        audit_nisim_nily_opening_binding_gaps(forged)
    with pytest.raises(TypeError):
        audit_nisim_nily_opening_binding_gaps(None if False else "nisim-nily")


def test_disposition_validation(evidence):
    _, audit = evidence
    covered = audit.gap("equal_minors.5_5")
    assert isinstance(covered, OpeningBindingGap)
    with pytest.raises(ValueError, match="known rule"):
        replace(covered, known_rule=None)
    with pytest.raises(ValueError, match="user-decision flag"):
        replace(covered, requires_user_decision=True)
    with pytest.raises(ValueError, match="production"):
        replace(covered, production_adopted=True)


def test_unversioned_30l_evidence_change_fails_closed(evidence, monkeypatch):
    binding, _ = evidence
    changed = replace(binding, bindings=tuple(
        replace(item, limitations="Unreviewed change")
        if item.binding_id == "minor_length_policy" else item
        for item in binding.bindings))
    monkeypatch.setattr(gap_module, "bind_nisim_nily_opening_contract",
                        lambda plan: changed)
    with pytest.raises(ValueError, match="canonical binding evidence changed"):
        audit_nisim_nily_opening_binding_gaps()


def test_minor_length_and_selection_evidence(evidence):
    _, audit = evidence
    for key in ("minor_length.ordinary_club_minimum",
                "minor_length.ordinary_diamond_minimum", "minor_length.longer_minor",
                "minor_selection.unequal_minors", "minor_selection.major6_minor5"):
        assert audit.gap(key).disposition is D.PARTNERSHIP_DECISION_REQUIRED
    for key in ("minor_length.six_card_minor_rule20",
                "minor_selection.rule20_six_minor",
                "minor_selection.major_vs_minor_5_5",
                "minor_selection.major_vs_minor_5_6"):
        assert audit.gap(key).disposition is D.COVERED_BY_APPROVED_EVIDENCE
    for hand, call in (("7.K4.KQJT96.A742", "1D"),
                       ("7.K4.A742.KQJT96", "1C")):
        result = assess_opening_policy_with_six_minor(
            Hand.parse(hand), auction=Auction(Seat.NORTH),
            vulnerability=Vulnerability.NONE)
        assert result.six_minor.decision is SixMinorDecision.ONE_LEVEL
        assert result.supported_call == call
    assert _assess((1, 5, 2, 5), ("", "AKQ", "", "K")).supported_call == "1H"
    assert _assess((1, 5, 6, 1), ("", "AKQ", "K", "")).supported_call == "1H"
    boundary = _assess((6, 1, 5, 1), ("AKQ", "", "", ""))
    assert boundary.classification is Classification.UNRESOLVED
    assert _check(boundary, "natural_choice").state is State.UNKNOWN
    assert all("SAYC" not in (audit.gap(x).known_rule or "") for x in (
        "minor_length.ordinary_club_minimum", "minor_length.ordinary_diamond_minimum"))


def test_equal_minors_are_independent_and_later_evidence_wins(evidence):
    _, audit = evidence
    assert [audit.gap(f"equal_minors.{x}").disposition for x in
            ("3_3", "4_4", "5_5", "6_6")] == [
                D.PARTNERSHIP_DECISION_REQUIRED, D.PARTNERSHIP_DECISION_REQUIRED,
                D.COVERED_BY_APPROVED_EVIDENCE, D.COVERED_BY_APPROVED_EVIDENCE]
    assert "supersedes PHASE29M" in " ".join(audit.gap("equal_minors.5_5").provenance)
    assert _assess((1, 2, 5, 5), ("", "", "AKQ", "K")).supported_call == "1D"
    assert _assess((1, 0, 6, 6), ("", "", "AKQ", "K")).supported_call == "1D"
    assert _assess((2, 3, 4, 4), ("", "AKQ", "K", "")).supported_call is None


def test_notrump_shape_subdomains(evidence):
    _, audit = evidence
    for name, shape in (("4333", (4, 3, 3, 3)),
                        ("4432", (4, 4, 3, 2)),
                        ("5332", (5, 3, 3, 2))):
        assert audit.gap(f"one_nt_shape.canonical_{name}").disposition is D.COVERED_BY_APPROVED_EVIDENCE
        assert evaluate_hand(_make(shape, ("", "", "", ""))).shape_class is ShapeClass.BALANCED
    assert audit.gap("one_nt_shape.five_card_major").disposition is D.COVERED_BY_APPROVED_EVIDENCE
    assert audit.gap("one_nt_shape.exact_nine_major_cards").disposition is D.COVERED_BY_APPROVED_EVIDENCE
    assert audit.gap("one_nt_shape.six_card_minor").disposition is D.PARTNERSHIP_DECISION_REQUIRED
    assert audit.gap("one_nt_shape.other_broader_shapes").disposition is D.PARTNERSHIP_DECISION_REQUIRED
    five_major = _assess((5, 3, 3, 2), ("AK", "AQ", "Q", ""))
    nine_major = _assess((5, 4, 2, 2), ("AK", "AQ", "Q", ""))
    six_minor = _assess((3, 2, 6, 2), ("AK", "AQ", "Q", ""))
    assert _check(five_major, "one_nt").state is State.POSITIVE
    assert _check(nine_major, "one_nt").state is State.NEGATIVE
    assert _check(six_minor, "one_nt").state is State.UNKNOWN
    assert "Draft" not in " ".join(p for g in audit.gaps for p in g.provenance)


def test_suit_nt_and_strong_precise_boundaries(evidence):
    _, audit = evidence
    for key in ("suit_vs_nt.canonical_nt_vs_one_level",
                "suit_vs_nt.five_card_major_nt", "strong.23_plus",
                "strong.22_approved_strong_suit", "strong.route3_closed_suit",
                "strong.balanced_20_22_interaction"):
        assert audit.gap(key).disposition is D.COVERED_BY_APPROVED_EVIDENCE
    for key in ("suit_vs_nt.broader_nt_shapes", "suit_vs_nt.strong_opening_interaction",
                "strong.playing_trick_route"):
        assert audit.gap(key).disposition is D.DEPENDENCY_REQUIRED
        assert audit.gap(key).dependency
        assert not audit.gap(key).requires_user_decision
    for key in ("strong.22_unlisted_strong_suit", "strong.strong_minor_overlap"):
        assert audit.gap(key).disposition is D.PARTNERSHIP_DECISION_REQUIRED
    assert _assess((5, 3, 3, 2), ("AKQ", "AK", "A", "K")).supported_call == "2C"
    unknown = _assess((5, 3, 3, 2), ("AJ", "AKQ", "A", "A"))
    assert unknown.hcp == 22 and _check(unknown, "strong_2c").state is State.UNKNOWN
    assert unknown.supported_call is None
    assert approved_playing_tricks("32") is None
    assert approved_playing_tricks("AKQJ234") is None
    route3 = _assess((6, 3, 3, 1), ("AKQ", "AQ", "A", "Q"))
    assert route3.hcp == 21 and route3.supported_call == "2C"
    assert sum(route3.playing_trick_components) == 8.5
    assert "SAYC" not in " ".join(g.known_rule or "" for g in audit.gaps)


def test_counts_remaining_bindings_and_recommendation_are_derived(evidence):
    _, audit = evidence
    assert (audit.covered_count, audit.decision_required_count,
            audit.dependency_required_count, audit.outside_scope_count) == (17, 11, 3, 0)
    assert sum((audit.covered_count, audit.decision_required_count,
                audit.dependency_required_count, audit.outside_scope_count)) == len(audit.gaps)
    assert audit.bindings_fully_resolved_by_existing_evidence == ()
    assert audit.remaining_partial_bindings == PARTIAL
    assert audit.requires_user_decisions
    assert not audit.ready_for_shadow_execution and not audit.ready_for_production
    assert not audit.production_bidding_changed and not audit.production_adopted
    assert audit.recommended_next_phase == "30N_NISIM_NILY_OPENING_DECISION_PACKET"
    dependency_only = replace(audit, gaps=tuple(
        replace(g, disposition=D.COVERED_BY_APPROVED_EVIDENCE,
                known_rule="Hypothetically approved", missing_decision=None,
                requires_user_decision=False)
        if g.disposition is D.PARTNERSHIP_DECISION_REQUIRED else g for g in audit.gaps),
        decision_requests=())
    assert dependency_only.recommended_next_phase == "30N_NISIM_NILY_OPENING_DEPENDENCY_COMPLETION"
    all_covered = replace(dependency_only, gaps=tuple(
        replace(g, disposition=D.COVERED_BY_APPROVED_EVIDENCE,
                known_rule="Hypothetically approved", dependency=None)
        for g in dependency_only.gaps))
    assert all_covered.recommended_next_phase == "30N_NISIM_NILY_OPENING_BINDING_COMPLETION"
    assert all_covered.bindings_fully_resolved_by_existing_evidence == PARTIAL


def test_grouped_decision_requests_are_exhaustive_and_neutral(evidence):
    _, audit = evidence
    assert audit.decision_request_ids == (
        "MAJOR_MINOR_PRECEDENCE", "MINOR_STRUCTURE", "NOTRUMP_SHAPES",
        "STRONG_OPENING_PRECEDENCE")
    decision_gaps = {g.gap_id for g in audit.gaps if g.disposition is D.PARTNERSHIP_DECISION_REQUIRED}
    requested = [gap_id for request in audit.decision_requests for gap_id in request.gap_ids]
    assert len(requested) == len(set(requested)) and set(requested) == decision_gaps
    assert all(isinstance(r, OpeningPartnershipDecisionRequest) and r.provenance
               and r.already_known and r.must_not_infer and r.existing_behavior_untouched
               and r.question for r in audit.decision_requests)
    assert all(audit.gap(g).requires_user_decision for g in requested)
    with pytest.raises(ValueError, match="exactly once"):
        replace(audit, decision_requests=audit.decision_requests[:-1])


def test_no_execution_imports_or_prior_contract_changes(evidence):
    binding, audit = evidence
    before_30l = binding.to_json()
    before_30k = build_two_over_one_opening_contract().to_json()
    routes_before = tuple(route.route_id for route in create_standard_sayc_router().routes)
    source = Path(__file__).resolve().parents[1] / "bridge" / "nisim_nily_opening_binding_gap_audit.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not imports.intersection({
        "models", "auction", "evaluation", "opening_policy_consolidation_audit",
        "nisim_nily_six_minor_preempt_policy", "opening_policy_six_minor_integration_audit",
        "sayc", "sayc_route_configuration", "engine_router", "bidding_engine",
        "deal_simulator"})
    definitions = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not definitions.intersection({
        "Hand", "Auction", "Call", "RuleDecision", "BiddingEngineResult",
        "BiddingEngine", "EngineRoute", "evaluate", "recommend", "choose_opening",
        "opening_call", "BiddingRouter"})
    routes_after = tuple(route.route_id for route in create_standard_sayc_router().routes)
    assert len(routes_before) == len(routes_after) == 45 and routes_before == routes_after
    assert binding.to_json() == before_30l
    assert build_two_over_one_opening_contract().to_json() == before_30k
    assert tuple(x.name for x in fields(SystemContext)) == ("system", "options")
    assert tuple(x.name for x in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system")
    assert not audit.production_bidding_changed and not audit.production_adopted
