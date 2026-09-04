from bridge import (
    Auction, BiddingContext, Hand, PolicyRegistry, Seat, SystemContext,
    Vulnerability, create_standard_sayc_router,
)


def ctx(calls,hand,options=None):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH,calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC",options or {}),
    )


def test_standard_router_has_seventeen_explicit_routes():
    router=create_standard_sayc_router()
    assert len(router.routes)==17


def test_opening_position_routes_to_opening_engine():
    router=create_standard_sayc_router()
    match=router.match(ctx((),"AKQJ9.KQ3.JT8.32"))
    assert match.route_id=="sayc.opening"


def test_one_club_response_position_routes():
    router=create_standard_sayc_router()
    assert router.match(ctx(("1C","P"),"KQJ9.82.QJ87.432")).route_id=="sayc.response.1c"


def test_one_diamond_response_combines_natural_and_notrump_rules():
    router=create_standard_sayc_router()
    match=router.match(ctx(("1D","P"),"KQJ9.82.QJ87.432"))
    ids={r.rule_id for r in match.engine.rules}
    assert any(".1d." in rid for rid in ids)
    assert any("2nt" in rid or "3nt" in rid for rid in ids)


def test_one_heart_response_combines_standard_one_nt_and_two_over_one():
    router=create_standard_sayc_router(PolicyRegistry())
    match=router.match(ctx(("1H","P"),"KQJ9.82.QJ87.432"))
    modules={type(r).__module__ for r in match.engine.rules}
    assert "bridge.sayc_1h_responses" in modules
    assert "bridge.sayc_major_one_notrump" in modules
    assert "bridge.two_over_one_responses" in modules


def test_one_spade_response_combines_standard_one_nt_and_two_over_one():
    router=create_standard_sayc_router(PolicyRegistry())
    match=router.match(ctx(("1S","P"),"82.KQJ9.QJ87.432"))
    modules={type(r).__module__ for r in match.engine.rules}
    assert "bridge.sayc_1s_responses" in modules
    assert "bridge.sayc_major_one_notrump" in modules
    assert "bridge.two_over_one_responses" in modules


def test_canonical_two_over_one_opener_rebid_routes():
    router=create_standard_sayc_router()
    expected={
        ("1H","P","2C","P"):"sayc.2over1.opener.1h.2c",
        ("1H","P","2D","P"):"sayc.2over1.opener.1h.2d",
        ("1S","P","2C","P"):"sayc.2over1.opener.1s.2c",
        ("1S","P","2D","P"):"sayc.2over1.opener.1s.2d",
    }
    for calls,route_id in expected.items():
        assert router.match(ctx(calls,"AKQJ9.KQ3.JT8.32",{"two_over_one":"game_force"})).route_id==route_id


def test_one_spade_two_heart_is_deliberately_not_routed_as_canonical_two_over_one():
    router=create_standard_sayc_router()
    assert router.match(ctx(("1S","P","2H","P"),"AKQJ9.KQ3.JT8.32",{"two_over_one":"game_force"})) is None


def test_competitive_response_position_is_unrouted():
    router=create_standard_sayc_router()
    assert router.match(ctx(("1C","1D"),"KQJ9.82.QJ87.432")) is None


def test_unsupported_later_auction_is_unrouted():
    router=create_standard_sayc_router()
    match=router.match(ctx(("1C","P","1H","P"),"AKQJ9.KQ3.JT8.32"))
    assert match is not None
    assert match.route_id=="sayc.opener.1c.1h"


def test_wrong_registry_type_is_rejected():
    try:
        create_standard_sayc_router(object())
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError")
