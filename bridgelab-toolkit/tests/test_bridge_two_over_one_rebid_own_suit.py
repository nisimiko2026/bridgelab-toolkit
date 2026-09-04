from bridge import Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability
from bridge.two_over_one_opener_rebids import create_sayc_two_over_one_opener_rebid_engine


def context(calls, hand, *, treatment="game_force", system="SAYC"):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, {"two_over_one": treatment}),
    )


def test_one_spade_two_club_two_spade_with_six_spades():
    ctx = context(("1S", "P", "2C", "P"), "AKQJ97.82.KQ3.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert result.recommended_call.serialize() == "2S"


def test_two_spade_requires_six_spades_in_controlled_branch():
    ctx = context(("1S", "P", "2C", "P"), "AKQJ9.82.KQ3.JT8")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_priority_one_second_suit_blocks_two_spade():
    ctx = context(("1S", "P", "2C", "P"), "AKQJ97.2.KQJ4.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert result.recommended_call.serialize() == "2D"


def test_unresolved_four_card_heart_second_suit_blocks_two_spade():
    ctx = context(("1S", "P", "2C", "P"), "AKQJ97.KQJ4.2.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_priority_two_four_card_club_support_blocks_two_spade():
    ctx = context(("1S", "P", "2C", "P"), "AKQJ97.2.32.KQJ4")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert result.recommended_call.serialize() == "3C"


def test_two_spade_requires_explicit_game_force():
    ctx = context(("1S", "P", "2C", "P"), "AKQJ97.82.KQ3.32", treatment="natural")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_two_spade_rejects_interference():
    ctx = context(("1S", "P", "2C", "2H"), "AKQJ97.82.KQ3.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_two_spade_source_trace_contains_priority_three():
    ctx = context(("1S", "P", "2C", "P"), "AKQJ97.82.KQ3.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    headings = {source.heading for source in result.recommended.sources}
    assert "Priority 3 — Rebid Own Suit" in headings
    assert "Priority 1 — Show a Second Suit" in headings
    assert "Priority 2 — Support Responder" in headings


def test_engine_now_contains_four_controlled_opener_rebid_rules():
    engine = create_sayc_two_over_one_opener_rebid_engine()
    assert len(engine.rules) == 4
