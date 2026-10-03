"""A8.11 production abstention extraction tests."""
from bridge.abstention_diagnostics import AbstentionReason
from bridge.models import Seat
from bridge.production_gap_extraction import extract_production_abstentions


def test_empty_run():
    r = extract_production_abstentions(count=0)
    assert r.runs == r.completed == r.abstained == 0
    assert r.cases == () and r.groups == ()


def test_accounting_matches_production_run():
    r = extract_production_abstentions(count=100)
    assert r.completed + r.abstained == 100
    assert len(r.cases) == r.abstained


def test_only_production_seats_can_abstain():
    r = extract_production_abstentions(count=100)
    assert all(x.stopped_seat in (Seat.NORTH, Seat.SOUTH) for x in r.cases)


def test_every_case_has_replay_identity():
    r = extract_production_abstentions(count=100)
    assert all(x.seed >= 1 and x.deal and x.replay_key.endswith(str(x.seed)) for x in r.cases)


def test_reason_partition_is_complete():
    r = extract_production_abstentions(count=100)
    assert sum(n for _, n in r.reason_counts) == r.abstained
    assert r.count(AbstentionReason.NO_ROUTE) + r.count(
        AbstentionReason.ROUTED_NO_APPLICABLE_RULE
    ) == r.abstained


def test_no_route_has_no_route_id():
    r = extract_production_abstentions(count=100)
    assert all(
        x.diagnostic.route_id is None
        for x in r.cases
        if x.diagnostic.reason is AbstentionReason.NO_ROUTE
    )


def test_routed_abstention_has_route_id():
    r = extract_production_abstentions(count=100)
    assert all(
        x.diagnostic.route_id
        for x in r.cases
        if x.diagnostic.reason is AbstentionReason.ROUTED_NO_APPLICABLE_RULE
    )


def test_group_counts_cover_all_abstentions():
    r = extract_production_abstentions(count=100)
    assert sum(x.count for x in r.groups) == r.abstained


def test_group_seed_counts_match():
    r = extract_production_abstentions(count=100)
    assert all(x.count == len(x.seeds) for x in r.groups)


def test_deterministic():
    a = extract_production_abstentions(start_seed=1, count=100)
    b = extract_production_abstentions(start_seed=1, count=100)
    assert a == b


def test_1000_case_gate():
    r = extract_production_abstentions(start_seed=1, count=1000)
    assert r.runs == 1000
    assert r.completed + r.abstained == 1000
    assert len(r.cases) == r.abstained


def test_no_policy_gap_or_ranking_surface():
    r = extract_production_abstentions(count=0)
    for name in (
        "policy_gap", "engine_defect", "rank", "ranking", "winner",
        "score", "priority", "correct", "selected", "preferred",
    ):
        assert not hasattr(r, name)
