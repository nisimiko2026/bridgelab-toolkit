"""Distribution and isolation tests for exact conditional proposals."""
from fractions import Fraction
from math import comb, factorial, sqrt
import inspect
import random

import pytest

from bridge.auction_information import (
    AuctionConstraintUpdate, AuctionInformationState, Certainty, ConstraintProvenance,
    EvidenceOrigin, NumericRange, RangeEvidence, ShapeEvidence,
)
from bridge.conditional_hidden_hand import ConditionalSampler, ConditionalStatus, sample_conditional_hidden_hands
from bridge.deals import Deal, full_deck, generate_deal
from bridge.evaluation import high_card_points, SUIT_ORDER
from bridge.hidden_hand_probability import (
    EvidenceKey, Feature, LikelihoodRule, SamplingConfig, SamplingStatus, WeightingStatus,
    sample_hidden_hands, vacant_place_reference,
)
from bridge.models import Hand, Rank, Seat, Suit
from bridge.probability_values import ProbabilityValue

OWN = Hand.parse("AKQ42.9876.3.J76")
SOURCE = ConstraintProvenance(EvidenceOrigin.PROFILE_INTERPRETATION, "general synthetic constraint")


def state(updates=(), own=OWN, seat=Seat.SOUTH):
    return AuctionInformationState.start(seat, own, seat).with_updates(updates)


def length(seat, suit, low, high=13, certainty=Certainty.GUARANTEED):
    return AuctionConstraintUpdate(seat, suit_lengths=((suit, RangeEvidence(
        NumericRange(low, high), certainty, SOURCE)),))


def hcp(seat, low, high):
    return AuctionConstraintUpdate(seat, hcp=RangeEvidence(NumericRange(low, high), Certainty.GUARANTEED, SOURCE))


def shape(seat, alternatives):
    return AuctionConstraintUpdate(seat, shapes=ShapeEvidence(alternatives, Certainty.GUARANTEED, SOURCE))


@pytest.fixture(scope="module")
def baseline():
    return ConditionalSampler(state())


def sample(s, n=100, seed=19, budget=20000):
    return ConditionalSampler(s).sample(SamplingConfig(n, budget, seed))


def test_unconstrained_count_mass_equals_entire_uniform_deal_space(baseline):
    assert baseline.diagnostics.proposal_allocation_count == comb(39, 13) * comb(26, 13)
    assert baseline.diagnostics.residual_hcp_seats == ()


def test_every_feasible_matrix_has_correct_multinomial_mass(baseline):
    masses = baseline.count_matrix_masses()
    assert len(masses) == baseline.diagnostics.matrix_count
    for matrix, mass in masses:
        assert all(sum(row) == 13 for row in matrix)
        expected = 1
        for j, suit in enumerate(SUIT_ORDER):
            total = 13 - OWN.length(suit)
            assert sum(row[j] for row in matrix) == total
            expected *= factorial(total) // (
                factorial(matrix[0][j]) * factorial(matrix[1][j]) * factorial(matrix[2][j]))
        assert mass == expected


def test_deterministic_setup_reuse_and_full_result(baseline):
    config = SamplingConfig(80, 80, 18)
    a = baseline.sample(config)
    assert a == baseline.sample(config) == sample_conditional_hidden_hands(state(), config)
    assert a.model.information_state == state()
    assert a.model != baseline.sample(SamplingConfig(80, 80, 19)).model


@pytest.mark.parametrize("perspective", tuple(Seat))
def test_oriented_legal_partition(perspective):
    result = sample(state(seat=perspective)).model
    assert result.accepted == result.proposals == 100
    for possibility in result.samples:
        assert tuple(s for s, _ in possibility.hands) == (
            perspective.partner(), perspective.next(), perspective.partner().next())
        cards = list(OWN.cards)
        for _, hand in possibility.hands:
            assert len(hand.cards) == 13
            assert not set(hand.cards).intersection(OWN.cards)
            cards.extend(hand.cards)
        assert len(cards) == len(set(cards)) == 52
        assert set(cards) == set(full_deck())


