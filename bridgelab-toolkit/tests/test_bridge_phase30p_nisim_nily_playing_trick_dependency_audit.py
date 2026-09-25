"""Phase 30P exact component-class coverage and legal-hand witnesses."""

import ast
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from bridge.evaluation import evaluate_hand
from bridge.models import Hand
from bridge.nisim_nily_opening_binding_completion import complete_nisim_nily_opening_binding
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.nisim_nily_playing_trick_dependency_audit import (
    PlayingTrickComponentRole as Role, PlayingTrickComponentStatus as Status,
    PlayingTrickDependencyAudit, audit_nisim_nily_playing_trick_dependency,
    observe_route3_hand,
)
from bridge.opening_policy_consolidation_audit import approved_playing_tricks, honor_pattern
from bridge.partnership_profiles import PartnershipProfile, resolve_partnership_profile
from bridge.profile_compiler import compile_profile_plan
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile


@pytest.fixture(scope="module")
def audit():
    return audit_nisim_nily_playing_trick_dependency()


def _make(shape, patterns):
    groups = []
    for length, honors in zip(shape, patterns):
        spots = "".join(rank for rank in "23456789T" if rank not in honors)
        groups.append(honors + spots[:length - len(honors)] or "-")
    return Hand.parse(".".join(groups))


def test_identity_contract_immutable_deterministic_serialization(audit):
    assert isinstance(audit, PlayingTrickDependencyAudit)
    assert (audit.profile_id, audit.profile_version, audit.base_system) == (
        NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
        SystemProfile.TWO_OVER_ONE_GF)
    assert (audit.baseline_phase, audit.completion_version, audit.audit_version) == (
        "30O", "30O.1", "30P.1")
    assert (audit.route3_min_hcp, audit.route3_max_hcp,
            audit.route3_min_primary_length, audit.route3_primary_pattern,
            audit.route3_max_side_length, audit.route3_threshold) == (
            17, 21, 6, "AKQ", 3, 8.5)
    assert audit.to_json() == audit_nisim_nily_playing_trick_dependency().to_json()
    assert json.loads(audit.to_json()) == audit.to_dict()
    with pytest.raises(FrozenInstanceError):
        audit.dependency_complete = True
    with pytest.raises(ValueError, match="canonical Nisim"):
        replace(audit, profile_id="partnership-b")
    with pytest.raises(ValueError, match="Route-3"):
        replace(audit, route3_threshold=9.0)
    with pytest.raises(ValueError, match="production"):
        replace(audit, production_changed=True)


def test_exact_approved_29s_table_and_length_semantics(audit):
    assert tuple((x.honor_pattern, x.length_scope, x.value) for x in audit.approved_table) == (
        ("A", "1-3", 1.0), ("K", "1-3", 0.0), ("Q", "1-3", 0.0),
        ("AK", "1-3", 2.0), ("AQ", "1-3", 1.5), ("AJ", "1-3", 1.0),
        ("AJT", "1-3", 1.5), ("KQ", "1-3", 1.0),
        ("KQT", "1-3", 1.5), ("KQJ", "1-3", 2.0),
        ("QJ", "1-3", 0.25), ("QJT", "1-3", 1.0),
        ("AKQ", "1-3", 3.0), ("AKQ", "exactly 6", 6.0))
    for holding, expected in (("A", 1), ("K", 0), ("Q", 0),
                              ("AK", 2), ("AQ", 1.5), ("AJ", 1),
                              ("AJT", 1.5), ("KQ", 1), ("KQT", 1.5),
                              ("KQJ", 2), ("QJ", .25), ("QJT", 1),
                              ("AKQ", 3), ("AKQ234", 6),
                              ("K2", 0), ("K23", 0)):
        assert approved_playing_tricks(holding) == expected
    for holding in ("", "2", "23", "234", "J", "T", "AT", "KT", "QT",
                    "KJ", "AKQ2345", "AKQ23456", "AKQJ23"):
        assert approved_playing_tricks(holding) is None
    assert honor_pattern("AKQ234") == honor_pattern("AKQ2345") == "AKQ"
    assert not any(x.honor_pattern == "AKQ" and x.length_scope == "7+"
                   for x in audit.approved_table)


