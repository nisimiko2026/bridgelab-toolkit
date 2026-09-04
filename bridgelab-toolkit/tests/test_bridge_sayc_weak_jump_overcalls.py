import pytest
from bridge import Auction,BiddingContext,Hand,KnowledgeSource,OffensiveHandAssessment,OffensiveHandStatus,PolicyRegistry,Seat,SystemContext,Vulnerability
from bridge.policy_registry import OFFENSIVE_HAND_POLICY_OPTION
from bridge.sayc_weak_jump_overcalls import SaycWeakJumpOvercallRule,legal_direct_jump_overcall_suits
SRC=KnowledgeSource("bidding/systems/sayc","Weak Jump Overcalls")
class O:
    policy_id="fixture.offense"
    def __init__(self,status=OffensiveHandStatus.QUALIFIES):self.status=status
    def assess(self,c):
        if self.status is OffensiveHandStatus.UNKNOWN:return OffensiveHandAssessment.unknown(self.policy_id)
        if self.status is OffensiveHandStatus.DOES_NOT_QUALIFY:return OffensiveHandAssessment.does_not_qualify(self.policy_id,"reject",(SRC,))
        return OffensiveHandAssessment.qualifies(self.policy_id,"qualify",(SRC,))
def ctx(hand,opening="1D",policy=True):
    opts={} if not policy else {OFFENSIVE_HAND_POLICY_OPTION:"fixture.offense"}
    return BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,(opening,)),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",opts))
def rule(status=OffensiveHandStatus.QUALIFIES):
    return SaycWeakJumpOvercallRule(PolicyRegistry.from_offensive_hand_policies([O(status)]))
def test_1d_2s_source_shape_recommends():
    d=rule().evaluate(ctx("KQJ983.7.J82.Q63"))
    assert d.applicable and d.candidate.serialize()=="2S"
def test_jump_level_is_mechanical_after_major():
    # after 1H, a club jump is 3C because 2C is already a two-level simple overcall
    d=rule().evaluate(ctx("82.74.J82.KQJ983","1H"))
    assert d.applicable and d.candidate.serialize()=="3C"
def test_hcp_outside_source_range_abstains():
    assert not rule().evaluate(ctx("AKQJ98.7.A82.Q63")).applicable
def test_exactly_six_required():
    assert not rule().evaluate(ctx("KQJ9832.7.J8.Q63")).applicable
def test_missing_policy_abstains():
    assert not rule().evaluate(ctx("KQJ983.7.J82.Q63",policy=False)).applicable
def test_unknown_or_reject_abstains():
    assert not rule(OffensiveHandStatus.UNKNOWN).evaluate(ctx("KQJ983.7.J82.Q63")).applicable
    assert not rule(OffensiveHandStatus.DOES_NOT_QUALIFY).evaluate(ctx("KQJ983.7.J82.Q63")).applicable
def test_two_six_card_jump_suits_abstain():
    assert not rule().evaluate(ctx("KQJ983.-.2.QJT983","1D")).applicable
def test_source_trace_present():
    d=rule().evaluate(ctx("KQJ983.7.J82.Q63"))
    assert any(x.heading=="Weak Jump Overcalls" for x in d.sources)