def test_hidden_real_cards_cannot_affect_results():
    first = generate_deal(33)
    own = first.hand(Seat.SOUTH)
    cards = [card for card in full_deck() if card not in own.cards]
    random.Random(42).shuffle(cards)
    second = Deal(34, ((Seat.SOUTH, own), (Seat.NORTH, Hand.from_cards(cards[:13])),
                       (Seat.WEST, Hand.from_cards(cards[13:26])), (Seat.EAST, Hand.from_cards(cards[26:]))))
    assert all(first.hand(seat) != second.hand(seat) for seat in (Seat.NORTH, Seat.WEST, Seat.EAST))
    assert sample(state(own=first.hand(Seat.SOUTH))) == sample(state(own=second.hand(Seat.SOUTH)))


@pytest.mark.parametrize("low,high", ((3, 13), (4, 13), (4, 4), (8, 8)))
def test_length_conditioning_has_no_rejection(low, high):
    result = sample(state((length(Seat.NORTH, Suit.SPADES, low, high),))).model
    assert result.accepted == result.proposals == 100
    assert not result.rejections
    assert all(low <= s.hand(Seat.NORTH).length(Suit.SPADES) <= high for s in result.samples)


@pytest.mark.parametrize("seat", (Seat.NORTH, Seat.WEST, Seat.EAST))
def test_exact_hcp_conditioning_for_any_primary_seat(seat):
    result = sample(state((hcp(seat, 11, 11),)))
    assert result.diagnostics.primary_hcp_seat is seat
    assert result.model.proposals == result.model.accepted == 100
    assert all(high_card_points(s.hand(seat)) == 11 for s in result.model.samples)


def test_combined_constraints_exact_no_rejection():
    result = sample(state((length(Seat.NORTH, Suit.SPADES, 4), hcp(Seat.NORTH, 10, 12)))).model
    assert result.proposals == result.accepted == 100
    assert all(s.hand(Seat.NORTH).length(Suit.SPADES) >= 4
               and 10 <= high_card_points(s.hand(Seat.NORTH)) <= 12 for s in result.samples)


def test_allowed_shapes_have_correct_exact_mass():
    alternatives = ((4, 4, 4, 1), (5, 3, 3, 2))
    sampler = ConditionalSampler(state((shape(Seat.NORTH, alternatives),)))
    totals = {s: 0 for s in alternatives}
    for matrix, mass in sampler.count_matrix_masses():
        totals[matrix[0]] += mass
    for s in alternatives:
        expected = comb(26, 13)
        for suit, n in zip(SUIT_ORDER, s):
            expected *= comb(13 - OWN.length(suit), n)
        assert totals[s] == expected
    model = sampler.sample(SamplingConfig(100, 100, 9)).model
    assert set(v for v, _ in model.marginal(Seat.NORTH, Feature.SHAPE).outcomes) == set(alternatives)


def test_defender_specific_lengths_preserve_orientation():
    result = sample(state((length(Seat.WEST, Suit.DIAMONDS, 5, 5),
                           length(Seat.EAST, Suit.DIAMONDS, 3, 3)))).model
    assert result.accepted == result.proposals == 100
    assert all(s.hand(Seat.WEST).length(Suit.DIAMONDS) == 5
               and s.hand(Seat.EAST).length(Suit.DIAMONDS) == 3 for s in result.samples)


def test_contradictory_state_never_draws(monkeypatch):
    def forbidden(*args):
        raise AssertionError("RNG must not be created")
    monkeypatch.setattr("bridge.conditional_hidden_hand.random.Random", forbidden)
    result = sample(state((length(Seat.NORTH, Suit.SPADES, 5), length(Seat.WEST, Suit.SPADES, 4))))
    assert result.diagnostics.status is ConditionalStatus.CONTRADICTORY
    assert result.model.proposals == result.model.accepted == 0


def test_rank_shape_impossibility_detected_at_setup(monkeypatch):
    def forbidden(*args):
        raise AssertionError("infeasible space must not be sampled")
    monkeypatch.setattr("bridge.conditional_hidden_hand.random.Random", forbidden)
    own = Hand.parse("AKQ42.9876.-.J763")
    result = sample(state((hcp(Seat.NORTH, 20, 20), length(Seat.NORTH, Suit.DIAMONDS, 13, 13)), own=own))
    assert result.diagnostics.status is ConditionalStatus.INFEASIBLE
    assert result.diagnostics.proposal_allocation_count == 0
    assert result.model.conflicts and result.model.proposals == 0


