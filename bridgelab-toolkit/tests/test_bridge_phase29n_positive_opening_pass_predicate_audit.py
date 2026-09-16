"""Evidence-grounded positive conjunction; no speculative Pass policy."""

import ast
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from bridge.models import Hand
from bridge.nisim_nily_opening_policy import build_nisim_nily_opening_policy
from bridge.opening_pass_positive_predicate_audit import (
    PositivePassClassification as Category, PositivePassSafetyCheck, REQUIRED_CHECKS,
    SafetyState, all_safety_conditions_established,
    assess_positive_opening_pass_candidate, build_positive_pass_audit_report,
)


def assess(text):
    return assess_positive_opening_pass_candidate(Hand.parse(text))


def test_ordinary_weak_hand_has_positive_facts_but_missing_proof_is_unknown():
    a = assess("J987.962.94.J943")
    assert (a.hcp, a.longest_suit_length, a.rule20_score) == (2, 4, 10)
    assert a.numerical_screen_satisfied
    assert a.classification is Category.SOURCE_OR_POLICY_INSUFFICIENT
    assert "strong_playing_tricks_excluded" in a.unknown_checks
    assert not a.production_recommendation_created
    assert a.to_json() == assess("J987.962.94.J943").to_json()
    assert json.loads(a.to_json()) == a.to_dict()
    with pytest.raises(FrozenInstanceError):
        a.hcp = 0


def test_positive_conjunction_requires_all_explicit_evidence_not_a_complement():
    # Abstract truth-table test only. These hypothetical proofs are NOT supplied
    # to the hand assessor and do not establish a repository-supported Pass hand.
    checks = tuple(PositivePassSafetyCheck(key, SafetyState.ESTABLISHED,
                   "hypothetical proof for conjunction test", ("TEST_ONLY",)) for key in REQUIRED_CHECKS)
    assert all_safety_conditions_established(checks)
    assert not all_safety_conditions_established(())
    assert not all_safety_conditions_established(checks[:-1])
    assert not all_safety_conditions_established(checks + checks[:1])
    for i in range(len(checks)):
        for state in (SafetyState.UNKNOWN, SafetyState.EXCLUDED):
            changed = checks[:i] + (replace(checks[i], state=state),) + checks[i+1:]
            assert not all_safety_conditions_established(changed)
    assert not all_safety_conditions_established((replace(checks[0], provenance=()),) + checks[1:])
    with pytest.raises(TypeError):
        PositivePassSafetyCheck("x", True, "not a state", ())


@pytest.mark.parametrize("text,hcp,score", [
    ("KQJ98.A9742.8.73", 10, 20),
    ("KQJ987.K9742.8.7", 9, 20),
    ("A98765.A98765.8.-", 8, 20),
    ("KQJ98.A974.8.J73", 11, 20),
])
def test_rule20_prevents_false_pass_at_low_and_borderline_hcp(text, hcp, score):
    a = assess(text)
    assert (a.hcp, a.rule20_score) == (hcp, score)
    assert a.classification is Category.RULE20_POTENTIAL_OPENING
    assert "rule20_candidate_excluded" in a.blocking_checks
    assert not a.production_recommendation_created


@pytest.mark.parametrize("text,hcp", [
    ("KQJ9.A974.83.J73", 11), ("AJ4.Q96.KT8.Q952", 12), ("AJ4.K96.KT8.Q952", 13),
])
def test_11_failed_screen_12_and_13_are_not_safe_pass(text, hcp):
    a = assess(text)
    assert a.hcp == hcp
    assert a.classification is Category.OTHER_PROTECTED_UNRESOLVED
    assert "bounded_strength" in a.blocking_checks


@pytest.mark.parametrize("text", ["KQJ876.32.43.543", "KQJ9876.3.43.543"])
def test_six_and_seven_card_hands_are_protected(text):
    a = assess(text)
    assert a.classification is Category.PROTECTED_PREEMPT_DOMAIN
    assert "bounded_suit_lengths" in a.blocking_checks
    assert "weak_preempt_overlap_excluded" in a.blocking_checks


def test_equal_major_and_minor_protection_and_partnership_1s():
    a = assess("AJ543.AQJ63.74.2")
    assert a.classification is Category.KNOWN_OPENING_COVERAGE_BOUNDARY
    assert "equal_major_boundary_excluded" in a.blocking_checks
    assert build_nisim_nily_opening_policy().equal_five_card_majors_choice == "1S"
    minor = assess("83.7.QJ984.K9742")
    assert minor.classification is Category.PROTECTED_EQUAL_SUIT_DOMAIN
    assert "equal_minor_boundary_excluded" in minor.blocking_checks


def test_strong_hcp_and_uncomputed_playing_tricks_never_pass():
    a = assess("AKQ.AKQ.AKQ.9876")
    assert a.classification is Category.PROTECTED_STRONG_2C_DOMAIN
    assert "known_hcp_strong_excluded" in a.blocking_checks
    uncomputed = assess("AKQJT9876.A2.3.4")
    assert "strong_playing_tricks_excluded" in uncomputed.unknown_checks
    assert uncomputed.classification is not Category.SAFE_ORDINARY_PASS_CANDIDATE


