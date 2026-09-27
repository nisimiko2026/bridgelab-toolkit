"""PT-A1 contract, physical allocation, and statistical checks."""
import ast
from fractions import Fraction
import inspect
from math import comb, sqrt
import random

import pytest

import bridge.hidden_hand_probability as module
from bridge.auction import Auction
from bridge.auction_information import (
    AuctionConstraintUpdate, AuctionInformationState, Certainty, ConstraintProvenance,
    DiscreteDistribution, EvidenceOrigin, NumericRange, RangeEvidence, ShapeEvidence,
)
from bridge.deals import Deal, full_deck, generate_deal
from bridge.evaluation import high_card_points
from bridge.hidden_hand_probability import (
    EvidenceKey, Feature, LikelihoodRule, SamplingConfig, SamplingStatus,
    WeightingStatus, sample_hidden_hands, vacant_place_reference,
)
from bridge.models import Hand, Seat, Suit
from bridge.probability_values import ProbabilityValue

OWN = Hand.parse("AKQ42.9876.3.J76")
SOURCE = ConstraintProvenance(EvidenceOrigin.PROFILE_INTERPRETATION, "synthetic general evidence")


def state(updates=(), own=OWN, perspective=Seat.SOUTH):
    return AuctionInformationState.start(perspective, own, perspective).with_updates(updates)


def length(seat, suit, low, high=13, certainty=Certainty.GUARANTEED):
    return AuctionConstraintUpdate(seat, suit_lengths=((suit, RangeEvidence(
        NumericRange(low, high), certainty, SOURCE)),))


def hcp(low, high):
    return AuctionConstraintUpdate(Seat.NORTH, hcp=RangeEvidence(
        NumericRange(low, high), Certainty.GUARANTEED, SOURCE))


def config(n=100, budget=20000, seed=19, likelihoods=()):
    return SamplingConfig(n, budget, seed, likelihoods)


def test_deterministic_result_includes_samples_marginals_and_diagnostics():
    s = state((length(Seat.NORTH, Suit.SPADES, 3),))
    assert sample_hidden_hands(s, config()) == sample_hidden_hands(s, config())


def test_different_seeds_change_samples():
    assert sample_hidden_hands(state(), config(seed=1)).samples != sample_hidden_hands(state(), config(seed=2)).samples


@pytest.mark.parametrize("perspective", tuple(Seat))
def test_legal_full_partition_and_oriented_seats(perspective):
    result = sample_hidden_hands(state(perspective=perspective), config(30))
    assert result.accepted == 30
    for sample in result.samples:
        assert tuple(seat for seat, _ in sample.hands) == (
            perspective.partner(), perspective.next(), perspective.partner().next())
        cards = list(OWN.cards)
        for _, hand in sample.hands:
            assert len(hand.cards) == 13
            assert not set(hand.cards).intersection(OWN.cards)
            cards.extend(hand.cards)
        assert len(cards) == len(set(cards)) == 52
        assert set(cards) == set(full_deck())


def test_hidden_source_cards_have_zero_effect():
    a = generate_deal(17)
    own = a.hand(Seat.SOUTH)
    unseen = [card for card in full_deck() if card not in own.cards]
    random.Random(900).shuffle(unseen)
    b = Deal(18, ((Seat.SOUTH, own), (Seat.NORTH, Hand.from_cards(unseen[:13])),
                  (Seat.EAST, Hand.from_cards(unseen[13:26])), (Seat.WEST, Hand.from_cards(unseen[26:]))))
    assert all(a.hand(seat) != b.hand(seat) for seat in (Seat.NORTH, Seat.EAST, Seat.WEST))
    auction = Auction(Seat.SOUTH, ("1S", "P", "2S"))
    updates = (length(Seat.NORTH, Suit.SPADES, 3),)
    first = AuctionInformationState.from_auction(Seat.SOUTH, a.hand(Seat.SOUTH), auction, updates)
    second = AuctionInformationState.from_auction(Seat.SOUTH, b.hand(Seat.SOUTH), auction, updates)
    assert sample_hidden_hands(first, config()) == sample_hidden_hands(second, config())


