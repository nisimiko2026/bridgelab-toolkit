from bridge import Auction,BiddingContext,Seat,SystemContext,Hand,Vulnerability
from bridge.sayc_1c1h_opener_rebids import create_sayc_one_club_one_heart_opener_rebid_engine
def ctx(h):
 a=Auction(Seat.NORTH)
 for x in ("1C","P","1H","P"):a.add(x)
 return BiddingContext.create(hand=Hand.parse(h),seat=Seat.NORTH,auction=a,system=SystemContext("SAYC"),vulnerability=Vulnerability.NONE)
def bid(h): return create_sayc_one_club_one_heart_opener_rebid_engine().evaluate(ctx(h)).recommended_call
def test_support(): assert bid("A84.KQ84.32.AK76").serialize()=="2H"
def test_four_spades(): assert bid("AK84.K82.32.AQ76").serialize()=="1S"
def test_six_clubs(): assert bid("A82.K8.32.AKQJ76").serialize()=="2C"
def test_nt(): assert bid("A82.K83.Q54.KJ76").serialize()=="1NT"
def test_clubs_do_not_bypass_spades(): assert bid("AK84.K82.3.AKQ76").serialize()=="1S"
def test_nt_does_not_bypass_spades(): assert bid("AQ84.K82.Q54.K76").serialize()=="1S"
