from bridge import analyze_benchmark_abstentions, run_sayc_coverage_benchmark

def test_all_baseline_abstentions_are_classified():
    r=run_sayc_coverage_benchmark(start_seed=1,count=100)
    a=analyze_benchmark_abstentions(r)
    assert len(a.classifications)==r.metrics.abstained
    assert sum(dict(a.stage_counts).values())==r.metrics.abstained

def test_classification_is_deterministic():
    a=analyze_benchmark_abstentions(run_sayc_coverage_benchmark(start_seed=1,count=100))
    b=analyze_benchmark_abstentions(run_sayc_coverage_benchmark(start_seed=1,count=100))
    assert a==b

def test_labels_are_descriptive_not_calls():
    a=analyze_benchmark_abstentions(run_sayc_coverage_benchmark(start_seed=1,count=100))
    assert all("." in x.label for x in a.classifications)
    assert all(x.label not in {"P","1C","1D","1H","1S","1NT"} for x in a.classifications)
