import pytest
from bridge import Auction,BiddingContext,Hand,KnowledgeSource,OffensiveHandAssessment,PolicyRegistry,Seat,SystemContext,Vulnerability
from bridge.policy_registry import OFFENSIVE_HAND_POLICY_OPTION,assess_configured_offensive_hand
SOURCE=KnowledgeSource("bidding/systems/sayc","Weak Jump Overcalls")
class P:
    def __init__(self,pid="fixture"): self.policy_id=pid
    def assess(self,c): return OffensiveHandAssessment.qualifies(self.policy_id,"yes",(SOURCE,))
def ctx(pid=None):
    opts={} if pid is None else {OFFENSIVE_HAND_POLICY_OPTION:pid}
    return BiddingContext.create(hand=Hand.parse("KQJ983.7.J82.Q63"),auction=Auction(Seat.NORTH,("1D",)),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",opts))
def test_registry_and_configuration():
    p=P(); r=PolicyRegistry.from_offensive_hand_policies([p])
    assert r.offensive_hand_policy_ids==("fixture",)
    assert assess_configured_offensive_hand(ctx("fixture"),r).qualifies_offense is True
def test_no_default():
    assert assess_configured_offensive_hand(ctx(),PolicyRegistry()) is None
def test_combined_registry():
    p=P(); r=PolicyRegistry.from_policies(offensive_hand_policies=[p])
    assert r.offensive_hand_policy("FIXTURE") is p
def test_duplicate_rejected():
    with pytest.raises(ValueError): PolicyRegistry.from_offensive_hand_policies([P("X"),P("x")])
