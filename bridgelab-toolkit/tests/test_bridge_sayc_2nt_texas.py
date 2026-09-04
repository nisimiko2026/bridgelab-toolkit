from bridge import Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc_2nt_texas import create_sayc_two_notrump_texas_accept_engine
from bridge.sayc_route_configuration import create_standard_sayc_router

HAND="AQ3.KJ4.AQ76.KJ3"

def ctx(calls, system="SAYC"):
    return BiddingContext.create(
        hand=Hand.parse(HAND), auction=Auction(Seat.NORTH,calls),
        vulnerability=Vulnerability.NONE, system=SystemContext(system))

def bid(calls, system="SAYC"):
    d=create_sayc_two_notrump_texas_accept_engine().evaluate(ctx(calls,system))
    return None if d.recommended_call is None else d.recommended_call.serialize()

def test_accepts_4d_to_4h():
    assert bid(("2NT","P","4D","P")) == "4H"

def test_accepts_4h_to_4s():
    assert bid(("2NT","P","4H","P")) == "4S"

def test_wrong_auction_abstains():
    assert bid(("2NT","P")) is None

def test_non_sayc_abstains():
    assert bid(("2NT","P","4D","P"),"Other") is None

def test_router_4d_route():
    m=create_standard_sayc_router().match(ctx(("2NT","P","4D","P")))
    assert m is not None and m.route_id=="sayc.opener.2nt.texas.4d"

def test_router_4h_route():
    m=create_standard_sayc_router().match(ctx(("2NT","P","4H","P")))
    assert m is not None and m.route_id=="sayc.opener.2nt.texas.4h"