def test_assessor_cannot_accept_abstain_no_route_or_claimed_proofs(monkeypatch):
    from bridge.bidding_rules import RuleDecision
    def forbidden(*args, **kwargs):
        raise AssertionError("audit must not recommend anything")
    monkeypatch.setattr(RuleDecision, "recommend", forbidden)
    hand = Hand.parse("J987.962.94.J943")
    result = assess_positive_opening_pass_candidate(hand)
    for keyword in ("production_result", "route", "abstention_code", "safety_override"):
        with pytest.raises(TypeError):
            assess_positive_opening_pass_candidate(hand, **{keyword: "ABSTAIN"})
    assert result.classification is not Category.SAFE_ORDINARY_PASS_CANDIDATE


def test_assessment_source_contains_no_router_or_rule_complement_logic():
    import bridge.opening_pass_positive_predicate_audit as module
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == "assess_positive_opening_pass_candidate")
    names = {n.id for n in ast.walk(function) if isinstance(n, ast.Name)}
    assert not names.intersection({"Call", "RuleDecision", "AuctionOutcome", "router", "batch"})
    assert not any(isinstance(n, ast.Attribute) and n.attr in ("recommend", "evaluate", "match")
                   for n in ast.walk(function))


@pytest.fixture(scope="module")
def sample():
    from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
    batch = run_full_auction_simulation(SimulationConfig(100, 1000))
    return batch, build_positive_pass_audit_report(batch)


def test_1000_deal_baseline_reconciliation_and_safe_count(sample):
    batch, report = sample
    assert report.total_deals == report.completed_simulations == 1000
    assert report.opening_depth0_abstain == 616
    assert dict(report.phase29m_counts) == {
        "RULE20_POTENTIAL_OPENING": 42, "KNOWN_OPENING_COVERAGE_BOUNDARY": 3,
        "PROTECTED_UNRESOLVED": 65, "SOURCE_OR_POLICY_INSUFFICIENT": 506,
        "POLICY_SUPPORTED_POTENTIAL_PASS": 0,
    }
    assert report.known_boundary_indexes == (57, 184, 613)
    assert report.phase29k_screen_count == 542
    assert sum(g.count for g in report.groups) == 616
    assert sum(n for _, _, n in report.transitions) == 616
    for old, count in report.phase29m_counts:
        assert sum(n for before, _, n in report.transitions if before == old) == count
    assert report.safe_candidate_count == 0  # No invented playing-trick proof.
    assert {g.classification.value: g.count for g in report.groups} == {
        "KNOWN_OPENING_COVERAGE_BOUNDARY": 3, "RULE20_POTENTIAL_OPENING": 46,
        "PROTECTED_STRONG_2C_DOMAIN": 0, "PROTECTED_PREEMPT_DOMAIN": 51,
        "PROTECTED_EQUAL_SUIT_DOMAIN": 11, "OTHER_PROTECTED_UNRESOLVED": 58,
        "SAFE_ORDINARY_PASS_CANDIDATE": 0, "SOURCE_OR_POLICY_INSUFFICIENT": 447,
    }
    assert report.numerical_screen_count == 447 and report.low_hcp_rule20_count == 4
    assert report.protected_unresolved_count == 120
    assert dict(report.numerical_screen_unknown_checks) == {
        "strong_playing_tricks_excluded": 447, "other_opening_exceptions_excluded": 447,
        "context_scope_established": 447,
    }
    assert report.simulation_error_count == report.reproduction_error_count == 0
    assert report.passed_out_compatible and not report.production_ready
    assert json.loads(report.to_json()) == report.to_dict()
    assert report.to_json() == build_positive_pass_audit_report(batch).to_json()
    for group in report.groups:
        assert len(group.representatives) <= 3
        assert sum(n for _, n in group.hcp_distribution) == group.count
        assert sum(n for _, n in group.shape_distribution) == group.count
        assert sum(n for _, n in group.longest_suit_distribution) == group.count
        assert sum(n for _, n in group.rule20_score_distribution) == group.count
        assert all(not hasattr(case, "deal") for case in group.representatives)


def test_production_rules_routes_and_previous_policy_unchanged():
    from bridge.sayc import sayc_opening_rules
    from bridge.sayc_route_configuration import create_standard_sayc_router
    from bridge.opening_pass_source_policy_audit import build_opening_pass_source_report
    before = tuple(rule.rule_id for rule in sayc_opening_rules())
    assess("J987.962.94.J943")
    assert tuple(rule.rule_id for rule in sayc_opening_rules()) == before
    assert len(before) == 14
    assert len(create_standard_sayc_router().routes) == 45
    assert build_opening_pass_source_report().implementation_readiness == "INCOMPLETE"
