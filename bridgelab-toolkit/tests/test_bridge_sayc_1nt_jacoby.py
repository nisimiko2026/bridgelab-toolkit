from bridge import Auction,BiddingContext,Hand,Seat,SystemContext,Vulnerability
from bridge.sayc_1nt_jacoby import *
from bridge.sayc_route_configuration import create_standard_sayc_router
def c(hand,calls,system="SAYC"): return BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,calls),vulnerability=Vulnerability.NONE,system=SystemContext(system))
def r(e,x):
 d=e.evaluate(x); return None if d.recommended_call is None else d.recommended_call.serialize()
def test_h(): assert r(create_sayc_one_notrump_jacoby_response_engine(),c("32.AQJ76.K43.872",("1NT","P")))=="2D"
def test_s(): assert r(create_sayc_one_notrump_jacoby_response_engine(),c("AQJ76.32.K43.872",("1NT","P")))=="2H"
def test_both(): assert r(create_sayc_one_notrump_jacoby_response_engine(),c("AQJ76.KQJ76.43.2",("1NT","P"))) is None
def test_none(): assert r(create_sayc_one_notrump_jacoby_response_engine(),c("AQ76.KJ43.872.32",("1NT","P"))) is None
def test_accept_h(): assert r(create_sayc_one_notrump_jacoby_accept_engine(),c("AQ3.KJ4.AQ76.KJ3",("1NT","P","2D","P")))=="2H"
def test_accept_s(): assert r(create_sayc_one_notrump_jacoby_accept_engine(),c("AQ3.KJ4.AQ76.KJ3",("1NT","P","2H","P")))=="2S"
def test_other_system(): assert r(create_sayc_one_notrump_jacoby_response_engine(),c("32.AQJ76.K43.872",("1NT","P"),"Other")) is None
def test_route_response(): assert create_standard_sayc_router().match(c("32.AQJ76.K43.872",("1NT","P"))).route_id=="sayc.response.1nt.jacoby"
def test_route_d(): assert create_standard_sayc_router().match(c("AQ3.KJ4.AQ76.KJ3",("1NT","P","2D","P"))).route_id=="sayc.opener.1nt.jacoby.2d"
def test_route_h(): assert create_standard_sayc_router().match(c("AQ3.KJ4.AQ76.KJ3",("1NT","P","2H","P"))).route_id=="sayc.opener.1nt.jacoby.2h"
