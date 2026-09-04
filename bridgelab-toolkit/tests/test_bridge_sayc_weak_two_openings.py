from bridge import Auction,BiddingContext,Seat,SystemContext,Hand,Vulnerability
from bridge.sayc import create_sayc_opening_engine
def bid(h):
 c=BiddingContext.create(hand=Hand.parse(h),seat=Seat.NORTH,auction=Auction(Seat.NORTH),system=SystemContext("SAYC"),vulnerability=Vulnerability.NONE)
 return create_sayc_opening_engine().evaluate(c).recommended_call
def test_weak_two_spades(): assert bid("KQJ876.32.43.543").serialize()=="2S"
def test_weak_two_hearts(): assert bid("32.KQJ876.43.543").serialize()=="2H"
def test_weak_two_diamonds(): assert bid("32.43.KQJ876.543").serialize()=="2D"
def test_below_range_abstains(): assert bid("QJ9876.32.43.543") is None
def test_above_range_does_not_use_weak_two(): assert bid("AKQJ87.K2.43.543").serialize()!="2S"
def test_five_card_suit_not_weak_two(): assert bid("KQJ87.632.43.543") is None
def test_seven_card_suit_advances_to_three_level_preempt(): assert bid("KQJ9876.3.43.543").serialize()=="3S"
def test_two_qualifying_suits_abstain(): assert bid("KQJ876.QJ9876.4.") is None
