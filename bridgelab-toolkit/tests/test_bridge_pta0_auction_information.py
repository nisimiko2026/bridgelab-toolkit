"""Focused, system-neutral PT-A0 auction information tests."""

from __future__ import annotations

import ast
import inspect
import random

import pytest

import bridge.auction_information as module
from bridge.auction import Auction
from bridge.auction_information import (
    AuctionConstraintUpdate,
    AuctionInformationState,
    Certainty,
    ConstraintProvenance,
    DiscreteDistribution,
    EvidenceOrigin,
    FitStatus,
    InformationStatus,
    NumericRange,
    RangeEvidence,
    ShapeEvidence,
    ShortnessKind,
    snapshots,
)
from bridge.deals import Deal, full_deck, generate_deal
from bridge.models import Hand, Seat, Suit
from bridge.probability_values import ProbabilityValue


OWN = Hand.parse("AKQ42.9876.3.J76")  # Five spades, singleton diamond.


def source(origin=EvidenceOrigin.PROFILE_INTERPRETATION, *, call_index=None, label="test"):
    return ConstraintProvenance(origin, label, call_index, "general-test")


def length(seat, suit, low, high=13, *, certainty=Certainty.GUARANTEED,
           origin=EvidenceOrigin.PROFILE_INTERPRETATION, call_index=None, label="length"):
    return AuctionConstraintUpdate(seat, suit_lengths=((suit, RangeEvidence(
        NumericRange(low, high), certainty, source(origin, call_index=call_index, label=label))),))


def hcp(seat, low, high, *, label="HCP"):
    return AuctionConstraintUpdate(seat, hcp=RangeEvidence(
        NumericRange(low, high), Certainty.GUARANTEED, source(label=label)))


def start():
    return AuctionInformationState.start(Seat.SOUTH, OWN, Seat.SOUTH)


def test_own_hand_exact_and_immutable():
    state = start()
    assert state.own_hand is OWN
    assert state.own_hand.length(Suit.SPADES) == 5
    assert state.own_hand.length(Suit.DIAMONDS) == 1
    with pytest.raises(Exception):
        state.own_hand = Hand.parse("AKQ.JT9.876.5432")


def test_unknown_partner_has_no_promised_length_or_fit():
    state = start()
    assert state.for_seat(Seat.NORTH).suit_evidence(Suit.SPADES) == ()
    assert state.fit(Suit.SPADES).status is FitStatus.NO_FIT_EVIDENCE
    assert state.for_seat(Seat.NORTH).suit_range(Suit.SPADES) == NumericRange(0, 8)


def test_guaranteed_suit_minimum():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 3),))
    assert state.for_seat(Seat.NORTH).suit_range(Suit.SPADES).minimum == 3


def test_hcp_ranges_intersect():
    state = start().with_updates((hcp(Seat.NORTH, 10, 12, label="first"),
                                  hcp(Seat.NORTH, 11, 20, label="second")))
    assert state.for_seat(Seat.NORTH).hcp == NumericRange(11, 12)


def test_suit_ranges_intersect():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 4, 8, label="first"),
                                  length(Seat.NORTH, Suit.SPADES, 0, 5, label="second")))
    assert state.for_seat(Seat.NORTH).suit_range(Suit.SPADES) == NumericRange(4, 5)


def test_conflicting_suit_evidence_keeps_both_sources():
    state = start().with_updates((length(Seat.NORTH, Suit.HEARTS, 5, 13, label="five"),
                                  length(Seat.NORTH, Suit.HEARTS, 0, 4, label="four")))
    assert state.status is InformationStatus.CONTRADICTORY
    conflict = next(c for c in state.conflicts if c.subject == "H length")
    assert {p.reference for p in conflict.sources} >= {"five", "four"}


def test_hcp_contradiction_is_explicit():
    state = start().with_updates((hcp(Seat.NORTH, 12, 14), hcp(Seat.NORTH, 0, 11)))
    assert any(c.subject == "HCP" for c in state.conflicts)
    assert state.for_seat(Seat.NORTH).hcp is None


def test_provenance_preserved_per_constraint():
    update = length(Seat.NORTH, Suit.SPADES, 3, label="partner supports spades")
    state = start().with_updates((update,))
    assert state.for_seat(Seat.NORTH).suit_evidence(Suit.SPADES)[0].provenance == update.provenance[0]


