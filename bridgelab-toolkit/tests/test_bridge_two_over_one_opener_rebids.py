import pytest

from bridge import (
    Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability,
)
from bridge.two_over_one_opener_rebids import create_sayc_two_over_one_opener_rebid_engine


def context(calls, hand, *, treatment="game_force", system="SAYC"):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, {"two_over_one": treatment}),
    )


def test_one_spade_two_club_two_diamond():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.KQJ4.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert result.recommended_call.serialize() == "2D"


def test_two_diamond_requires_four_diamonds():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.KQ3.JT8")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_two_diamond_abstains_with_competing_four_card_hearts():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.KQJ4.82.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_one_heart_two_diamond_two_spade():
    ctx = context(("1H", "P", "2D", "P"), "KQJ4.AKQ97.82.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert result.recommended_call.serialize() == "2S"


def test_two_spade_requires_four_spades():
    ctx = context(("1H", "P", "2D", "P"), "KQ3.AKQ97.82.JT8")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_two_spade_requires_five_hearts():
    ctx = context(("1H", "P", "2D", "P"), "KQJ4.AKQ9.82.JT8")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_requires_explicit_game_force_treatment():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.KQJ4.32", treatment="natural")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_requires_exact_uncontested_auction():
    ctx = context(("1S", "P", "2C", "2H"), "AKQ97.82.KQJ4.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_non_sayc_abstains():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.KQJ4.32", system="Acol")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert not result.has_recommendation


def test_source_trace_uses_opener_rebid_priority():
    ctx = context(("1S", "P", "2C", "P"), "AKQ97.82.KQJ4.32")
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(ctx)
    assert result.recommended is not None
    headings = {source.heading for source in result.recommended.sources}
    assert "Opener's Rebids" in headings
    assert "Priority 1 — Show a Second Suit" in headings


def test_registry_contains_controlled_opener_rebid_rules():
    engine = create_sayc_two_over_one_opener_rebid_engine()
    assert len(engine.rules) == 4
