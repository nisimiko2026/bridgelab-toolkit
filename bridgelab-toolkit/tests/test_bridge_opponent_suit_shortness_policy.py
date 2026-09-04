import pytest
from bridge import Auction,BiddingContext,Hand,KnowledgeSource,Seat,SystemContext,Vulnerability
from bridge.models import Suit
from bridge.opponent_suit_shortness_policy import *
from bridge.policy_registry import *
SRC=KnowledgeSource("bidding/systems/sayc","Takeout Double")
def ctx(pid=None):
 opts={} if pid is None else {OPPONENT_SUIT_SHORTNESS_POLICY_OPTION:pid}
 return BiddingContext.create(hand=Hand.parse("KQJ9.8742.3.AQ63"),auction=Auction(Seat.NORTH,("1D",)),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",opts))
class P:
 policy_id="fixture.short"
 def assess(self,c,suit,length):
  return OpponentSuitShortnessAssessment(self.policy_id,OpponentSuitShortnessStatus.QUALIFIES,suit,length,"fixture qualifies",(SRC,))
def test_preserves_objective_length():
 r=assess_opponent_suit_shortness(P(),ctx(),Suit.DIAMONDS,1)
 assert r.status is OpponentSuitShortnessStatus.QUALIFIES and r.suit_length==1
def test_known_requires_trace():
 with pytest.raises(ValueError): OpponentSuitShortnessAssessment("x",OpponentSuitShortnessStatus.QUALIFIES,Suit.DIAMONDS,1)
def test_registry_explicit_only():
 reg=PolicyRegistry.from_opponent_suit_shortness_policies([P()])
 assert assess_configured_opponent_suit_shortness(ctx(),reg,Suit.DIAMONDS,1) is None
 assert assess_configured_opponent_suit_shortness(ctx("fixture.short"),reg,Suit.DIAMONDS,1).suit_length==1
def test_no_threshold_is_built_in():
 # policy receives even length 3 unchanged; architecture itself does not decide whether 3 is short.
 assert assess_opponent_suit_shortness(P(),ctx(),Suit.DIAMONDS,3).suit_length==3
