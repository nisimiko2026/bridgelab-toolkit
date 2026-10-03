"""A8.10 production-scale SAYC benchmark tests."""
import pytest
from bridge.production_scale_benchmark import ProductionScaleBenchmarkReport,run_production_scale_benchmark

def test_zero_case_production_run():
    r=run_production_scale_benchmark(count=0)
    assert r.count==0 and r.replay_records==()
    assert r.completed==0 and r.abstained==0

def test_small_production_run_preserves_replay_records():
    r=run_production_scale_benchmark(start_seed=1,count=10)
    assert len(r.replay_records)==10
    assert r.coverage.metrics.runs==10

def test_same_seed_range_is_deterministic():
    a=run_production_scale_benchmark(start_seed=1,count=25)
    b=run_production_scale_benchmark(start_seed=1,count=25)
    assert a.coverage.metrics==b.coverage.metrics
    assert a.replay_records==b.replay_records

def test_accounting_completed_plus_abstained_equals_runs():
    r=run_production_scale_benchmark(count=100)
    assert r.completed+r.abstained==100

def test_production_and_fixture_calls_remain_separate():
    r=run_production_scale_benchmark(count=100)
    assert r.coverage.metrics.production_calls>=0
    assert r.coverage.metrics.fixture_calls>=0
    assert all(not rule.startswith("benchmark.fixture.") for rule,_ in r.coverage.metrics.production_rule_counts)

def test_rates_are_bounded():
    r=run_production_scale_benchmark(count=100)
    for value in (r.opening_rate,r.responder_bid_rate,r.opener_rebid_rate):
        assert 0.0<=value<=1.0

def test_1000_case_production_gate():
    r=run_production_scale_benchmark(start_seed=1,count=1000)
    assert r.count==1000
    assert len(r.replay_records)==1000
    assert r.completed+r.abstained==1000

def test_start_seed_validation():
    with pytest.raises(TypeError): run_production_scale_benchmark(start_seed=True,count=1)

def test_count_type_validation():
    with pytest.raises(TypeError): run_production_scale_benchmark(count=True)

def test_negative_count_rejected():
    with pytest.raises(ValueError): run_production_scale_benchmark(count=-1)

def test_report_is_immutable():
    r=run_production_scale_benchmark(count=0)
    with pytest.raises(AttributeError): r.count=1

def test_no_rank_winner_score_correctness_or_policy_override_surface():
    r=run_production_scale_benchmark(count=0)
    for name in ("rank","ranking","winner","score","correct","accuracy","selected","preferred","override"):
        assert not hasattr(r,name)
