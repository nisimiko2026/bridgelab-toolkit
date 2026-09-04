from bridge import continuation_breakdown,run_sayc_coverage_benchmark

def test_breakdown_matches_depth_four_abstention_population():
    r=run_sayc_coverage_benchmark(start_seed=1,count=1000)
    b=continuation_breakdown(r)
    expected=sum(1 for c in r.batch.cases if c.result.stop_reason.value=="no-recommendation" and len(c.result.steps)>=4)
    assert b.total==expected
    assert sum(x.count for x in b.auctions)==expected

def test_breakdown_is_frequency_then_lexical_ordered():
    b=continuation_breakdown(run_sayc_coverage_benchmark(start_seed=1,count=1000))
    pairs=[(-x.count,x.auction) for x in b.auctions]
    assert pairs==sorted(pairs)

def test_breakdown_is_deterministic():
    a=continuation_breakdown(run_sayc_coverage_benchmark(start_seed=1,count=1000))
    b=continuation_breakdown(run_sayc_coverage_benchmark(start_seed=1,count=1000))
    assert a==b
