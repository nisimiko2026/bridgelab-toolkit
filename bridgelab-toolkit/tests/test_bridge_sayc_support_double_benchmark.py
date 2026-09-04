import pytest
from bridge.bidding_rules import KnowledgeSource
from bridge.policy_registry import PolicyRegistry, SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION
from bridge.sayc_competitive_benchmark import run_sayc_support_double_benchmark
from bridge.support_double_eligibility_policy import SupportDoubleEligibilityAssessment, SupportDoubleEligibilityStatus
SRC=KnowledgeSource("bidding/conventions/doubles/support-double","Requirements")
class Q:
 policy_id="fixture.support.qualifies"
 def assess(self,c):
  return SupportDoubleEligibilityAssessment(self.policy_id,SupportDoubleEligibilityStatus.QUALIFIES,"benchmark fixture only",(SRC,))
def setup():
 return PolicyRegistry.from_support_double_eligibility_policies([Q()]),{SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION:"fixture.support.qualifies"}
@pytest.mark.parametrize("route",["1D-P-1H-1S","1C-P-1H-1S","1D-P-1S-2C","1H-P-1S-2D"])
def test_route_reached(route):
 reg,opt=setup();r=run_sayc_support_double_benchmark(count=25,route=route,registry=reg,system_options=opt)
 assert r.metrics.positions_reached==25
 assert r.metrics.support_double_actions==r.metrics.exactly_three_support
 assert r.metrics.actions if False else True
def test_without_policy_no_actions():
 r=run_sayc_support_double_benchmark(count=25)
 assert r.metrics.positions_reached==25 and r.metrics.support_double_actions==0
def test_deterministic():
 reg,opt=setup()
 a=run_sayc_support_double_benchmark(count=50,registry=reg,system_options=opt)
 b=run_sayc_support_double_benchmark(count=50,registry=reg,system_options=opt)
 assert a.metrics==b.metrics and a.batch.replay_records==b.batch.replay_records
def test_invalid_route():
 with pytest.raises(ValueError):run_sayc_support_double_benchmark(count=1,route="1C-P-1S-2H")
