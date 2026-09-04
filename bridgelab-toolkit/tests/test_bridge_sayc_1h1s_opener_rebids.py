from bridge import Auction,BiddingContext,Seat,SystemContext,Hand,Vulnerability
from bridge.sayc_1h1s_opener_rebids import create_sayc_one_heart_one_spade_opener_rebid_engine
def ctx(h):
 a=Auction(Seat.NORTH)
 for x in ("1H","P","1S","P"):a.add(x)
 return BiddingContext.create(hand=Hand.parse(h),seat=Seat.NORTH,auction=a,system=SystemContext("SAYC"),vulnerability=Vulnerability.NONE)
def bid(h): return create_sayc_one_heart_one_spade_opener_rebid_engine().evaluate(ctx(h)).recommended_call
def test_six_hearts_without_higher_branch_rebids_two_hearts(): assert bid("A82.AKQJ76.32.54").serialize()=="2H"
def test_balanced_12_14_without_higher_branch_rebids_1nt(): assert bid("A82.KQJ84.Q54.32").serialize()=="1NT"
def test_two_hearts_abstains_with_four_clubs(): assert bid("A8.AKQJ76.3.KJ54") is None
def test_four_diamonds_are_shown_when_no_club_overlap(): assert bid("A8.AKQJ76.QJ54.3").serialize()=="2D"
def test_diamond_rule_abstains_when_clubs_also_four(): assert bid("A.AKQJ.QJ54.KJ54") is None
def test_balanced_18_19_without_higher_branch_rebids_2nt(): assert bid("AQ2.AKJ84.KQ3.54").serialize()=="2NT"
def test_rebid_abstains_with_spade_support(): assert bid("AQ84.AKJ76.32.54") is None
