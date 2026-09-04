from bridge import (
    Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability,
    assess_one_heart_two_diamond_balanced_rebid,
)
from bridge.two_over_one_opener_rebids import create_sayc_two_over_one_opener_rebid_engine


def context(hand, *, calls=("1H", "P", "2D", "P"), treatment="game_force", system="SAYC"):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, {"two_over_one": treatment}),
    )


def test_balanced_shape_is_detected_but_not_executable():
    assessment = assess_one_heart_two_diamond_balanced_rebid(
        context("KQ3.AKQ97.QJ2.32")
    )
    assert assessment.exact_auction
    assert assessment.game_force_configured
    assert assessment.balanced
    assert not assessment.strength_contract_known
    assert not assessment.executable


def test_strength_contract_remains_unknown_even_with_high_hcp():
    assessment = assess_one_heart_two_diamond_balanced_rebid(
        context("AKQ.AKQ97.KJ2.32")
    )
    assert not assessment.strength_contract_known
    assert not assessment.executable


def test_strength_contract_remains_unknown_even_with_lower_hcp():
    assessment = assess_one_heart_two_diamond_balanced_rebid(
        context("KQ3.KQJ97.QJ2.32")
    )
    assert not assessment.strength_contract_known
    assert not assessment.executable


def test_unbalanced_hand_fails_shape_evidence():
    assessment = assess_one_heart_two_diamond_balanced_rebid(
        context("KQ3.AKQ97.QJ32.2")
    )
    assert not assessment.balanced
    assert not assessment.executable


def test_non_game_force_configuration_is_not_executable():
    assessment = assess_one_heart_two_diamond_balanced_rebid(
        context("KQ3.AKQ97.QJ2.32", treatment="natural")
    )
    assert not assessment.game_force_configured
    assert not assessment.executable


def test_wrong_auction_is_not_exact():
    assessment = assess_one_heart_two_diamond_balanced_rebid(
        context("KQ3.AKQ97.QJ2.32", calls=("1H", "P", "2C", "P"))
    )
    assert not assessment.exact_auction


def test_non_sayc_is_not_exact_scope():
    assessment = assess_one_heart_two_diamond_balanced_rebid(
        context("KQ3.AKQ97.QJ2.32", system="Acol")
    )
    assert not assessment.exact_auction


def test_source_trace_records_both_canonical_headings():
    assessment = assess_one_heart_two_diamond_balanced_rebid(
        context("KQ3.AKQ97.QJ2.32")
    )
    headings = {source.heading for source in assessment.sources}
    assert "Opener's First Responsibility" in headings
    assert "Priority 4 — Balanced Rebids" in headings


def test_no_production_two_notrump_recommendation_is_added():
    result = create_sayc_two_over_one_opener_rebid_engine().evaluate(
        context("KQ3.AKQ97.QJ2.32")
    )
    assert not result.has_recommendation
