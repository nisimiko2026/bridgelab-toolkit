"""Tri-state evidence tests; no new bridge-policy assumptions."""
import ast
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_opening_policy import build_nisim_nily_opening_policy
from bridge.opening_pass_safety_evidence_audit import (
    SafetyEvidenceStatus as Status, SafetyEvidenceDimension as Dimension,
    SafetyEvidenceAssessment, ResolutionType, overall_safety,
    assess_pass_safety_evidence, build_pass_safety_audit_report,
    opening_exception_registry, safety_gap_matrix,
)


def assess(text, calls=()):
    return assess_pass_safety_evidence(Hand.parse(text), auction=Auction(Seat.NORTH, calls),
            vulnerability=Vulnerability.NONE, system=SystemContext("SAYC"))


def test_tristate_all_dimensions_and_unknowns():
    assert {s.value for s in Status} == {"SAFE", "UNSAFE", "UNKNOWN"}
    hypothetical = tuple(SafetyEvidenceAssessment(d, Status.SAFE, "TEST_ONLY", ("truth-table",), "hypothetical proof") for d in Dimension)
    assert overall_safety(hypothetical) is Status.SAFE
    assert overall_safety(()) is Status.UNKNOWN
    assert overall_safety(hypothetical[:-1]) is Status.UNKNOWN
    assert overall_safety(hypothetical + hypothetical[:1]) is Status.UNKNOWN
    for i in range(len(hypothetical)):
        altered = hypothetical[:i] + (replace(hypothetical[i], status=Status.UNKNOWN),) + hypothetical[i+1:]
        assert overall_safety(altered) is Status.UNKNOWN
        assert overall_safety(altered + (replace(hypothetical[i], status=Status.UNSAFE),)) is Status.UNSAFE
    with pytest.raises(TypeError):
        SafetyEvidenceAssessment(Dimension.CONTEXT_SAFETY, False, "test", (), "")


def test_actual_context_facts_do_not_imply_context_policy():
    first = assess("J987.962.94.J943")
    third = assess("J987.962.94.J943", ("P", "P"))
    assert first.opening_position == 1 and third.opening_position == 3
    assert first.acting_seat == "N" and third.acting_seat == "S"
    assert not first.actor_previously_passed and not third.actor_previously_passed
    assert first.relative_vulnerability == "equal-nonvulnerable"
    assert first.overall is third.overall is Status.UNKNOWN
    assert all(d.status is Status.UNKNOWN for d in first.dimensions)
    assert first.phase29n.numerical_screen_satisfied
    assert "ordinary_preempt_excluded" in first.objectively_excluded_domains
    assert first.to_json() == assess("J987.962.94.J943").to_json()
    with pytest.raises(FrozenInstanceError):
        first.system = "other"


@pytest.mark.parametrize("text", ["AJ4.Q96.KT8.Q952", "KQJ876.32.43.543", "AKQ.AKQ.AKQ.9876"])
def test_positive_existing_openings_are_unsafe_for_pass(text):
    a = assess(text)
    assert a.overall is Status.UNSAFE
    assert any(h.startswith("existing-opening:") for h in a.positive_hazards)


def test_rule20_does_not_invent_low_hcp_opening():
    assert assess("KQJ98.A974.8.J73").overall is Status.UNSAFE
    low = assess("KQJ98.A9742.8.73")
    assert low.phase29n.rule20_qualified
    assert low.overall is Status.UNKNOWN
    assert not low.positive_hazards


def test_equal_suits_playing_tricks_and_preempt_gaps_protected():
    assert build_nisim_nily_opening_policy().equal_five_card_majors_choice == "1S"
    assert assess("AJ543.AQJ63.74.2").overall is Status.UNSAFE
    for text in ("83.7.QJ984.K9742", "4.T6.QT98732.K98", "KQJ876.QJ9876.4.-"):
        assert assess(text).overall is Status.UNKNOWN
    a = assess("AKQJT9876.A2.3.4")
    assert next(d for d in a.dimensions if d.dimension is Dimension.PLAYING_TRICK_SAFETY).status is Status.UNKNOWN


def test_no_status_or_route_override_no_new_pass_rule():
    import bridge.opening_pass_safety_evidence_audit as module
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    assert not any(isinstance(n, ast.Attribute) and n.attr == "recommend" for n in ast.walk(tree))
    assert not any(isinstance(n, ast.Name) and n.id == "RuleDecision" for n in ast.walk(tree))
    for key in ("production_status", "no_route", "unknown", "abstain"):
        with pytest.raises(TypeError):
            assess_pass_safety_evidence(Hand.parse("J987.962.94.J943"), auction=Auction(Seat.NORTH),
                vulnerability=Vulnerability.NONE, system=SystemContext("SAYC"), **{key: True})
    with pytest.raises(ValueError):
        assess("J987.962.94.J943", ("P", "P", "P", "P"))


