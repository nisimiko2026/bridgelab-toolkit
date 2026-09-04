from bridge import Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc_1nt_stayman import create_sayc_one_notrump_stayman_opener_response_engine
from bridge.sayc_route_configuration import create_standard_sayc_router

def ctx(calls, hand, system="SAYC"):
    return BiddingContext.create(hand=Hand.parse(hand), auction=Auction(Seat.NORTH,calls), vulnerability=Vulnerability.NONE, system=SystemContext(system))

def bid(calls, hand):
    d=create_sayc_one_notrump_stayman_opener_response_engine().evaluate(ctx(calls,hand))
    return None if d.recommended_call is None else d.recommended_call.serialize()

def test_no_four_card_major_returns_2d():
    assert bid(("1NT","P","2C","P"), "AQ3.KJ4.AQ76.KJ3") == "2D"

def test_four_hearts_only_returns_2h():
    assert bid(("1NT","P","2C","P"), "AQ3.KJ74.AQ7.KJ3") == "2H"

def test_four_spades_only_returns_2s():
    assert bid(("1NT","P","2C","P"), "AQ74.KJ3.AQ7.KJ3") == "2S"

def test_both_four_card_majors_abstain():
    assert bid(("1NT","P","2C","P"), "AQ74.KJ74.AQ7.KJ") is None

def test_wrong_auction_abstains():
    assert bid(("1NT","P"), "AQ3.KJ4.AQ76.KJ3") is None

def test_non_sayc_abstains():
    e=create_sayc_one_notrump_stayman_opener_response_engine()
    assert e.evaluate(ctx(("1NT","P","2C","P"), "AQ3.KJ4.AQ76.KJ3", "Other")).recommended_call is None

def test_router_has_stayman_opener_route():
    m=create_standard_sayc_router().match(ctx(("1NT","P","2C","P"), "AQ3.KJ4.AQ76.KJ3"))
    assert m is not None and m.route_id == "sayc.opener.1nt.stayman"
