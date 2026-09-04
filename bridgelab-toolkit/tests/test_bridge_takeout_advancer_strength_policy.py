import pytest
from bridge import Auction,BiddingContext,Hand,KnowledgeSource,Seat,SystemContext,Vulnerability
from bridge.takeout_advancer_strength_policy import *
from bridge.policy_registry import *
SRC=KnowledgeSource("bidding/conventions/doubles/take-out-double","Responses")
def ctx(pid=None):
 opts={} if pid is None else {TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION:pid}
 return BiddingContext.create(hand=Hand.parse("KJ94.8742.63.Q63"),auction=Auction(Seat.NORTH,("1D","X","Pass")),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",opts))
class P:
 policy_id="fixture.minimum"
 def assess(self,c):
  return TakeoutAdvancerStrengthAssessment(self.policy_id,TakeoutAdvancerStrengthClass.MINIMUM,"fixture",(SRC,))
def test_explicit_classification():
 r=assess_takeout_advancer_strength(P(),ctx())
 assert r.strength_class is TakeoutAdvancerStrengthClass.MINIMUM
def test_known_requires_trace():
 with pytest.raises(ValueError): TakeoutAdvancerStrengthAssessment("x",TakeoutAdvancerStrengthClass.MINIMUM)
def test_registry_has_no_default():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([P()])
 assert assess_configured_takeout_advancer_strength(ctx(),reg) is None
def test_registry_resolves_explicit_policy():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([P()])
 assert assess_configured_takeout_advancer_strength(ctx("fixture.minimum"),reg).strength_class is TakeoutAdvancerStrengthClass.MINIMUM
def test_architecture_embeds_no_hcp_boundary():
 # Classification is delegated entirely to the supplied policy.
 assert assess_takeout_advancer_strength(P(),ctx()).strength_class is TakeoutAdvancerStrengthClass.MINIMUM