def test_derived_shape_bound_explains_all_contributing_sources():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 5, label="spade promise"),
                                  length(Seat.NORTH, Suit.HEARTS, 4, label="heart promise")))
    sources = state.for_seat(Seat.NORTH).suit_provenance(Suit.DIAMONDS)
    assert {item.reference for item in sources} >= {"spade promise", "heart promise"}
    assert any(item.origin is EvidenceOrigin.DERIVED_ARITHMETIC for item in sources)


def test_three_partner_spades_establishes_eight_card_fit():
    fit = start().with_updates((length(Seat.NORTH, Suit.SPADES, 3),)).fit(Suit.SPADES)
    assert fit.total.minimum == 8
    assert fit.status is FitStatus.KNOWN_8_PLUS_FIT


def test_four_partner_spades_establishes_nine_card_fit():
    fit = start().with_updates((length(Seat.NORTH, Suit.SPADES, 4),)).fit(Suit.SPADES)
    assert fit.total.minimum == 9
    assert fit.status is FitStatus.KNOWN_9_PLUS_FIT


def test_singleton_is_recorded_before_fit():
    diamond = next(s for s in start().own_shortness() if s.suit is Suit.DIAMONDS)
    assert (diamond.length, diamond.kind, diamond.certainty) == (1, ShortnessKind.SINGLETON, Certainty.EXACT)
    assert not diamond.fit_established


def test_fit_changes_relevance_not_physical_singleton():
    before = next(s for s in start().own_shortness() if s.suit is Suit.DIAMONDS)
    after = next(s for s in start().with_updates((length(Seat.NORTH, Suit.SPADES, 3),)).own_shortness()
                 if s.suit is Suit.DIAMONDS)
    assert (before.length, before.kind, before.provenance) == (after.length, after.kind, after.provenance)
    assert not before.fit_established and after.fit_established


def test_opponent_suit_evidence_remains_seat_specific():
    state = start().after_call("1S").after_call("2D", (length(
        Seat.WEST, Suit.DIAMONDS, 5, origin=EvidenceOrigin.OPPONENT_CALL,
        call_index=1, label="West diamond call"),))
    assert state.for_seat(Seat.WEST).suit_range(Suit.DIAMONDS).minimum == 5
    assert state.for_seat(Seat.EAST).suit_evidence(Suit.DIAMONDS) == ()
    diamond = next(s for s in state.own_shortness() if s.suit is Suit.DIAMONDS)
    assert diamond.opponent_location_evidence_available


def test_opponent_fit_keeps_left_and_right_distinct():
    state = start().with_updates((length(Seat.WEST, Suit.HEARTS, 5, 6),
                                  length(Seat.EAST, Suit.HEARTS, 3, 4)))
    fit = state.opponent_fit(Suit.HEARTS)
    assert fit.left_length == NumericRange(5, 6)
    assert fit.right_length == NumericRange(3, 4)
    assert fit.total == NumericRange(8, 9)
    assert fit.status is FitStatus.KNOWN_8_PLUS_FIT


def test_soft_evidence_does_not_narrow_hard_bounds():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 5, 6,
                                          certainty=Certainty.INFERRED),))
    assert state.for_seat(Seat.NORTH).suit_range(Suit.SPADES) == NumericRange(0, 8)
    assert state.fit(Suit.SPADES).status is FitStatus.NO_FIT_EVIDENCE
    assert state.for_seat(Seat.NORTH).suit_evidence(Suit.SPADES)[0].certainty is Certainty.INFERRED


def test_snapshots_after_each_call_are_distinct_and_cumulative():
    initial = start()
    states = snapshots(initial, (("1S", ()), ("P", ()),
        ("2S", (length(Seat.NORTH, Suit.SPADES, 3, origin=EvidenceOrigin.PARTNER_CALL,
                       call_index=2),)),
        ("P", (length(Seat.EAST, Suit.DIAMONDS, 4, origin=EvidenceOrigin.OPPONENT_CALL,
                      call_index=3),))))
    assert tuple(len(state.entries) for state in states) == (1, 2, 3, 4)
    assert initial.entries == ()
    assert states[1].fit(Suit.SPADES).status is FitStatus.NO_FIT_EVIDENCE
    assert states[2].fit(Suit.SPADES).status is FitStatus.KNOWN_8_PLUS_FIT
    assert states[3].for_seat(Seat.EAST).suit_range(Suit.DIAMONDS).minimum == 4


def test_guaranteed_bounds_narrow_monotonically():
    first = start().with_updates((length(Seat.NORTH, Suit.SPADES, 3, 5),))
    second = first.with_updates((length(Seat.NORTH, Suit.SPADES, 4, 8),))
    assert first.for_seat(Seat.NORTH).suit_range(Suit.SPADES) == NumericRange(3, 5)
    assert second.for_seat(Seat.NORTH).suit_range(Suit.SPADES) == NumericRange(4, 5)
    assert len(second.updates) == 2 and len(first.updates) == 1