def tiny_state(*, residual=False):
    # There are 13*13=169 physical allocations: the diamond East gets and
    # the club West gets. Equal card HCP gives exactly 9*9 + 4 = 85 allocations.
    own = Hand.parse("AKQJT98765432.-.-.-")
    updates = [shape(Seat.NORTH, ((0, 13, 0, 0),)), shape(Seat.WEST, ((0, 0, 12, 1),)),
               shape(Seat.EAST, ((0, 0, 1, 12),)), hcp(Seat.WEST, 10, 10)]
    if residual:
        updates.append(hcp(Seat.NORTH, 10, 10))
    return state(tuple(updates), own=own)


def test_primary_hcp_mass_matches_independent_tiny_enumeration():
    oracle = [(d, c) for d in full_deck() if d.suit is Suit.DIAMONDS
              for c in full_deck() if c.suit is Suit.CLUBS
              if max(int(d.rank) - 10, 0) == max(int(c.rank) - 10, 0)]
    sampler = ConditionalSampler(tiny_state())
    assert sampler.diagnostics.proposal_allocation_count == len(oracle) == 85
    result = sampler.sample(SamplingConfig(5000, 5000, 55)).model
    assert result.accepted == result.proposals == 5000
    observed = sum(any(c.rank is Rank.ACE for c in s.hand(Seat.EAST).cards_in(Suit.DIAMONDS))
                   for s in result.samples) / result.accepted
    p = 1 / 85
    assert abs(observed - p) <= 6 * sqrt(p * (1-p) / result.accepted)


def test_uniform_card_allocation_given_fixed_counts():
    own = Hand.parse("AKQJT98765432.-.-.-")
    s = state((shape(Seat.NORTH, ((0, 13, 0, 0),)), shape(Seat.WEST, ((0, 0, 12, 1),)),
               shape(Seat.EAST, ((0, 0, 1, 12),))), own=own)
    sampler = ConditionalSampler(s)
    assert sampler.diagnostics.proposal_allocation_count == 169
    result = sampler.sample(SamplingConfig(4000, 4000, 91)).model
    p = 1/13
    for rank in Rank:
        observed = sum(s.hand(Seat.EAST).cards_in(Suit.DIAMONDS)[0].rank is rank
                       for s in result.samples) / result.accepted
        assert abs(observed - p) <= 6 * sqrt(p * (1-p) / result.accepted)


def test_residual_hcp_is_explicit_and_still_uniform():
    sampler = ConditionalSampler(tiny_state(residual=True))
    assert sampler.diagnostics.primary_hcp_seat is Seat.NORTH
    assert sampler.diagnostics.proposal_allocation_count == 169
    assert sampler.diagnostics.residual_hcp_seats == (Seat.WEST,)
    result = sampler.sample(SamplingConfig(4000, 15000, 45)).model
    assert result.accepted == 4000 and result.proposals > 4000
    assert sum(n for _, n in result.rejections) + result.accepted == result.proposals
    assert all(high_card_points(s.hand(Seat.WEST)) == 10 for s in result.samples)
    p = 1/85
    observed = sum(s.hand(Seat.EAST).cards_in(Suit.DIAMONDS)[0].rank is Rank.ACE
                   for s in result.samples) / result.accepted
    assert abs(observed - p) <= 6 * sqrt(p * (1-p) / result.accepted)


def test_residual_budget_does_not_mean_infeasible():
    result = ConditionalSampler(tiny_state(residual=True)).sample(SamplingConfig(100, 10, 19))
    assert result.diagnostics.status is ConditionalStatus.READY
    assert result.model.sampling_status is SamplingStatus.BUDGET_EXHAUSTED
    assert result.model.proposals == 10 and result.model.accepted < 100


def test_reference_conditional_and_exact_marginals_agree():
    from benchmarks.pta1_probability_validation import exact_partner_joint
    s = state((length(Seat.NORTH, Suit.SPADES, 4), hcp(Seat.NORTH, 10, 12)))
    joint = {key: p for key, p in exact_partner_joint(OWN).items() if key[0] >= 4 and 10 <= key[1] <= 12}
    p = float(sum(v for (spades, _), v in joint.items() if spades == 4) / sum(joint.values()))
    direct = sample(s, n=3000, seed=31).model
    reference = sample_hidden_hands(s, SamplingConfig(3000, 100000, 32))
    frequencies = []
    for model in (direct, reference):
        assert model.accepted == 3000
        observed = sum(x.hand(Seat.NORTH).length(Suit.SPADES) == 4 for x in model.samples) / model.accepted
        assert abs(observed - p) <= 6 * sqrt(p * (1-p) / model.accepted)
        frequencies.append(observed)
    assert abs(frequencies[0] - frequencies[1]) <= 6 * sqrt(2 * p * (1-p) / 3000)


