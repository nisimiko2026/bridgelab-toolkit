from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.sayc_later_seat_opening import create_sayc_later_seat_opening_engine


def ctx(calls, hand, system="SAYC"):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, {}),
    )


def call_of(calls, hand, system="SAYC"):
    r = create_sayc_later_seat_opening_engine().evaluate(ctx(calls, hand, system))
    return None if r.recommended_call is None else r.recommended_call.serialize()


def test_seed_1534_shape_opens_1s_in_third_seat():
    assert call_of(("P","P"), "T9843.AKJ32.7.65") == "1S"


def test_seed_4949_shape_opens_1s_in_third_seat():
    assert call_of(("P","P"), "AQ987.QJ974.-.862") == "1S"


def test_seed_9577_shape_opens_1s_in_fourth_seat():
    assert call_of(("P","P","P"), "AK632.JT865.J.T6") == "1S"


def test_nonqualifying_equal_majors_abstains():
    assert call_of(("P","P"), "JT753.K9742.6.AT") is None


def test_wrong_auction_prefix_abstains():
    assert call_of((), "T9843.AKJ32.7.65") is None


def test_one_pass_is_not_later_seat_scope():
    assert call_of(("P",), "T9843.AKJ32.7.65") is None


def test_non_sayc_profile_isolated():
    assert call_of(("P","P"), "T9843.AKJ32.7.65", "2/1") is None


def test_fourth_seat_qualifying_hand_opens():
    assert call_of(("P","P","P"), "T9843.AKJ32.7.65") == "1S"


def test_rule20_qualifying_two_suited_hand_uses_a9_policy():
    # 10 HCP + 5 + 5 = Rule 20; higher equal suit is spades.
    assert call_of(("P","P"), "KQ987.AJ876.2.43") == "1S"


def test_out_of_scope_shape_abstains():
    assert call_of(("P","P"), "AKQJ9.876.54.432") is None
