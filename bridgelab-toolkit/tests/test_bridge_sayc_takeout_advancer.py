from bridge import Auction,BiddingContext,Hand,KnowledgeSource,Seat,SystemContext,Vulnerability
from bridge.bidding_rules import evaluate_rule
from bridge.policy_registry import *
from bridge.sayc_takeout_advancer import SaycTakeoutAdvancerMinimumRule
from bridge.takeout_advancer_strength_policy import *

SRC=KnowledgeSource("bidding/conventions/doubles/take-out-double","Responses")
class Minimum:
 policy_id="fixture.minimum"
 def assess(self,c):return TakeoutAdvancerStrengthAssessment(self.policy_id,TakeoutAdvancerStrengthClass.MINIMUM,"fixture minimum",(SRC,))
class Invitational:
 policy_id="fixture.inv"
 def assess(self,c):return TakeoutAdvancerStrengthAssessment(self.policy_id,TakeoutAdvancerStrengthClass.INVITATIONAL,"fixture invitational",(SRC,))
def context(auction,hand,pid):
 return BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,auction),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",{TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION:pid}))
def test_after_1h_cheapest_four_card_unbid_is_1s():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([Minimum()])
 d=evaluate_rule(SaycTakeoutAdvancerMinimumRule(reg),context(("1H","X","P"),"KJ94.8732.63.Q63","fixture.minimum"))
 assert d.applicable and d.candidate.serialize()=="1S"
def test_after_1d_lowest_legal_level_precedes_two_clubs():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([Minimum()])
 d=evaluate_rule(SaycTakeoutAdvancerMinimumRule(reg),context(("1D","X","P"),"KJ94.8732.6.Q763","fixture.minimum"))
 assert d.applicable and d.candidate.serialize()=="1H"
def test_after_1c_diamond_is_cheapest():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([Minimum()])
 d=evaluate_rule(SaycTakeoutAdvancerMinimumRule(reg),context(("1C","X","P"),"KJ94.8732.Q763.6","fixture.minimum"))
 assert d.applicable and d.candidate.serialize()=="1D"
def test_after_1s_clubs_selected_at_two_level():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([Minimum()])
 d=evaluate_rule(SaycTakeoutAdvancerMinimumRule(reg),context(("1S","X","P"),"K94.8732.63.Q763","fixture.minimum"))
 assert d.applicable and d.candidate.serialize()=="2C"
def test_no_policy_abstains():
 d=evaluate_rule(SaycTakeoutAdvancerMinimumRule(PolicyRegistry()),context(("1H","X","P"),"KJ94.8732.63.Q63","missing"))
 assert not d.applicable
def test_invitational_is_not_swallowed():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([Invitational()])
 d=evaluate_rule(SaycTakeoutAdvancerMinimumRule(reg),context(("1H","X","P"),"KJ94.8732.63.Q63","fixture.inv"))
 assert not d.applicable
def test_openers_suit_is_not_selected():
 reg=PolicyRegistry.from_takeout_advancer_strength_policies([Minimum()])
 d=evaluate_rule(SaycTakeoutAdvancerMinimumRule(reg),context(("1D","X","P"),"KJ94.8732.Q763.6","fixture.minimum"))
 assert d.candidate.serialize()=="1H"