@pytest.mark.parametrize("minimum,maximum", ((3, 13), (4, 13), (4, 4)))
def test_hard_partner_lengths(minimum, maximum):
    result = sample_hidden_hands(state((length(Seat.NORTH, Suit.SPADES, minimum, maximum),)), config())
    assert result.sampling_status is SamplingStatus.COMPLETE
    assert all(minimum <= s.hand(Seat.NORTH).length(Suit.SPADES) <= maximum for s in result.samples)


@pytest.mark.parametrize("low,high", ((10, 12), (11, 11)))
def test_hard_hcp(low, high):
    result = sample_hidden_hands(state((hcp(low, high),)), config())
    assert result.accepted == 100
    assert all(low <= high_card_points(s.hand(Seat.NORTH)) <= high for s in result.samples)


def test_combined_hcp_and_length():
    result = sample_hidden_hands(state((hcp(10, 12), length(Seat.NORTH, Suit.SPADES, 4))), config())
    assert result.accepted == 100
    assert all(10 <= high_card_points(s.hand(Seat.NORTH)) <= 12
               and s.hand(Seat.NORTH).length(Suit.SPADES) >= 4 for s in result.samples)


def test_only_admissible_shape_alternatives():
    shapes = ((4, 4, 4, 1), (5, 3, 3, 2))
    evidence = ShapeEvidence(shapes, Certainty.GUARANTEED, SOURCE)
    result = sample_hidden_hands(state((AuctionConstraintUpdate(Seat.NORTH, shapes=evidence),)), config(50))
    assert result.accepted == 50
    assert all(tuple(s.hand(Seat.NORTH).length(suit) for suit in (
        Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)) in shapes for s in result.samples)


def test_opponent_constraints_not_interchangeable():
    result = sample_hidden_hands(state((length(Seat.WEST, Suit.DIAMONDS, 5),
                                       length(Seat.EAST, Suit.DIAMONDS, 0, 2))), config(40))
    assert result.accepted == 40
    assert all(s.hand(Seat.WEST).length(Suit.DIAMONDS) >= 5
               and s.hand(Seat.EAST).length(Suit.DIAMONDS) <= 2 for s in result.samples)


def test_contradiction_rejected_before_rng(monkeypatch):
    def forbidden(*args):
        raise AssertionError("sampling contradictory state")
    monkeypatch.setattr(module.random, "Random", forbidden)
    result = sample_hidden_hands(state((length(Seat.NORTH, Suit.SPADES, 5),
                                       length(Seat.WEST, Suit.SPADES, 4))), config())
    assert result.sampling_status is SamplingStatus.CONTRADICTORY
    assert result.proposals == result.accepted == 0 and result.conflicts
    assert result.weights == result.marginals == ()


@pytest.mark.parametrize("certainty", (Certainty.INFERRED, Certainty.PROBABILISTIC))
def test_soft_evidence_does_not_restrict_samples(certainty):
    base = sample_hidden_hands(state(), config())
    result = sample_hidden_hands(state((length(Seat.NORTH, Suit.SPADES, 8, 8, certainty),)), config())
    assert result.samples == base.samples
    assert result.weights == base.weights
    assert result.weighting_status is WeightingStatus.INSUFFICIENT_WEIGHTING
    assert result.soft_evidence[0].evidence.certainty is certainty
    assert result.unresolved_soft_evidence == (EvidenceKey(0, Feature.SPADES),)


