from bridge import Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability
from bridge.two_over_one_opener_rebids import create_sayc_two_over_one_opener_rebid_engine


def context(calls, hand, *, treatment="game_force", system="SAYC"):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, {"two_over_one": treatment}),
    )


def test_one_spade_two_club_three_club_with_four_card_support():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.32.KQJ4")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert result.recommended_call.serialize() == "3C"


def test_three_club_requires_four_clubs_in_controlled_slice():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.KQ2.32.JT8")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_second_suit_priority_blocks_three_club_when_four_diamonds():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.KQJ4.A2")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert result.recommended_call.serialize() == "2D"


def test_unresolved_heart_second_suit_blocks_three_club():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.KQJ4.2.A32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_three_club_requires_explicit_game_force():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.32.KQJ4", treatment="natural")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_three_club_rejects_interference():
    ctx = context(("1S", "P", "2C", "2H"), "AKQ97.82.32.KQJ4")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_three_club_source_trace_contains_support_priority():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.32.KQJ4")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    headings = {source.heading for source in result.recommended.sources}
    assert "Priority 2 — Support Responder" in headings
    assert "Priority 1 — Show a Second Suit" in headings


def test_one_heart_two_diamond_three_diamond_remains_unimplemented():
    # The canonical 2/1 source says only "Diamond support" for 3♦ and does not
    # state a deterministic support-card count. BridgeLab therefore abstains.
    ctx = context(("1H", "P", "2D", "P"), "82.AKQ97.KQJ4.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_engine_now_contains_three_controlled_opener_rebid_rules():
    engine = create_sayc_two_over_one_opener_rebid_engine()
    assert len(engine.rules) == 4
