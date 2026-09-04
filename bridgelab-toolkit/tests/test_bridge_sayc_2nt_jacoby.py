from bridge import Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc_2nt_jacoby import create_sayc_two_notrump_jacoby_accept_engine, create_sayc_two_notrump_jacoby_response_engine
from bridge.sayc_route_configuration import create_standard_sayc_router


def ctx(calls, hand):
    return BiddingContext.create(hand=Hand.parse(hand), auction=Auction(Seat.NORTH,calls), vulnerability=Vulnerability.NONE, system=SystemContext("SAYC"))


def call(engine, calls, hand):
    d=engine.evaluate(ctx(calls,hand))
    return None if d.recommended_call is None else d.recommended_call.serialize()


def test_heart_transfer_after_2nt():
    assert call(create_sayc_two_notrump_jacoby_response_engine(), ("2NT","P"), "32.KJ987.876.543") == "3D"

def test_spade_transfer_after_2nt():
    assert call(create_sayc_two_notrump_jacoby_response_engine(), ("2NT","P"), "KJ987.32.876.543") == "3H"

def test_transfer_has_no_hcp_floor():
    assert call(create_sayc_two_notrump_jacoby_response_engine(), ("2NT","P"), "32.98765.876.543") == "3D"

def test_four_card_major_does_not_transfer():
    assert call(create_sayc_two_notrump_jacoby_response_engine(), ("2NT","P"), "32.KJ98.8764.543") is None

def test_both_five_card_majors_abstain():
    assert call(create_sayc_two_notrump_jacoby_response_engine(), ("2NT","P"), "KJ987.QJ987.8.43") is None

def test_opener_accepts_heart_transfer():
    assert call(create_sayc_two_notrump_jacoby_accept_engine(), ("2NT","P","3D","P"), "AQ3.KJ4.AQ76.KJ3") == "3H"

def test_opener_accepts_spade_transfer():
    assert call(create_sayc_two_notrump_jacoby_accept_engine(), ("2NT","P","3H","P"), "AQ3.KJ4.AQ76.KJ3") == "3S"

def test_router_has_2nt_response_route():
    assert create_standard_sayc_router().match(ctx(("2NT","P"), "32.KJ987.876.543")).route_id == "sayc.response.2nt.jacoby"

def test_router_has_both_accept_routes():
    r=create_standard_sayc_router()
    assert r.match(ctx(("2NT","P","3D","P"), "AQ3.KJ4.AQ76.KJ3")).route_id == "sayc.opener.2nt.jacoby.3d"
    assert r.match(ctx(("2NT","P","3H","P"), "AQ3.KJ4.AQ76.KJ3")).route_id == "sayc.opener.2nt.jacoby.3h"