def test_probability_one_stays_soft_and_unresolved():
    evidence = RangeEvidence(NumericRange(4, 4), Certainty.PROBABILISTIC, SOURCE,
                             DiscreteDistribution(((4, ProbabilityValue(1, 1)),)))
    s = state((AuctionConstraintUpdate(Seat.NORTH, suit_lengths=((Suit.SPADES, evidence),)),))
    result = sample_hidden_hands(s, config())
    assert result.weighting_status is WeightingStatus.INSUFFICIENT_WEIGHTING
    assert any(sample.hand(Seat.NORTH).length(Suit.SPADES) != 4 for sample in result.samples)
    assert result.soft_evidence[0].evidence == evidence


def test_explicit_likelihood_weights_and_ess():
    s = state((length(Seat.NORTH, Suit.SPADES, 4, 4, Certainty.INFERRED),))
    rule = LikelihoodRule(EvidenceKey(0, Feature.SPADES), ((4, ProbabilityValue(1, 1)),),
                          ProbabilityValue(1, 4), SOURCE)
    result = sample_hidden_hands(s, config(likelihoods=(rule,)))
    prior = sample_hidden_hands(s, config())
    assert result.samples == prior.samples
    assert result.weighting_status is WeightingStatus.WEIGHTED
    raw = [Fraction(1) if sample.hand(Seat.NORTH).length(Suit.SPADES) == 4 else Fraction(1, 4)
           for sample in result.samples]
    assert [w.as_fraction() for w in result.weights] == [w / sum(raw) for w in raw]
    assert result.effective_sample_size == sum(raw) ** 2 / sum(w * w for w in raw)
    assert 0 < result.effective_sample_size < result.accepted
    assert result.config.likelihoods[0].provenance == SOURCE


def test_zero_soft_weight_does_not_remove_legal_samples():
    s = state((length(Seat.NORTH, Suit.SPADES, 4, 4, Certainty.PROBABILISTIC),))
    rule = LikelihoodRule(EvidenceKey(0, Feature.SPADES), ((4, ProbabilityValue(1, 1)),),
                          ProbabilityValue(0, 1), SOURCE)
    result = sample_hidden_hands(s, config(likelihoods=(rule,)))
    assert any(weight.is_zero for weight in result.weights)
    assert result.accepted == 100 and result.sampling_status is SamplingStatus.COMPLETE
    assert result.soft_evidence[0].evidence.certainty is Certainty.PROBABILISTIC


def test_all_zero_weights_have_explicit_status():
    s = state((length(Seat.NORTH, Suit.SPADES, 4, 4, Certainty.INFERRED),))
    rule = LikelihoodRule(EvidenceKey(0, Feature.SPADES), (), ProbabilityValue(0, 1), SOURCE)
    result = sample_hidden_hands(s, config(likelihoods=(rule,)))
    assert result.weighting_status is WeightingStatus.ZERO_TOTAL_WEIGHT
    assert result.accepted == 100 and result.weights == result.marginals == ()
    assert result.effective_sample_size == 0


def test_likelihood_requires_existing_soft_evidence():
    rule = LikelihoodRule(EvidenceKey(0, Feature.SPADES), (), ProbabilityValue(1, 1), SOURCE)
    with pytest.raises(ValueError, match="soft evidence"):
        sample_hidden_hands(state((length(Seat.NORTH, Suit.SPADES, 3),)), config(likelihoods=(rule,)))


def test_normalization_and_unweighted_ess():
    result = sample_hidden_hands(state(), config())
    assert sum(w.as_fraction() for w in result.weights) == 1
    assert result.effective_sample_size == 100
    assert len(result.marginals) == 18
    for marginal in result.marginals:
        assert sum(p.as_fraction() for _, p in marginal.outcomes) == 1


def test_rejection_accounting_and_budget_exhaustion():
    result = sample_hidden_hands(state((length(Seat.NORTH, Suit.SPADES, 4),)), config(1000, 30))
    assert result.sampling_status is SamplingStatus.BUDGET_EXHAUSTED
    assert result.proposals == 30
    assert sum(count for _, count in result.rejections) + result.accepted == result.proposals
    assert result.rejection_rate == (30 - result.accepted) / 30
    assert result.accepted < result.requested


