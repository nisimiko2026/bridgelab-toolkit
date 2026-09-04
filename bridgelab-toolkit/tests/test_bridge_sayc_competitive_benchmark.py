import pytest

from bridge import run_sayc_direct_overcall_benchmark


def test_competitive_benchmark_is_deterministic():
    a = run_sayc_direct_overcall_benchmark(start_seed=1, count=50, opening="1D")
    b = run_sayc_direct_overcall_benchmark(start_seed=1, count=50, opening="1D")
    assert a.metrics == b.metrics
    assert a.batch.replay_records == b.batch.replay_records


@pytest.mark.parametrize("opening", ["1C", "1D", "1H", "1S"])
def test_each_scripted_one_level_opening_reaches_direct_position(opening):
    r = run_sayc_direct_overcall_benchmark(start_seed=1, count=20, opening=opening)
    assert r.metrics.direct_positions_reached == 20
    assert r.metrics.direct_actions == 0
    assert r.metrics.direct_abstentions == 20
    assert all(case.result.final_auction == opening for case in r.batch.cases)


def test_invalid_scripted_opening_is_rejected():
    with pytest.raises(ValueError):
        run_sayc_direct_overcall_benchmark(count=1, opening="1NT")


def test_empty_competitive_benchmark():
    r = run_sayc_direct_overcall_benchmark(start_seed=1, count=0, opening="1D")
    assert r.metrics.runs == 0
    assert r.metrics.direct_positions_reached == 0
    assert r.metrics.direct_actions == 0
    assert r.metrics.direct_abstentions == 0
