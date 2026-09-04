from bridge.milestone_runner import run_phase10_milestone

def test_small_validation_reaches_all_frozen_scenarios():
    r=run_phase10_milestone(start_seed=1,count=20)
    assert r.deal_count==20
    assert len(r.results)==4
    assert all(x.positions_reached>0 for x in r.results)

def test_small_validation_is_deterministic():
    a=run_phase10_milestone(start_seed=1,count=25)
    b=run_phase10_milestone(start_seed=1,count=25)
    assert a==b

def test_seed_changes_result():
    a=run_phase10_milestone(start_seed=1,count=50)
    b=run_phase10_milestone(start_seed=51,count=50)
    assert a!=b

def test_direct_preflight_exercises_multiple_competitive_rule_families():
    r=run_phase10_milestone(start_seed=1,count=1000)
    direct=next(x for x in r.results if x.scenario_id=="sayc.direct.competition")
    rules=dict(direct.rule_counts)
    assert rules.get("sayc.overcall.one_level.natural",0)>0
    assert rules.get("sayc.overcall.weak_jump",0)>0
    assert rules.get("sayc.double.takeout.direct",0)>0
    assert rules.get("sayc.overcall.direct.1nt",0)>0

def test_chunked_matches_single_run_exactly():
    from bridge.milestone_runner import run_phase10_milestone_chunked
    a=run_phase10_milestone(start_seed=1,count=40)
    b=run_phase10_milestone_chunked(start_seed=1,count=40,chunk_size=10)
    assert a==b

def test_chunked_handles_partial_last_chunk():
    from bridge.milestone_runner import run_phase10_milestone_chunked
    a=run_phase10_milestone(start_seed=5,count=23)
    b=run_phase10_milestone_chunked(start_seed=5,count=23,chunk_size=7)
    assert a==b