def test_unrealizable_rank_constraints_are_exhausted_not_relaxed():
    # Shape and HCP are individually permitted by PT-A0, but thirteen diamonds
    # contain only ten HCP. Sampling must neither relax constraints nor claim
    # that budget exhaustion itself proves impossibility.
    own = Hand.parse("AKQ42.9876.-.J763")
    s = state((hcp(20, 20), length(Seat.NORTH, Suit.DIAMONDS, 13, 13)), own=own)
    result = sample_hidden_hands(s, config(1, 20))
    assert result.sampling_status is SamplingStatus.BUDGET_EXHAUSTED
    assert result.proposals == 20 and result.accepted == 0
    assert result.weighting_status is WeightingStatus.NO_SAMPLES
    assert result.weights == result.marginals == ()


def test_partially_weighted_evidence_retains_unresolved_items():
    s = state((length(Seat.NORTH, Suit.SPADES, 4, 4, Certainty.INFERRED),
               length(Seat.WEST, Suit.DIAMONDS, 5, 5, Certainty.INFERRED)))
    rule = LikelihoodRule(EvidenceKey(0, Feature.SPADES), (), ProbabilityValue(1, 2), SOURCE)
    result = sample_hidden_hands(s, config(likelihoods=(rule,)))
    assert result.weighting_status is WeightingStatus.INSUFFICIENT_WEIGHTING
    assert result.unresolved_soft_evidence == (EvidenceKey(1, Feature.DIAMONDS),)
    assert len(result.soft_evidence) == 2


def test_soft_shape_is_preserved_without_exclusion():
    shape = ShapeEvidence(((4, 4, 4, 1),), Certainty.INFERRED, SOURCE)
    result = sample_hidden_hands(state((AuctionConstraintUpdate(Seat.NORTH, shapes=shape),)), config())
    assert result.samples == sample_hidden_hands(state(), config()).samples
    assert result.soft_evidence[0].evidence == shape


@pytest.mark.parametrize("seed", (101, 202))
def test_unconstrained_hypergeometric_distribution(seed):
    result = sample_hidden_hands(state(), config(4000, 4000, seed))
    p = sum(Fraction(comb(8, k) * comb(31, 13-k), comb(39, 13)) for k in range(3, 9))
    observed = sum(s.hand(Seat.NORTH).length(Suit.SPADES) >= 3 for s in result.samples) / result.accepted
    se = sqrt(float(p * (1-p)) / result.accepted)
    # A prespecified six-standard-error stochastic guard, not a calibration claim.
    assert abs(observed - float(p)) <= 6 * se


def test_vacant_reference_ignores_partnership_shortness():
    other = Hand.parse("AKQ42.98.32.J765")
    a = vacant_place_reference(state(), Suit.SPADES, 4)
    b = vacant_place_reference(state(own=other), Suit.SPADES, 4)
    short = ShapeEvidence(((4, 4, 1, 4),), Certainty.GUARANTEED, SOURCE)
    c = vacant_place_reference(state((AuctionConstraintUpdate(Seat.NORTH, shapes=short),)), Suit.SPADES, 4)
    assert a == b == c
    assert a[2].probability.as_fraction() == Fraction(comb(13, 2)**2, comb(26, 4))
    assert a[0].first_defender is Seat.WEST and a[0].second_defender is Seat.EAST


def test_defender_specific_vacant_reference_preserves_orientation():
    s = state((length(Seat.WEST, Suit.DIAMONDS, 5, 5), length(Seat.EAST, Suit.DIAMONDS, 3, 3)))
    result = vacant_place_reference(s, Suit.SPADES, 4, defender_side_suit=Suit.DIAMONDS)
    assert result[0].probability.as_fraction() == Fraction(comb(10, 4), comb(18, 4))
    assert result[4].probability.as_fraction() == Fraction(comb(8, 4), comb(18, 4))
    assert result[0].probability != result[4].probability


