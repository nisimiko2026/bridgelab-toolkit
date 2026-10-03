"""A8.15 consolidated production benchmark report tests."""
from bridge.production_benchmark_report import build_consolidated_production_benchmark_report
from bridge.production_gap_evidence import EvidenceClass


def test_empty():
    r=build_consolidated_production_benchmark_report(count=0)
    assert r.summary.runs==r.summary.completed==r.summary.abstained==0
    assert r.summary.completion_rate==r.summary.abstention_rate==0.0


def test_1000_headline_baseline():
    r=build_consolidated_production_benchmark_report(count=1000)
    assert r.summary.runs==1000
    assert r.summary.completed==75
    assert r.summary.abstained==925
    assert r.summary.production_calls==850
    assert r.summary.fixture_calls==850


def test_component_accounting_agrees():
    r=build_consolidated_production_benchmark_report(count=1000)
    assert r.concentration.abstained==r.evidence.abstained==r.representatives.abstained==925


def test_rates():
    r=build_consolidated_production_benchmark_report(count=1000)
    assert r.summary.completion_rate==0.075
    assert r.summary.abstention_rate==0.925


def test_evidence_partition():
    r=build_consolidated_production_benchmark_report(count=1000)
    assert sum(g.count for g in r.evidence.groups)==r.summary.abstained


def test_concentration_dimensions():
    r=build_consolidated_production_benchmark_report(count=1000)
    for groups in (r.concentration.by_reason,r.concentration.by_depth,r.concentration.by_route,r.concentration.by_auction):
        assert sum(g.count for g in groups)==r.summary.abstained


def test_representatives_are_bounded_examples():
    r=build_consolidated_production_benchmark_report(count=1000,per_class_limit=5)
    assert r.representatives.selected_count==15
    assert all(len(g.cases)<=5 for g in r.representatives.groups)


def test_all_evidence_classes_present():
    r=build_consolidated_production_benchmark_report(count=1000)
    assert {g.evidence_class for g in r.evidence.groups}==set(EvidenceClass)


def test_deterministic():
    assert build_consolidated_production_benchmark_report(count=100)==build_consolidated_production_benchmark_report(count=100)


def test_no_ranking_correctness_policy_surface():
    r=build_consolidated_production_benchmark_report(count=0)
    for n in ("priority","rank","ranking","winner","score","correct","accuracy","policy_gap","engine_defect"):
        assert not hasattr(r,n)


def test_seed_window_preserved():
    r=build_consolidated_production_benchmark_report(start_seed=101,count=10)
    assert r.summary.start_seed==101
    assert r.summary.runs==10


def test_1000_replay_population_consistency():
    r=build_consolidated_production_benchmark_report(count=1000)
    assert sum(g.available_count for g in r.representatives.groups)==925