def test_exception_registry_and_gap_taxonomy():
    registry = opening_exception_registry()
    assert registry == opening_exception_registry()
    assert len({r.exception_id for r in registry}) == len(registry)
    playing = next(r for r in registry if r.exception_id == "strong-playing")
    assert not playing.positive_predicate_available and not playing.exclusion_predicate_available
    assert not playing.production_implemented
    gaps = safety_gap_matrix()
    assert gaps == safety_gap_matrix()
    assert all(g.required_resolution is not ResolutionType.ENGINE_HELPER_REQUIRED for g in gaps)
    assert next(g for g in gaps if g.gap_id == "playing-bound").gap_kind == "SOURCE_GAP"
    assert next(g for g in gaps if g.gap_id == "approved-opening-coverage").gap_kind == "COVERAGE_GAP"


@pytest.fixture(scope="module")
def sample():
    from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
    batch = run_full_auction_simulation(SimulationConfig(100, 1000))
    return batch, build_pass_safety_audit_report(batch)


def test_447_decomposition_and_intersections(sample):
    _, r = sample
    assert r.depth0_abstain == 616 and len(r.insufficient_cases) == 447
    assert len({c.deal_index for c in r.insufficient_cases}) == 447
    assert dict(r.subset_overall_counts) == {"SAFE": 0, "UNSAFE": 0, "UNKNOWN": 447}
    for dimension in Dimension:
        assert {s:n for d,s,n in r.dimension_counts if d == dimension.value} == {"SAFE": 0, "UNSAFE": 0, "UNKNOWN": 447}
    assert sum(n for _,n in r.unknown_intersections) == 447
    assert next(n for label,n in r.unknown_intersections if label.count("+") == 2) == 447
    assert all(c.opening_position == 1 and c.acting_seat == c.dealer and not c.actor_previously_passed for c in r.insufficient_cases)
    assert all(c.system == "SAYC" and c.system_options == () for c in r.insufficient_cases)
    assert all(c.phase29n.numerical_screen_satisfied for c in r.insufficient_cases)
    assert all(not hasattr(c, "deal") for c in r.insufficient_cases)


def test_reconcile_42_to_46_and_65_to_120(sample):
    _, r = sample
    old, new = dict(r.phase29m_counts), dict(r.phase29n_counts)
    moves = {(a,b):n for a,b,n in r.phase29m_to_n}
    assert old["RULE20_POTENTIAL_OPENING"] == 42
    assert new["RULE20_POTENTIAL_OPENING"] == 42 + 3 + 1 == 46
    assert moves[("PROTECTED_UNRESOLVED", "RULE20_POTENTIAL_OPENING")] == 3
    assert moves[("SOURCE_OR_POLICY_INSUFFICIENT", "RULE20_POTENTIAL_OPENING")] == 1
    protected = sum(new[k] for k in ("PROTECTED_STRONG_2C_DOMAIN", "PROTECTED_PREEMPT_DOMAIN", "PROTECTED_EQUAL_SUIT_DOMAIN", "OTHER_PROTECTED_UNRESOLVED"))
    assert old["PROTECTED_UNRESOLVED"] == 65
    assert protected == 65 - 3 + 58 == 120
    assert moves[("SOURCE_OR_POLICY_INSUFFICIENT", "OTHER_PROTECTED_UNRESOLVED")] == 58
    assert sum(new.values()) == sum(old.values()) == 616
    assert sum(n for _,_,n in r.phase29m_to_n) == 616
    assert dict(r.full_population_overall_counts) == {"SAFE": 0, "UNSAFE": 45, "UNKNOWN": 571}


def test_serialization_examples_and_routes(sample):
    from bridge.sayc_route_configuration import create_standard_sayc_router
    batch, r = sample
    assert r.to_json() == build_pass_safety_audit_report(batch).to_json()
    assert json.loads(r.to_json()) == r.to_dict()
    assert all(len(cases) <= 3 for _, cases in r.representatives)
    assert r.simulation_errors == r.reproduction_errors == 0
    assert not r.production_ready
    assert not r.playing_trick_evaluator_found and not r.quick_trick_evaluator_found
    assert len(create_standard_sayc_router().routes) == 45
