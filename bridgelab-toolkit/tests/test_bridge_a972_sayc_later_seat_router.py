from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router

def ctx(calls, hand):
    return BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,calls),
        vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",{}))

def call_of(router,calls,hand):
    r=router.evaluate(ctx(calls,hand))
    return None if r.recommended_call is None else r.recommended_call.serialize()

def test_route_count_47():
    assert len(create_standard_sayc_router().routes)==47

def test_exact_route_ids():
    r=create_standard_sayc_router()
    assert r.match(ctx(("P","P"),"T9843.AKJ32.7.65")).route_id=="sayc.opening.later-seat.third"
    assert r.match(ctx(("P","P","P"),"AK632.JT865.J.T6")).route_id=="sayc.opening.later-seat.fourth"

def test_three_approved_witnesses():
    r=create_standard_sayc_router()
    assert call_of(r,("P","P"),"T9843.AKJ32.7.65")=="1S"
    assert call_of(r,("P","P"),"AQ987.QJ974.-.862")=="1S"
    assert call_of(r,("P","P","P"),"AK632.JT865.J.T6")=="1S"

def test_nonqualifying_abstains():
    assert call_of(create_standard_sayc_router(),("P","P"),"JT753.K9742.6.AT") is None

def test_out_of_scope_abstains():
    assert call_of(create_standard_sayc_router(),("P","P"),"AKQJ9.876.54.432") is None

def test_original_opening_route_unchanged():
    m=create_standard_sayc_router().match(ctx((),"AKQJ9.KQ3.JT8.32"))
    assert m.route_id=="sayc.opening"

def test_one_pass_still_no_route():
    assert create_standard_sayc_router().match(ctx(("P",),"T9843.AKJ32.7.65")) is None

def test_later_routes_use_a971_adapter():
    r=create_standard_sayc_router()
    for calls,hand in [(("P","P"),"T9843.AKJ32.7.65"),(("P","P","P"),"AK632.JT865.J.T6")]:
        m=r.match(ctx(calls,hand))
        assert type(m.engine.rules[0]).__module__=="bridge.sayc_later_seat_opening"
