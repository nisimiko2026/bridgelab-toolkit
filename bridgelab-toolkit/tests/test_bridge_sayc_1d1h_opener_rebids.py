from bridge import (
    Auction, BiddingContext, Seat, SystemContext, Hand, Vulnerability,
    create_sayc_one_diamond_one_heart_opener_rebid_engine,
)

def ctx(hand):
    a=Auction(Seat.NORTH)
    for c in ("1D","P","1H","P"):
        a.add(c)
    return BiddingContext.create(
        hand=Hand.parse(hand), seat=Seat.NORTH, auction=a,
        system=SystemContext("SAYC"), vulnerability=Vulnerability.NONE
    )

def bid(hand):
    return create_sayc_one_diamond_one_heart_opener_rebid_engine().evaluate(ctx(hand)).recommended_call

def test_four_card_heart_support_raises_two_hearts():
    assert bid("AK2.QJ84.AK76.54").serialize()=="2H"

def test_four_spades_are_shown_after_excluding_heart_support():
    assert bid("AQ72.K8.KJ76.Q54").serialize()=="1S"

def test_four_clubs_are_shown_when_no_four_spades():
    assert bid("AQ2.K8.KJ76.QJ54").serialize()=="2C"

def test_spades_precede_clubs_in_conservative_second_suit_slice():
    assert bid("AQ72.K8.KJ7.QJ54").serialize()=="1S"

def test_balanced_12_14_without_support_or_second_suit_rebids_1nt():
    assert bid("AQ2.K83.QJ76.J54").serialize()=="1NT"

def test_balanced_18_19_without_support_or_second_suit_rebids_2nt():
    assert bid("AQ2.K83.AJ76.KQ4").serialize()=="2NT"

def test_six_diamonds_rebid_when_higher_priority_branches_are_absent():
    assert bid("AQ2.K8.KQJ876.54").serialize()=="2D"

def test_six_diamonds_do_not_bypass_four_spades():
    assert bid("AQ72.K8.KQJ876.5").serialize()=="1S"
