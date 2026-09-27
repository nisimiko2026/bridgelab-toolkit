"""Focused PT-1 structural and probability invariants."""

import ast
from fractions import Fraction
from pathlib import Path

import pytest

from bridge.deals import Deal
from bridge.models import Rank, Seat, Suit
from bridge.playing_trick_calibration import (
    CrossruffStage, ShortnessKind, TRUMP_STRUCTURES,
    analyze_case, generate_conditioned_case, run_calibration, shortness_activation_round,
)
from bridge.probability_questions import VacantPlacesQuestion
from bridge.probability_values import ProbabilityValue
from bridge.vacant_places import oriented_trump_break


def test_activation_rounds():
    assert [shortness_activation_round(n) for n in (0, 1, 2, 3)] == [0, 1, 2, None]


def test_distinct_structures_and_equal_trumps():
    assert len(TRUMP_STRUCTURES) == 8
    assert {(6, 3), (5, 4)} <= set(TRUMP_STRUCTURES)
    assert {(7, 3), (6, 4), (5, 5)} <= set(TRUMP_STRUCTURES)
    for structure in TRUMP_STRUCTURES:
        kind = (ShortnessKind.EQUAL_HAND_SINGLETON if structure == (5, 5)
                else ShortnessKind.SHORT_HAND_SINGLETON)
        case = generate_conditioned_case(12, structure, kind)
        assert case.trump_structure == structure
        assert case.partnership_trumps == sum(structure)
        assert case.outstanding_trumps == 13 - sum(structure)
        assert sum(case.defender_trump_split) == case.outstanding_trumps
        assert case.equal_trumps == (structure == (5, 5))
        assert case.short_trump_hand is (None if structure == (5, 5) else Seat.SOUTH)
    with pytest.raises(ValueError, match="equal trump lengths"):
        generate_conditioned_case(12, (5, 5), ShortnessKind.SHORT_HAND_SINGLETON)
    orientations = {generate_conditioned_case(seed, (5, 5), ShortnessKind.EQUAL_HAND_SINGLETON)
                    .short_suits[0].hand for seed in range(30)}
    assert orientations == {Seat.NORTH, Seat.SOUTH}


def test_singleton_location_is_distinct():
    short = generate_conditioned_case(22, (6, 3), ShortnessKind.SHORT_HAND_SINGLETON)
    long = generate_conditioned_case(22, (6, 3), ShortnessKind.LONG_HAND_SINGLETON)
    assert short.short_suits[0].hand is Seat.SOUTH
    assert long.short_suits[0].hand is Seat.NORTH
    assert short.shortness_kind != long.shortness_kind


def test_natural_top_winners_excluded_from_ruffable_losers():
    high = low = None
    for seed in range(1500):
        case = generate_conditioned_case(seed, (6, 3), ShortnessKind.SHORT_HAND_SINGLETON)
        item = case.short_suits[0]
        if item.opposite_length >= 4 and item.certain_top_rank_winners >= 2:
            high = item
        if item.opposite_length >= 4 and item.certain_top_rank_winners == 0:
            low = item
        if high and low and high.opposite_length == low.opposite_length:
            break
    assert high is not None and low is not None
    assert high.ruffable_losers < high.opposite_length - high.activation_round
    assert low.ruffable_losers == low.opposite_length - low.activation_round


def test_no_unmeasured_ruff_receives_a_trick_credit():
    case = generate_conditioned_case(43, (5, 3), ShortnessKind.SHORT_HAND_SINGLETON)
    assert case.marginal_ruff_value is None
    assert case.natural_playing_tricks is None
    assert case.double_dummy_tricks is None
    assert case.adjusted_playing_tricks is None
    assert case.short_hand_ruff_capacity == 3


def test_reciprocal_shortness_does_not_establish_crossruff():
    case = generate_conditioned_case(31, (6, 4), ShortnessKind.RECIPROCAL_SINGLETONS)
    assert len(case.short_suits) == 2
    assert case.short_suits[0].suit != case.short_suits[1].suit
    assert case.crossruff_stage in (CrossruffStage.INDEPENDENT_SHORTNESS,
                                    CrossruffStage.CROSSRUFF_AVAILABLE)
    assert case.crossruff_stage is not CrossruffStage.CROSSRUFF_ESTABLISHED
    assert case.crossruff_value is None


