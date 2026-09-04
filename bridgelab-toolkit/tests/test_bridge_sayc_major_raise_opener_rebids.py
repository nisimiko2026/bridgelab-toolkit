from bridge import Auction,BiddingContext,Seat,SystemContext,Hand,Vulnerability,Strain
from bridge.sayc_major_raise_opener_rebids import create_sayc_simple_major_raise_opener_rebid_engine
def ctx(h,calls):
 a=Auction(Seat.NORTH)
 for x in calls:a.add(x)
 return BiddingContext.create(hand=Hand.parse(h),seat=Seat.NORTH,auction=a,system=SystemContext("SAYC"),vulnerability=Vulnerability.NONE)
def test_spade_minimum_passes():
 r=create_sayc_simple_major_raise_opener_rebid_engine(Strain.SPADES).evaluate(ctx("AQ853.K82.J76.A7",("1S","P","2S","P")))
 assert r.recommended_call.serialize()=="P"
def test_heart_minimum_passes():
 r=create_sayc_simple_major_raise_opener_rebid_engine(Strain.HEARTS).evaluate(ctx("A7.AQ853.K82.J76",("1H","P","2H","P")))
 assert r.recommended_call.serialize()=="P"
def test_medium_spade_hand_abstains():
 r=create_sayc_simple_major_raise_opener_rebid_engine(Strain.SPADES).evaluate(ctx("AKQ53.K82.J76.A7",("1S","P","2S","P")))
 assert r.recommended is None
def test_bergen_configuration_abstains():
 sys=SystemContext("SAYC",options=(("major_raise_style","bergen"),))
 a=Auction(Seat.NORTH)
 for x in ("1S","P","2S","P"):a.add(x)
 c=BiddingContext.create(hand=Hand.parse("AQ853.K82.J76.A7"),seat=Seat.NORTH,auction=a,system=sys,vulnerability=Vulnerability.NONE)
 assert create_sayc_simple_major_raise_opener_rebid_engine(Strain.SPADES).evaluate(c).recommended is None
def test_nonmajor_factory_rejected():
 import pytest
 with pytest.raises(ValueError):create_sayc_simple_major_raise_opener_rebid_engine(Strain.CLUBS)