def test_same_visible_information_same_state_despite_different_hidden_hands():
    first_deal = generate_deal(2026)
    own = first_deal.hand(Seat.SOUTH)
    hidden = [card for card in full_deck() if card not in own.cards]
    random.Random(29).shuffle(hidden)
    second_deal = Deal(2027, ((Seat.SOUTH, own),
                              (Seat.NORTH, Hand.from_cards(hidden[:13])),
                              (Seat.EAST, Hand.from_cards(hidden[13:26])),
                              (Seat.WEST, Hand.from_cards(hidden[26:]))))
    assert all(first_deal.hand(seat) != second_deal.hand(seat) for seat in Seat if seat is not Seat.SOUTH)
    auction = Auction(Seat.SOUTH, ("1S", "P", "2S"))
    updates = (length(Seat.NORTH, Suit.SPADES, 3, origin=EvidenceOrigin.PARTNER_CALL,
                      call_index=2),)
    first = AuctionInformationState.from_auction(Seat.SOUTH, first_deal.hand(Seat.SOUTH), auction, updates)
    second = AuctionInformationState.from_auction(Seat.SOUTH, second_deal.hand(Seat.SOUTH), auction, updates)
    assert first == second
    assert first.fit(Suit.SPADES) == second.fit(Suit.SPADES)
    assert first.own_shortness() == second.own_shortness()
    assert first.conflicts == second.conflicts
    for seat in first.partner, *first.opponents:
        assert first.for_seat(seat) == second.for_seat(seat)
    for suit in Suit:
        assert first.opponent_fit(suit) == second.opponent_fit(suit)


def test_no_dds_or_full_deal_import_in_production_module():
    imports = _module_imports()
    assert not any("dds" in name or "endplay" in name or "deal_analysis" in name or "deals" in name
                   for name in imports)
    assert "Deal" not in vars(module)


def test_no_bidding_system_specific_import():
    imports = _module_imports()
    assert not any(any(term in name for term in ("sayc", "two_over_one", "acol", "precision", "blue_club", "bidding_rules"))
                   for name in imports)


def test_no_partnership_specific_import():
    assert not any("nisim" in name or "partnership" in name for name in _module_imports())


def test_no_playing_trick_value_is_produced():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 3),))
    names = set(state.__dataclass_fields__) | set(state.fit(Suit.SPADES).__dataclass_fields__)
    names |= set(state.own_shortness()[0].__dataclass_fields__)
    assert not names.intersection({"npt", "srv", "crv", "erv", "apt", "shortness_bonus", "distribution_points"})
    assert "playing_trick" not in inspect.getsource(module).lower()


def test_shape_arithmetic_derives_remaining_card_limit():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 5),
                                  length(Seat.NORTH, Suit.HEARTS, 4)))
    partner = state.for_seat(Seat.NORTH)
    assert partner.suit_range(Suit.DIAMONDS).maximum <= 4
    assert partner.suit_range(Suit.CLUBS).maximum <= 4


def test_impossible_13_card_shape_is_detected():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 5),
                                  length(Seat.NORTH, Suit.HEARTS, 5),
                                  length(Seat.NORTH, Suit.DIAMONDS, 4)))
    assert any(conflict.subject == "13-card shape" for conflict in state.conflicts)


def test_shape_restriction_can_force_shortness_without_guessing():
    shape = ShapeEvidence(((4, 4, 4, 1),), Certainty.GUARANTEED, source(label="shape"))
    state = start().with_updates((AuctionConstraintUpdate(Seat.NORTH, shapes=shape),))
    partner = state.for_seat(Seat.NORTH)
    assert partner.shortness_known(Suit.CLUBS, ShortnessKind.SINGLETON)
    assert not partner.shortness_known(Suit.DIAMONDS, ShortnessKind.SINGLETON)


def test_supplied_distribution_stays_probabilistic():
    probabilities = DiscreteDistribution(((0, ProbabilityValue(1, 4)),
                                          (1, ProbabilityValue(3, 4))))
    evidence = RangeEvidence(NumericRange(0, 1), Certainty.PROBABILISTIC,
                             source(label="supplied probability"), probabilities)
    state = start().with_updates((AuctionConstraintUpdate(Seat.NORTH, suit_lengths=((Suit.DIAMONDS, evidence),)),))
    assert state.for_seat(Seat.NORTH).suit_range(Suit.DIAMONDS).minimum == 0
    assert state.for_seat(Seat.NORTH).suit_evidence(Suit.DIAMONDS)[0].distribution == probabilities