def test_mixed_shortness_can_label_void_plus_singleton_without_fake_value():
    for seed in range(1000):
        case = generate_conditioned_case(seed, (6, 3), ShortnessKind.SHORT_HAND_SINGLETON)
        deal = Deal.parse(case.deal_id, seed=case.deal_seed)
        void_suit = next((suit for suit in Suit if suit not in (Suit.SPADES, case.short_suits[0].suit)
                          and deal.hand(Seat.NORTH).length(suit) == 0), None)
        if void_suit is not None:
            mixed = analyze_case(deal, Suit.SPADES, ShortnessKind.MIXED_SHORTNESS,
                                 ((Seat.SOUTH, case.short_suits[0].suit), (Seat.NORTH, void_suit)))
            assert sorted(item.activation_round for item in mixed.short_suits) == [0, 1]
            assert mixed.crossruff_value is None
            with pytest.raises(ValueError, match="reciprocal-singleton"):
                analyze_case(deal, Suit.SPADES, ShortnessKind.RECIPROCAL_SINGLETONS,
                             ((Seat.SOUTH, case.short_suits[0].suit), (Seat.NORTH, void_suit)))
            break
    else:
        pytest.fail("no void-plus-singleton fixture found")


def test_seed_replays_exact_records():
    first = run_calibration((6, 3), ShortnessKind.SHORT_HAND_SINGLETON,
                            seed=991, accepted_target=6)
    second = run_calibration((6, 3), ShortnessKind.SHORT_HAND_SINGLETON,
                             seed=991, accepted_target=6)
    assert first == second
    assert len({case.deal_id for case in first.records}) == 6


def test_rejections_do_not_count_as_accepted():
    batch = run_calibration((5, 4), ShortnessKind.SHORT_HAND_SINGLETON,
                            seed=101, accepted_target=5,
                            accept=lambda case: case.deal_seed % 2 == 0)
    assert batch.generated == 10
    assert batch.accepted == len(batch.records) == 5
    assert all(case.deal_seed % 2 == 0 for case in batch.records)


def test_baseline_shortness_does_not_change_unconditional_break():
    question = VacantPlacesQuestion("trump", Suit.SPADES, (Seat.EAST, Seat.WEST))
    probabilities = oriented_trump_break(question, 4)
    assert sum((item.probability.as_fraction() for item in probabilities), Fraction()) == 1
    assert [item.first_trumps for item in probabilities] == list(range(5))
    assert probabilities[2].probability.as_fraction() == Fraction(78 * 78, 14950)
    for seed in (1, 2, 3):
        case = generate_conditioned_case(seed, (6, 3), ShortnessKind.SHORT_HAND_SINGLETON)
        assert case.outstanding_trumps == 4
        assert oriented_trump_break(question, case.outstanding_trumps) == probabilities


def test_defender_specific_lengths_shift_oriented_probabilities():
    question = VacantPlacesQuestion("trump", Suit.SPADES, (Seat.EAST, Seat.WEST))
    baseline = oriented_trump_break(question, 4)
    conditioned = oriented_trump_break(
        question, 4, side_suit=Suit.HEARTS,
        side_length_mixture=((6, 1, ProbabilityValue(1, 1)),))
    assert conditioned[0].first_defender is Seat.EAST
    assert conditioned[0].second_defender is Seat.WEST
    assert conditioned[0].probability > baseline[0].probability
    assert conditioned[4].probability < baseline[4].probability
    assert conditioned[1].probability != conditioned[3].probability


def test_uncertain_side_length_is_mixed_not_coerced_to_five():
    question = VacantPlacesQuestion("trump", Suit.SPADES, (Seat.EAST, Seat.WEST))
    five = oriented_trump_break(question, 4, side_suit=Suit.HEARTS,
                                side_length_mixture=((5, 1, ProbabilityValue(1, 1)),))
    six = oriented_trump_break(question, 4, side_suit=Suit.HEARTS,
                               side_length_mixture=((6, 1, ProbabilityValue(1, 1)),))
    mixed = oriented_trump_break(question, 4, side_suit=Suit.HEARTS,
                                 side_length_mixture=((5, 1, ProbabilityValue(1, 2)),
                                                      (6, 1, ProbabilityValue(1, 2))))
    assert mixed[0].probability.as_fraction() == (
        five[0].probability.as_fraction() + six[0].probability.as_fraction()) / 2


def test_new_general_modules_do_not_import_bidding_or_profiles():
    bridge_dir = Path(__file__).resolve().parents[1] / "bridge"
    allowed = {"deals", "evaluation", "models", "probability_questions", "probability_values"}
    for name in ("playing_trick_calibration.py", "vacant_places.py"):
        tree = ast.parse((bridge_dir / name).read_text(encoding="utf-8"))
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                   and node.level == 1}
        assert imports <= allowed


def test_production_router_remains_at_45_routes():
    from bridge import create_standard_sayc_router
    assert len(create_standard_sayc_router().routes) == 45
