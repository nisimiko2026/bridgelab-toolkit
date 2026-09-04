from bridge import run_sayc_coverage_benchmark


def test_benchmark_is_deterministic():
    a=run_sayc_coverage_benchmark(start_seed=1,count=50)
    b=run_sayc_coverage_benchmark(start_seed=1,count=50)
    assert a.metrics==b.metrics
    assert a.batch.replay_records==b.batch.replay_records


def test_baseline_labels_fixture_calls_separately():
    r=run_sayc_coverage_benchmark(start_seed=1,count=50)
    assert r.metrics.fixture_calls>=0
    assert all(not rule.startswith("benchmark.fixture.") for rule,_ in r.metrics.production_rule_counts)


def test_metrics_are_bounded():
    m=run_sayc_coverage_benchmark(start_seed=1,count=50).metrics
    assert 0<=m.opened<=m.runs
    assert 0<=m.responder_reached<=m.opened
    assert 0<=m.responder_bid<=m.responder_reached
    assert 0<=m.opener_rebid<=m.responder_bid
    assert m.completed+m.abstained<=m.runs


def test_empty_benchmark_has_zero_rates():
    m=run_sayc_coverage_benchmark(start_seed=1,count=0).metrics
    assert m.opening_rate==0.0
    assert m.responder_bid_rate==0.0
    assert m.opener_rebid_rate==0.0
