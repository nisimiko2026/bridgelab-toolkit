import pytest
from bridge import Auction,BiddingContext,Hand,KnowledgeSource,PolicyRegistry,Seat,StopperAssessment,SystemContext,Vulnerability
from bridge.models import Suit
from bridge.policy_registry import STOPPER_POLICY_OPTION
from bridge.sayc_direct_notrump_overcall import SaycDirectOneNotrumpOvercallRule
SRC=(KnowledgeSource("bidding/systems/sayc","Notrump Overcalls — Direct 1NT"),)
class Stop:
 policy_id="fixture.stop"
 def __init__(self,kind="yes"):self.kind=kind
 def assess(self,c,s):
  e=c.evaluation.honor_evidence(s)
  if self.kind=="unknown":return StopperAssessment.unknown(policy_id=self.policy_id,evidence=e)
  if self.kind=="no":return StopperAssessment.not_stopped(policy_id=self.policy_id,evidence=e,explanation="fixture no",sources=SRC)
  return StopperAssessment.stopped(policy_id=self.policy_id,evidence=e,explanation="fixture yes",sources=SRC)
def ctx(hand,opening="1H",policy=True,system="SAYC"):
 opts={STOPPER_POLICY_OPTION:"fixture.stop"} if policy else {}
 return BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,(opening,)),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping(system,opts))
def rule(kind="yes"):
 return SaycDirectOneNotrumpOvercallRule(PolicyRegistry.from_stopper_policies([Stop(kind)]))
@pytest.mark.parametrize("opening",["1C","1D","1H","1S"])
def test_15_18_balanced_stopped_recommends_1nt(opening):
 d=rule().evaluate(ctx("AQ84.KJ6.AT5.J32",opening))
 assert d.applicable and d.candidate.serialize()=="1NT"
def test_missing_stopper_policy_abstains(): assert not rule().evaluate(ctx("AQ84.KJ6.AT5.J32",policy=False)).applicable
def test_unknown_stopper_abstains(): assert not rule("unknown").evaluate(ctx("AQ84.KJ6.AT5.J32")).applicable
def test_unstopped_abstains(): assert not rule("no").evaluate(ctx("AQ84.KJ6.AT5.J32")).applicable
def test_outside_range_abstains(): assert not rule().evaluate(ctx("AQ84.KJ6.T75.932")).applicable
def test_unbalanced_abstains(): assert not rule().evaluate(ctx("AQ842.KJ65.AT5.J")).applicable
def test_non_sayc_abstains(): assert not rule().evaluate(ctx("AQ84.KJ6.AT5.J32",system="Other")).applicable
