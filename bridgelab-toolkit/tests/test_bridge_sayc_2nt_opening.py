from bridge import Auction,BiddingContext,Seat,SystemContext,Hand,Vulnerability
from bridge.sayc import create_sayc_opening_engine
def bid(h):
 c=BiddingContext.create(hand=Hand.parse(h),seat=Seat.NORTH,auction=Auction(Seat.NORTH),system=SystemContext("SAYC"),vulnerability=Vulnerability.NONE)
 d=create_sayc_opening_engine().evaluate(c)
 return None if d.recommended_call is None else d.recommended_call.serialize()
def test_20_balanced(): assert bid("AQ3.KJ4.AQ76.KJ3")=="2NT"
def test_21_balanced(): assert bid("AQ3.KJ4.AQ76.AJ3")=="2NT"
def test_19_not_2nt(): assert bid("AQ3.KJ4.AJ76.KJ3")!="2NT"
def test_22_not_2nt(): assert bid("AK3.AJ4.AQ76.AJ3")!="2NT"
def test_unbalanced_not_2nt(): assert bid("AQ32.KJ42.AQ76.A")!="2NT"
