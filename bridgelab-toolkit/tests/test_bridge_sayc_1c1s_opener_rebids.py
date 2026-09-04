from bridge import Auction,BiddingContext,Seat,SystemContext,Hand,Vulnerability
from bridge.sayc_1c1s_opener_rebids import create_sayc_one_club_one_spade_opener_rebid_engine
def ctx(h):
 a=Auction(Seat.NORTH)
 for x in ("1C","P","1S","P"):a.add(x)
 return BiddingContext.create(hand=Hand.parse(h),seat=Seat.NORTH,auction=a,system=SystemContext("SAYC"),vulnerability=Vulnerability.NONE)
def bid(h): return create_sayc_one_club_one_spade_opener_rebid_engine().evaluate(ctx(h)).recommended_call
def test_support(): assert bid("AK84.32.543.AK76").serialize()=="2S"
def test_reverse_hearts(): assert bid("A82.KQJ4.3.AKQ76").serialize()=="2H"
def test_reverse_requires_clubs_longer_than_hearts(): assert bid("A82.KQJ4.Q3.AK76") is None
def test_diamonds(): assert bid("A82.K3.QJ54.AK76").serialize()=="2D"
def test_nt(): assert bid("A82.K83.Q54.KJ76").serialize()=="1NT"
def test_two_nt(): assert bid("A82.K83.AQ4.AQ76").serialize()=="2NT"
def test_six_clubs(): assert bid("A82.32.54.AKQJ76").serialize()=="2C"
def test_diamonds_do_not_bypass_hearts(): assert bid("A82.KQJ4.Q543.AK") is None