def test_static_exhaustive_inventory_counts_and_primary_lengths(audit):
    assert "Exhaustive legal honor-pattern/suit-length" in audit.population_basis
    assert (audit.structural_population, audit.fully_evaluable_count,
            audit.blocked_count) == (130062, 1620, 128442)
    assert audit.structural_population == audit.fully_evaluable_count + audit.blocked_count
    assert len(audit.component_classes) == 73
    assert len(audit.dependency_classes) == 48
    assert len(audit.real_hand_witnesses) == 71
    assert [(x.length, x.occurrence_count, x.approved_count, x.missing_count)
            for x in audit.primary_length_summaries] == [
                (6, 61662, 15777, 45885), (7, 43266, 0, 43266),
                (8, 19236, 0, 19236), (9, 5160, 0, 5160),
                (10, 708, 0, 708), (11, 30, 0, 30)]
    assert sum(x.occurrence_count for x in audit.primary_length_summaries) == audit.structural_population
    assert sum(x.occurrence_count for x in audit.side_length_summaries) == 3 * audit.structural_population
    for x in audit.primary_length_summaries + audit.side_length_summaries:
        assert x.occurrence_count == x.approved_count + x.missing_count
        assert x.distinct_honor_patterns and x.representative_holdings
    assert [x.length for x in audit.side_length_summaries] == [0, 1, 2, 3]
    assert [(x.occurrence_count, x.approved_count, x.missing_count)
            for x in audit.side_length_summaries] == [
                (11880, 0, 11880), (82038, 44538, 37500),
                (160608, 81342, 79266), (135660, 72444, 63216)]


def test_missing_class_ids_and_status_are_exact(audit):
    assert tuple(x.dependency_id for x in audit.component_classes) == tuple(
        sorted(x.dependency_id for x in audit.component_classes))
    assert audit.missing_dependency_ids == tuple(x.dependency_id
                                                 for x in audit.dependency_classes)
    assert len(audit.missing_dependency_ids) == len(set(audit.missing_dependency_ids)) == 48
    assert audit.missing_dependency_ids == (
        "primary.AKQ.length10", "primary.AKQ.length11", "primary.AKQ.length7",
        "primary.AKQ.length8", "primary.AKQ.length9",
        "primary.AKQJ.length10", "primary.AKQJ.length11", "primary.AKQJ.length6",
        "primary.AKQJ.length7", "primary.AKQJ.length8", "primary.AKQJ.length9",
        "primary.AKQJT.length10", "primary.AKQJT.length11", "primary.AKQJT.length6",
        "primary.AKQJT.length7", "primary.AKQJT.length8", "primary.AKQJT.length9",
        "primary.AKQT.length10", "primary.AKQT.length11", "primary.AKQT.length6",
        "primary.AKQT.length7", "primary.AKQT.length8", "primary.AKQT.length9",
        "side.AKJ.length3", "side.AKT.length3", "side.AQJ.length3",
        "side.AQT.length3", "side.AT.length2", "side.AT.length3",
        "side.J.length1", "side.J.length2", "side.J.length3",
        "side.JT.length2", "side.JT.length3", "side.KJ.length2",
        "side.KJ.length3", "side.KJT.length3", "side.KT.length2",
        "side.KT.length3", "side.QT.length2", "side.QT.length3",
        "side.T.length1", "side.T.length2", "side.T.length3",
        "side.empty.length0", "side.spot_only.length1",
        "side.spot_only.length2", "side.spot_only.length3")
    by_id = {x.dependency_id: x for x in audit.component_classes}
    assert by_id["primary.AKQ.length6"].approved_value == 6
    assert by_id["primary.AKQ.length6"].status is Status.APPROVED_VALUE
    assert by_id["primary.AKQ.length7"].approved_value is None
    assert by_id["side.K.length3"].approved_value == 0
    assert by_id["side.empty.length0"].approved_value is None
    assert by_id["side.spot_only.length1"].approved_value is None
    assert all(x.status is Status.MISSING_VALUE and x.approved_value is None
               and x.requires_new_authority for x in audit.dependency_classes)
    assert all(x.occurrence_count > 0 and x.representative_holdings
               for x in audit.dependency_classes)


