import pytest
from bridge import KnowledgeSource
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_competitive_benchmark import run_sayc_takeout_advancer_benchmark
from bridge.policy_registry import TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION
from bridge.takeout_advancer_strength_policy import TakeoutAdvancerStrengthAssessment,TakeoutAdvancerStrengthClass
SRC=KnowledgeSource("bidding/conventions/doubles/take-out-double","Responses")
class Minimum:
 policy_id="fixture.minimum"
 def assess(self,c): return TakeoutAdvancerStrengthAssessment(self.policy_id,TakeoutAdvancerStrengthClass.MINIMUM,"fixture",(SRC,))
def test_deterministic():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([Minimum()])
 opts={TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION:"fixture.minimum"}
 a=run_sayc_takeout_advancer_benchmark(start_seed=1,count=50,opening="1D",registry=reg,system_options=opts)
 b=run_sayc_takeout_advancer_benchmark(start_seed=1,count=50,opening="1D",registry=reg,system_options=opts)
 assert a.metrics==b.metrics and a.batch.replay_records==b.batch.replay_records
@pytest.mark.parametrize("opening",["1C","1D","1H","1S"])
def test_reaches_advancer(opening):
 r=run_sayc_takeout_advancer_benchmark(count=20,opening=opening)
 assert r.metrics.advancer_positions_reached==20
 assert r.metrics.advancer_actions==0 and r.metrics.advancer_abstentions==20
def test_minimum_policy_activates_some_cases():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([Minimum()])
 r=run_sayc_takeout_advancer_benchmark(count=100,opening="1H",registry=reg,system_options={TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION:"fixture.minimum"})
 assert r.metrics.advancer_actions>0
 assert dict(r.metrics.production_rule_counts)=={"sayc.advancer.takeout.minimum.natural":r.metrics.advancer_actions}
def test_invalid_opening():
 with pytest.raises(ValueError):run_sayc_takeout_advancer_benchmark(count=1,opening="1NT")