@pytest.mark.parametrize("conditioned", (False, True))
def test_conditional_vacant_places_reference(conditioned):
    updates = (length(Seat.NORTH, Suit.SPADES, 4, 4),)
    if conditioned:
        updates += (length(Seat.WEST, Suit.DIAMONDS, 5, 5), length(Seat.EAST, Suit.DIAMONDS, 3, 3))
    s = state(updates)
    model = sample(s, n=4000, seed=8).model
    reference = vacant_place_reference(s, Suit.SPADES, 4,
                                       defender_side_suit=Suit.DIAMONDS if conditioned else None)
    for item in reference:
        p = float(item.probability.as_fraction())
        observed = sum(x.hand(Seat.WEST).length(Suit.SPADES) == item.first_trumps
                       for x in model.samples) / model.accepted
        assert abs(observed - p) <= 6 * sqrt(p * (1-p) / model.accepted)


def test_partnership_shortness_does_not_change_fixed_total_defender_reference():
    a = state((shape(Seat.NORTH, ((4, 4, 1, 4),)),))
    b = state((shape(Seat.NORTH, ((4, 3, 3, 3),)),))
    for s in (a, b):
        model = sample(s, n=3000, seed=41).model
        p = float(vacant_place_reference(s, Suit.SPADES, 4)[2].probability.as_fraction())
        observed = sum(x.hand(Seat.WEST).length(Suit.SPADES) == 2 for x in model.samples) / model.accepted
        assert abs(observed - p) <= 6 * sqrt(p * (1-p) / model.accepted)


def test_soft_evidence_and_explicit_likelihood_keep_pta1_semantics():
    s = state((length(Seat.NORTH, Suit.SPADES, 4, 4, Certainty.PROBABILISTIC),))
    sampler = ConditionalSampler(s)
    cfg = SamplingConfig(100, 100, 1)
    unresolved = sampler.sample(cfg).model
    assert unresolved.samples == ConditionalSampler(state()).sample(cfg).model.samples
    assert unresolved.weighting_status is WeightingStatus.INSUFFICIENT_WEIGHTING
    rule = LikelihoodRule(EvidenceKey(0, Feature.SPADES), ((4, ProbabilityValue(1, 1)),),
        ProbabilityValue(0, 1), SOURCE)
    weighted = sampler.sample(SamplingConfig(100, 100, 1, (rule,))).model
    assert weighted.samples == unresolved.samples
    assert weighted.weighting_status is WeightingStatus.WEIGHTED
    assert any(w.is_zero for w in weighted.weights)
    assert sum(w.as_fraction() for w in weighted.weights) == 1
    assert 0 < weighted.effective_sample_size < weighted.accepted
    assert weighted.soft_evidence[0].evidence.certainty is Certainty.PROBABILISTIC


def test_public_entry_rejects_source_deal_and_has_no_value_outputs():
    assert tuple(inspect.signature(sample_conditional_hidden_hands).parameters) == ("state", "config")
    with pytest.raises(TypeError):
        ConditionalSampler(generate_deal(1))
    result = sample(state(), n=1)
    assert not set(result.model.__dataclass_fields__).intersection(
        {"erv", "npt", "srv", "crv", "rcc", "apt", "distribution_points"})


def test_infeasibility_provenance_does_not_blame_soft_evidence():
    soft_source = ConstraintProvenance(EvidenceOrigin.NEGATIVE_INFERENCE, "unresolved soft evidence")
    soft = AuctionConstraintUpdate(Seat.EAST, hcp=RangeEvidence(
        NumericRange(3, 5), Certainty.INFERRED, soft_source))
    own = Hand.parse("AKQ42.9876.-.J763")
    result = sample(state((hcp(Seat.NORTH, 20, 20),
                           length(Seat.NORTH, Suit.DIAMONDS, 13, 13), soft), own=own))
    assert result.diagnostics.status is ConditionalStatus.INFEASIBLE
    sources = result.model.conflicts[0].sources
    assert SOURCE in sources and soft_source not in sources
    assert any(source.origin is EvidenceOrigin.OWN_HAND for source in sources)
    assert result.model.soft_evidence[0].evidence.provenance == soft_source
