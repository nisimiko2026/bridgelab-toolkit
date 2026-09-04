from bridge import Auction,BiddingContext,Seat,SystemContext,Hand,Vulnerability
from bridge.sayc_1d1s_opener_rebids import create_sayc_one_diamond_one_spade_opener_rebid_engine
def ctx(h):
 a=Auction(Seat.NORTH)
 for x in ("1D","P","1S","P"):a.add(x)
 return BiddingContext.create(hand=Hand.parse(h),seat=Seat.NORTH,auction=a,system=SystemContext("SAYC"),vulnerability=Vulnerability.NONE)
def bid(h):
 return create_sayc_one_diamond_one_spade_opener_rebid_engine().evaluate(ctx(h)).recommended_call
def test_support(): assert bid("AK84.32.AK76.543").serialize()=="2S"
def test_clubs(): assert bid("A82.32.AK76.QJ54").serialize()=="2C"
def test_reverse(): assert bid("A82.KQJ4.AK765.4").serialize()=="2H"
def test_nt(): assert bid("A82.K83.QJ76.K54").serialize()=="1NT"
def test_nt_does_not_bypass_clubs(): assert bid("A82.K8.QJ76.KJ54").serialize()=="2C"

def test_two_nt(): assert bid("A82.K83.AQJ6.KQ4").serialize()=="2NT"
def test_six_diamonds(): assert bid("A82.K3.AQJ765.54").serialize()=="2D"
def test_two_diamonds_does_not_bypass_clubs(): assert bid("A82.3.AQJ76.KJ54").serialize()=="2C"