def test_real_hands_cover_each_component_class_and_sum_known_only(audit):
    seen = set()
    fully = blocked = 0
    for case in audit.real_hand_witnesses:
        hand = Hand.parse(case.hand)
        facts = evaluate_hand(hand)
        assert len(hand.cards) == sum(case.suit_lengths) == 13
        assert facts.hcp == case.hcp and facts.suit_lengths == case.suit_lengths
        assert 17 <= case.hcp <= 21
        assert case.route3_structural_gate_met
        primary = next(x for x in case.component_observations
                       if x.role is Role.PRIMARY_CLOSED_SUIT)
        assert primary.suit == case.primary_suit and primary.length >= 6
        assert set("AKQ") <= set(primary.holding)
        assert all(x.length <= 3 for x in case.component_observations
                   if x.role is Role.SIDE_SUIT)
        assert case.known_component_total == sum(
            x.approved_value for x in case.component_observations
            if x.approved_value is not None)
        assert case.unknown_component_count == sum(
            x.approved_value is None for x in case.component_observations)
        assert case.route3_fully_evaluable is (case.unknown_component_count == 0)
        if case.route3_fully_evaluable:
            fully += 1
            assert case.threshold_met_if_evaluable is (case.known_component_total >= 8.5)
        else:
            blocked += 1
            assert case.threshold_met_if_evaluable is None
        for obs in case.component_observations:
            prefix = "primary" if obs.role is Role.PRIMARY_CLOSED_SUIT else "side"
            name = obs.honor_pattern or ("empty" if obs.length == 0 else "spot_only")
            seen.add(f"{prefix}.{name}.length{obs.length}")
            assert obs.approved_value == approved_playing_tricks(obs.holding)
    assert seen == {x.dependency_id for x in audit.component_classes}
    assert fully > 0 and blocked > 0


def test_ineligible_hands_excluded_from_route3_dependency_population():
    below = _make((6, 3, 3, 1), ("AKQ", "", "", ""))
    above = _make((6, 3, 3, 1), ("AKQ", "AKQ", "AK", ""))
    side_four = _make((6, 4, 2, 1), ("AKQ", "AK", "A", ""))
    no_akq = _make((6, 3, 3, 1), ("AKJ", "AKQ", "", ""))
    assert evaluate_hand(below).hcp < 17
    assert evaluate_hand(above).hcp > 21
    assert evaluate_hand(side_four).hcp in range(17, 22)
    assert evaluate_hand(no_akq).hcp in range(17, 22)
    assert all(observe_route3_hand(x) is None for x in
               (below, above, side_four, no_akq))
    with pytest.raises(TypeError):
        observe_route3_hand("AKQ234.AKQ.AK.2")


def test_decision_requests_are_complete_without_prefilled_values(audit):
    assert tuple(x.dependency_id for x in audit.decision_requests) == audit.missing_dependency_ids
    assert all(x.requested_value is None and x.why_needed and x.representative_holdings
               for x in audit.decision_requests)
    assert not audit.dependency_complete and not audit.shadow_execution_ready
    assert audit.recommended_next_phase == (
        "30Q_NISIM_NILY_PLAYING_TRICK_COMPONENT_DECISIONS")
    with pytest.raises(ValueError, match="prefill"):
        replace(audit.decision_requests[0], requested_value=0)
    with pytest.raises(ValueError, match="exactly"):
        replace(audit, decision_requests=audit.decision_requests[:-1])


def test_partnership_scope_historical_preservation_and_router_guard(audit):
    completion = complete_nisim_nily_opening_binding()
    assert completion.remaining_dependency_gap_ids == ("strong.playing_trick_route",)
    assert not completion.ready_for_shadow_execution
    other = PartnershipProfile("partnership-b", "30P.test", SystemProfile.TWO_OVER_ONE_GF, ())
    other_plan = compile_profile_plan(resolve_partnership_profile(other))
    assert other_plan.profile_id != audit.profile_id
    with pytest.raises(ValueError, match="canonical Nisim"):
        replace(audit, profile_id=other_plan.profile_id)
    source = Path(__file__).resolve().parents[1] / "bridge" / "nisim_nily_playing_trick_dependency_audit.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not imports.intersection({"sayc", "sayc_route_configuration", "bidding_engine",
                                     "engine_router", "deal_simulator"})
    definitions = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not definitions.intersection({"Call", "RuleDecision", "BiddingEngineResult",
                                         "BiddingEngine", "EngineRoute", "choose_opening",
                                         "opening_call", "recommend"})
    routes_before = tuple(x.route_id for x in create_standard_sayc_router().routes)
    routes_after = tuple(x.route_id for x in create_standard_sayc_router().routes)
    assert len(routes_before) == len(routes_after) == 45
    assert routes_before == routes_after
    assert not audit.production_changed
