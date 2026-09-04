from bridge import Auction, BiddingContext, Call, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc import SaycThreeLevelPreemptOpeningRule, create_sayc_opening_engine
from bridge.models import Suit

def ctx(hand, system="SAYC"):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, ()),
        vulnerability=Vulnerability.NONE,
        system=SystemContext(system),
    )

def test_3s_exact_seven_cards_6_hcp():
    r=create_sayc_opening_engine().evaluate(ctx("KQJ9874.82.74.83"))
    assert r.recommended_call == Call.parse("3S")

def test_3h_exact_seven_cards_10_hcp():
    r=create_sayc_opening_engine().evaluate(ctx("82.AQJ9874.K7.83"))
    assert r.recommended_call == Call.parse("3H")

def test_3d_exact_seven_cards():
    r=create_sayc_opening_engine().evaluate(ctx("82.74.AQJ9874.83"))
    assert r.recommended_call == Call.parse("3D")

def test_3c_exact_seven_cards():
    r=create_sayc_opening_engine().evaluate(ctx("82.74.83.AQJ9874"))
    assert r.recommended_call == Call.parse("3C")

def test_rejects_below_6_hcp():
    d=SaycThreeLevelPreemptOpeningRule(Suit.SPADES,"3S","x").evaluate(ctx("J987432.82.74.Q3"))
    assert not d.applicable

def test_rejects_above_10_hcp():
    d=SaycThreeLevelPreemptOpeningRule(Suit.HEARTS,"3H","x").evaluate(ctx("82.AQJ9874.A7.83"))
    assert not d.applicable

def test_rejects_six_card_suit():
    d=SaycThreeLevelPreemptOpeningRule(Suit.SPADES,"3S","x").evaluate(ctx("QJ9874.82.743.83"))
    assert not d.applicable

def test_sayc_only():
    d=SaycThreeLevelPreemptOpeningRule(Suit.SPADES,"3S","x").evaluate(ctx("KQJ9874.82.74.83","Acol"))
    assert not d.applicable

def test_seven_plus_six_preempt_choice_abstains_without_source_tiebreak():
    r=create_sayc_opening_engine().evaluate(ctx("KQJ9876.QJ9876.."))
    assert not r.has_recommendation
