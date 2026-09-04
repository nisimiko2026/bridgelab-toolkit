import pytest
from bridge.milestone_benchmark import (
    DEFAULT_DEAL_COUNT,MILESTONE_VERSION,SCENARIOS,
    MilestoneResult,summarize_milestone,validate_milestone_results,
)

def result(sid,actions=10,abstentions=90):
    return MilestoneResult(sid,DEFAULT_DEAL_COUNT,100,actions,abstentions,())

def test_frozen_version_and_100k_default():
    assert MILESTONE_VERSION=="phase10a.v1"
    assert DEFAULT_DEAL_COUNT==100_000

def test_scenarios_have_unique_ids():
    assert len({x.scenario_id for x in SCENARIOS})==len(SCENARIOS)

def test_competitive_policy_gates_are_explicit():
    competitive=[x for x in SCENARIOS if x.family=="competitive"]
    assert competitive
    assert all(x.requires_explicit_policy for x in competitive)

def test_summary_is_deterministic_aggregation():
    rs=(result(SCENARIOS[0].scenario_id,20,80),result(SCENARIOS[1].scenario_id,30,70))
    a=summarize_milestone(rs)
    b=summarize_milestone(rs)
    assert a==b
    assert a.total_positions==200
    assert a.total_actions==50
    assert a.total_abstentions==150

def test_reject_unknown_scenario():
    with pytest.raises(ValueError):
        validate_milestone_results((result("unknown"),),deal_count=DEFAULT_DEAL_COUNT)

def test_reject_duplicate_scenario():
    x=result(SCENARIOS[0].scenario_id)
    with pytest.raises(ValueError):
        validate_milestone_results((x,x),deal_count=DEFAULT_DEAL_COUNT)

def test_reject_wrong_deal_count():
    x=MilestoneResult(SCENARIOS[0].scenario_id,10,10,1,9,())
    with pytest.raises(ValueError):
        validate_milestone_results((x,),deal_count=DEFAULT_DEAL_COUNT)

def test_reject_impossible_counts():
    x=MilestoneResult(SCENARIOS[0].scenario_id,DEFAULT_DEAL_COUNT,10,8,8,())
    with pytest.raises(ValueError):
        validate_milestone_results((x,),deal_count=DEFAULT_DEAL_COUNT)
