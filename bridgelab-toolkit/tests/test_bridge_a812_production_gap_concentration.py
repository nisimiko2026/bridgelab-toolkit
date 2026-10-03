"""A8.12 production gap concentration tests."""
from bridge.production_gap_concentration import analyze_production_gap_concentration


def _sum(groups):
    return sum(x.count for x in groups)


def test_empty():
    r=analyze_production_gap_concentration(count=0)
    assert r.abstained==0
    assert r.by_reason==r.by_depth==r.by_route==r.by_auction==()


def test_each_dimension_accounts_for_all_abstentions():
    r=analyze_production_gap_concentration(count=100)
    for groups in (r.by_reason,r.by_depth,r.by_route,r.by_auction):
        assert _sum(groups)==r.abstained


def test_shares_sum_to_one_when_nonempty():
    r=analyze_production_gap_concentration(count=100)
    for groups in (r.by_reason,r.by_depth,r.by_route,r.by_auction):
        assert abs(sum(x.share_of_abstentions for x in groups)-1.0)<1e-12


def test_no_route_bucket_is_explicit():
    r=analyze_production_gap_concentration(count=100)
    assert any(x.key=="<NO_ROUTE>" for x in r.by_route)


def test_opening_abstention_bucket_is_explicit():
    r=analyze_production_gap_concentration(count=100)
    assert any(x.key=="<OPENING>" for x in r.by_auction)


def test_seed_provenance_preserved():
    r=analyze_production_gap_concentration(count=100)
    assert all(x.count==len(x.seeds) for groups in
               (r.by_reason,r.by_depth,r.by_route,r.by_auction) for x in groups)


def test_stable_lexical_not_frequency_order():
    r=analyze_production_gap_concentration(count=1000)
    for groups in (r.by_reason,r.by_depth,r.by_route,r.by_auction):
        assert [x.key for x in groups]==sorted(x.key for x in groups)


def test_deterministic():
    assert analyze_production_gap_concentration(count=100)==analyze_production_gap_concentration(count=100)


def test_1000_case_gate():
    r=analyze_production_gap_concentration(count=1000)
    assert r.source.runs==1000
    assert r.source.completed+r.abstained==1000


def test_no_priority_ranking_correctness_surface():
    r=analyze_production_gap_concentration(count=0)
    for name in ("priority","rank","ranking","winner","score","correct","accuracy","selected","preferred"):
        assert not hasattr(r,name)
