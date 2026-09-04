from bridge import Auction,BiddingContext,Hand,KnowledgeSource,Seat,SystemContext,Vulnerability
from bridge.models import Suit
from bridge.opponent_suit_shortness_policy import *
from bridge.policy_registry import *
from bridge.sayc_takeout_double import SaycTakeoutDoubleRule
SRC=KnowledgeSource("bidding/systems/sayc","Takeout Double")
class Short:
 policy_id="fixture.short"
 def assess(self,c,suit,length):
  return OpponentSuitShortnessAssessment(self.policy_id,OpponentSuitShortnessStatus.QUALIFIES,suit,length,"fixture",(SRC,))
class NotShort:
 policy_id="fixture.not"
 def assess(self,c,suit,length):
  return OpponentSuitShortnessAssessment(self.policy_id,OpponentSuitShortnessStatus.DOES_NOT_QUALIFY,suit,length,"fixture",(SRC,))
def C(hand,pid=None,opening="1D"):
 opts={} if pid is None else {OPPONENT_SUIT_SHORTNESS_POLICY_OPTION:pid}
 return BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,(opening,)),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",opts))
def test_qualifies_with_explicit_policy():
 reg=PolicyRegistry.from_opponent_suit_shortness_policies([Short()])
 d=SaycTakeoutDoubleRule(reg).evaluate(C("KQJ9.AQ84.3.KJ63","fixture.short"))
 assert d.applicable and str(d.candidate)=="X"
def test_no_policy_abstains():
 assert not SaycTakeoutDoubleRule(PolicyRegistry()).evaluate(C("KQJ9.AQ84.3.KJ63")).applicable
def test_less_than_12_abstains():
 reg=PolicyRegistry.from_opponent_suit_shortness_policies([Short()])
 assert not SaycTakeoutDoubleRule(reg).evaluate(C("KQJ9.A842.3.J963","fixture.short")).applicable
def test_every_unbid_suit_needs_three():
 reg=PolicyRegistry.from_opponent_suit_shortness_policies([Short()])
 assert not SaycTakeoutDoubleRule(reg).evaluate(C("KQJ94.AQ84.32.KJ","fixture.short")).applicable
def test_rejected_shortness_abstains():
 reg=PolicyRegistry.from_opponent_suit_shortness_policies([NotShort()])
 assert not SaycTakeoutDoubleRule(reg).evaluate(C("KQJ9.AQ84.3.KJ63","fixture.not")).applicable