def test_soft_or_ranged_lengths_not_coerced_to_vacant_places():
    s = state((length(Seat.WEST, Suit.DIAMONDS, 5),))
    with pytest.raises(ValueError, match="fixed hard lengths"):
        vacant_place_reference(s, Suit.SPADES, 4, defender_side_suit=Suit.DIAMONDS)


def test_sampled_defender_break_matches_vacant_reference():
    s = state((length(Seat.NORTH, Suit.SPADES, 4, 4),))
    result = sample_hidden_hands(s, config(3000, 30000, 44))
    expected = float(vacant_place_reference(s, Suit.SPADES, 4)[2].probability.as_fraction())
    observed = sum(x.hand(Seat.WEST).length(Suit.SPADES) == 2 for x in result.samples) / result.accepted
    assert abs(observed - expected) <= 6 * sqrt(expected * (1-expected) / result.accepted)


@pytest.mark.parametrize("kwargs", ({"requested": 0}, {"max_proposals": 0}, {"seed": True},
                                    {"likelihoods": []}))
def test_invalid_configuration(kwargs):
    with pytest.raises((TypeError, ValueError)):
        SamplingConfig(**kwargs)


def test_no_source_deal_input_or_forbidden_dependencies():
    assert tuple(inspect.signature(sample_hidden_hands).parameters) == ("state", "config")
    with pytest.raises(TypeError):
        sample_hidden_hands(generate_deal(1))
    imports = [n.module for n in ast.walk(ast.parse(inspect.getsource(module))) if isinstance(n, ast.ImportFrom)]
    assert not any(any(term in name for term in ("dds", "endplay", "bidding", "partnership", "playing_trick"))
                   for name in imports if name)
    assert "Deal" not in vars(module)


def test_result_retains_visible_state_for_provenance_replay():
    auction = Auction(Seat.SOUTH, ("1S", "P", "2S"))
    visible = AuctionInformationState.from_auction(Seat.SOUTH, OWN, auction,
                                                   (length(Seat.NORTH, Suit.SPADES, 3),))
    result = sample_hidden_hands(visible, config(10))
    assert result.information_state == visible
    assert sample_hidden_hands(result.information_state, result.config) == result


def test_exact_combinatorial_reference_matches_hypergeometric_and_symmetry():
    from benchmarks.pta1_probability_validation import exact_partner_joint
    joint = exact_partner_joint(OWN)
    assert sum(joint.values()) == 1
    for k in range(9):
        assert sum(p for (spades, _), p in joint.items() if spades == k) == Fraction(
            comb(8, k) * comb(31, 13-k), comb(39, 13))
    assert sum(hcp * p for (_, hcp), p in joint.items()) == Fraction(40 - high_card_points(OWN), 3)


def test_joint_shape_contradiction_rejected_before_sampling():
    evidence = ShapeEvidence(((1, 3, 4, 5), (5, 3, 4, 1)), Certainty.GUARANTEED, SOURCE)
    result = sample_hidden_hands(state(tuple(AuctionConstraintUpdate(seat, shapes=evidence)
                                            for seat in (Seat.NORTH, Seat.WEST, Seat.EAST))), config())
    assert result.sampling_status is SamplingStatus.CONTRADICTORY
    assert result.proposals == 0 and not result.samples
    assert any(c.subject == "joint unseen shapes" for c in result.conflicts)


def test_empirical_probability_one_is_explicitly_probabilistic():
    result = sample_hidden_hands(state((hcp(11, 11),)), config(20))
    marginal = result.marginal(Seat.NORTH, Feature.HCP)
    assert marginal.outcomes == ((11, ProbabilityValue(1, 1)),)
    assert marginal.certainty is Certainty.PROBABILISTIC
    assert result.information_state.updates[0].hcp.certainty is Certainty.GUARANTEED
