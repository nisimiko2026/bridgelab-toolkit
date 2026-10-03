"""A8.14 representative/replay case tests."""
import pytest

from bridge.production_gap_evidence import EvidenceClass
from bridge.production_replay_cases import build_representative_replay_report


def test_negative_limit_rejected():
    with pytest.raises(ValueError):
        build_representative_replay_report(count=0, per_class_limit=-1)


def test_empty():
    r = build_representative_replay_report(count=0)
    assert r.runs == r.abstained == r.selected_count == 0
    assert r.groups == ()


def test_zero_limit_preserves_populations_but_selects_none():
    r = build_representative_replay_report(count=100, per_class_limit=0)
    assert r.groups
    assert r.selected_count == 0
    assert all(g.available_count > 0 and g.cases == () for g in r.groups)


def test_limit_respected():
    r = build_representative_replay_report(count=1000, per_class_limit=3)
    assert all(len(g.cases) <= 3 for g in r.groups)


def test_all_three_evidence_classes_represented_at_1000():
    r = build_representative_replay_report(count=1000)
    assert {g.evidence_class for g in r.groups} == set(EvidenceClass)


def test_available_counts_cover_abstentions():
    r = build_representative_replay_report(count=1000)
    assert sum(g.available_count for g in r.groups) == r.abstained == 925


def test_selection_is_lowest_seed_not_frequency_rank():
    r = build_representative_replay_report(count=1000, per_class_limit=5)
    for g in r.groups:
        seeds = [c.seed for c in g.cases]
        assert seeds == sorted(seeds)


def test_replay_identity_preserved():
    r = build_representative_replay_report(count=1000)
    for g in r.groups:
        for c in g.cases:
            assert c.replay_key == f"sayc-production@1:seed:{c.seed}"
            assert c.deal


def test_diagnostic_evidence_preserved():
    r = build_representative_replay_report(count=1000)
    for g in r.groups:
        for c in g.cases:
            assert c.reason
            if c.reason == "no-route":
                assert c.route_id is None
            else:
                assert c.route_id is not None


def test_evidence_class_matches_group():
    r = build_representative_replay_report(count=1000)
    assert all(c.evidence_class is g.evidence_class for g in r.groups for c in g.cases)


def test_deterministic():
    assert build_representative_replay_report(count=100) == build_representative_replay_report(count=100)


def test_no_priority_correctness_surface():
    r = build_representative_replay_report(count=0)
    for n in ("priority", "rank", "ranking", "winner", "score", "correct", "accuracy", "preferred"):
        assert not hasattr(r, n)


def test_1000_case_gate():
    r = build_representative_replay_report(count=1000, per_class_limit=5)
    assert r.runs == 1000
    assert r.abstained == 925
    assert r.selected_count == 15