def test_mutable_distribution_and_shape_inputs_are_rejected():
    with pytest.raises(TypeError):
        DiscreteDistribution([(0, ProbabilityValue(1, 1))])
    with pytest.raises(TypeError):
        ShapeEvidence([(4, 4, 4, 1)], Certainty.GUARANTEED, source())


def test_exact_evidence_cannot_claim_multiple_values():
    with pytest.raises(ValueError, match="exact range"):
        RangeEvidence(NumericRange(3, 4), Certainty.EXACT, source())
    with pytest.raises(ValueError, match="exact shape"):
        ShapeEvidence(((4, 4, 4, 1), (5, 3, 3, 2)), Certainty.EXACT, source())


def test_negative_inference_has_representation_but_no_automatic_rule():
    state = start().with_updates((length(Seat.NORTH, Suit.HEARTS, 0, 4,
                                          certainty=Certainty.INFERRED,
                                          origin=EvidenceOrigin.NEGATIVE_INFERENCE),))
    assert state.for_seat(Seat.NORTH).suit_range(Suit.HEARTS).maximum > 4
    assert state.for_seat(Seat.NORTH).suit_evidence(Suit.HEARTS)[0].provenance.origin is EvidenceOrigin.NEGATIVE_INFERENCE


def test_exact_unknown_seat_and_future_call_provenance_rejected():
    with pytest.raises(ValueError, match="exact unknown-seat"):
        start().with_updates((length(Seat.NORTH, Suit.SPADES, 3, 3,
                                          certainty=Certainty.EXACT),))
    with pytest.raises(ValueError, match="future call"):
        start().with_updates((length(Seat.NORTH, Suit.SPADES, 3,
                                          origin=EvidenceOrigin.PARTNER_CALL,
                                          call_index=0),))


def test_cross_seat_card_capacity_contradiction():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 5),
                                  length(Seat.WEST, Suit.SPADES, 4)))
    assert any(conflict.subject == "unseen S cards" for conflict in state.conflicts)


def test_cross_seat_conflict_names_shape_source():
    shape = ShapeEvidence(((5, 4, 3, 1),), Certainty.GUARANTEED, source(label="partner shape"))
    state = start().with_updates((AuctionConstraintUpdate(Seat.NORTH, shapes=shape),
                                  length(Seat.WEST, Suit.SPADES, 4, label="opponent spades")))
    conflict = next(c for c in state.conflicts if c.subject == "unseen S cards")
    assert {p.reference for p in conflict.sources} >= {"partner shape", "opponent spades"}


def _module_imports() -> tuple[str, ...]:
    tree = ast.parse(inspect.getsource(module))
    return tuple(node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)) + tuple(
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)


def test_complete_four_state_shortness_progression():
    first = start()
    second = first.with_updates((length(Seat.NORTH, Suit.SPADES, 3, label="support"),))
    third = second.with_updates((length(Seat.NORTH, Suit.SPADES, 4, label="more support"),))
    defender = length(Seat.WEST, Suit.DIAMONDS, 5, label="defender diamond evidence")
    fourth = third.with_updates((defender,))
    states = (first, second, third, fourth)
    assert [state.fit(Suit.SPADES).total.minimum for state in states] == [5, 8, 9, 9]
    shortness = [next(s for s in state.own_shortness() if s.suit is Suit.DIAMONDS)
                 for state in states]
    assert [s.fit_established for s in shortness] == [False, True, True, True]
    assert [s.opponent_location_evidence_available for s in shortness] == [False, False, False, True]
    assert all(s.length == 1 and s.certainty is Certainty.EXACT for s in shortness)
    assert len({s.provenance for s in shortness}) == 1
    assert fourth.for_seat(Seat.WEST).suit_evidence(Suit.DIAMONDS)[0].provenance == defender.provenance[0]
    assert [len(state.updates) for state in states] == [0, 1, 2, 3]
    for state in states:
        assert not any(hasattr(state, name) for name in ("erv", "npt", "srv", "crv", "apt"))


@pytest.mark.parametrize("perspective", tuple(Seat))
def test_all_perspectives_preserve_opponent_orientation(perspective):
    state = AuctionInformationState.start(perspective, OWN, perspective)
    left, right = perspective.next(), perspective.partner().next()
    state = state.after_call("1S").after_call("2D", (length(
        left, Suit.DIAMONDS, 5, origin=EvidenceOrigin.OPPONENT_CALL, call_index=1),))
    assert state.opponents == (left, right)
    assert state.entries[1].seat is left
    assert state.for_seat(left).suit_range(Suit.DIAMONDS).minimum == 5
    assert state.for_seat(right).suit_evidence(Suit.DIAMONDS) == ()


@pytest.mark.parametrize("certainty", (Certainty.INFERRED, Certainty.PROBABILISTIC))
def test_soft_single_value_never_becomes_guaranteed(certainty):
    distribution = DiscreteDistribution(((4, ProbabilityValue(1, 1)),)) if certainty is Certainty.PROBABILISTIC else None
    evidence = RangeEvidence(NumericRange(4, 4), certainty, source(), distribution)
    state = start().with_updates((AuctionConstraintUpdate(Seat.NORTH, suit_lengths=((Suit.SPADES, evidence),)),))
    assert state.fit(Suit.SPADES).status is FitStatus.NO_FIT_EVIDENCE
    assert state.for_seat(Seat.NORTH).suit_range(Suit.SPADES) == NumericRange(0, 8)
    assert state.for_seat(Seat.NORTH).suit_evidence(Suit.SPADES) == (evidence,)


def test_contradictory_state_cannot_establish_fit_or_activate_shortness():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 4),
                                  length(Seat.WEST, Suit.SPADES, 5)))
    assert state.status is InformationStatus.CONTRADICTORY
    assert state.fit(Suit.SPADES).status is FitStatus.CONTRADICTORY
    assert state.fit(Suit.SPADES).total is None
    assert state.opponent_fit(Suit.SPADES).status is FitStatus.CONTRADICTORY
    assert not any(s.fit_established for s in state.own_shortness())


def test_own_long_suit_alone_guarantees_partnership_total():
    state = AuctionInformationState.start(Seat.SOUTH, Hand.parse("AKQJT987.234.-.32"), Seat.SOUTH)
    assert state.fit(Suit.SPADES).status is FitStatus.KNOWN_8_PLUS_FIT
    diamond = next(s for s in state.own_shortness() if s.suit is Suit.DIAMONDS)
    assert diamond.kind is ShortnessKind.VOID and diamond.certainty is Certainty.EXACT


def test_impossible_fit_is_distinct_from_possible_fit():
    state = start().with_updates((length(Seat.NORTH, Suit.SPADES, 0, 2),))
    assert state.fit(Suit.SPADES).status is FitStatus.NO_POSSIBLE_FIT


def test_opponent_total_respects_available_cards_and_partner_evidence():
    assert start().opponent_fit(Suit.HEARTS).total == NumericRange(0, 9)
    state = start().with_updates((length(Seat.NORTH, Suit.HEARTS, 3, 4),))
    assert state.opponent_fit(Suit.HEARTS).total == NumericRange(5, 6)
    assert any(p.reference == "length" for p in state.opponent_fit(Suit.HEARTS).sources)


def test_cross_seat_hcp_contradiction_retains_sources():
    state = start().with_updates((hcp(Seat.NORTH, 20, 22, label="partner strength"),
                                  hcp(Seat.WEST, 20, 22, label="defender strength")))
    conflict = next(c for c in state.conflicts if c.subject == "unseen HCP")
    assert {p.reference for p in conflict.sources} >= {"partner strength", "defender strength"}


def test_auction_mutation_does_not_change_snapshot():
    auction = Auction(Seat.SOUTH, ("1S",))
    state = AuctionInformationState.from_auction(Seat.SOUTH, OWN, auction)
    auction.add("P")
    assert len(state.entries) == 1


def test_joint_shape_contradiction_detected_despite_overlapping_suit_extrema():
    shape = ShapeEvidence(((1, 3, 4, 5), (5, 3, 4, 1)), Certainty.GUARANTEED,
                          source(label="correlated shape alternatives"))
    state = start().with_updates(tuple(AuctionConstraintUpdate(seat, shapes=shape)
                                      for seat in (Seat.NORTH, Seat.WEST, Seat.EAST)))
    assert all(state.for_seat(seat).status is InformationStatus.CONSISTENT
               for seat in (Seat.NORTH, Seat.WEST, Seat.EAST))
    conflict = next(c for c in state.conflicts if c.subject == "joint unseen shapes")
    assert any(p.reference == "correlated shape alternatives" for p in conflict.sources)
    assert state.fit(Suit.SPADES).status is FitStatus.CONTRADICTORY
