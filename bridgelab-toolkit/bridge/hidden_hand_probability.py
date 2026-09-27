"""Seeded uniform hidden-card allocation conditioned on PT-A0 hard evidence.

No actual hidden hand is an input. Soft marginal beliefs are not likelihoods:
only explicit configuration factors may reweight the hard-conditioned prior.
Runtime measurements belong outside these reproducible immutable results.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
import random

from .auction_information import (
    AuctionInformationState, AuctionConstraintUpdate, Certainty, ConstraintConflict,
    ConstraintProvenance, InformationStatus, RangeEvidence, ShapeEvidence,
)
from .deals import full_deck
from .evaluation import SUIT_ORDER, high_card_points
from .models import Hand, Seat, Suit
from .probability_questions import VacantPlacesQuestion
from .probability_values import ProbabilityValue
from .vacant_places import OrientedTrumpBreak, oriented_trump_break


class SamplingStatus(Enum):
    COMPLETE = "complete"
    CONTRADICTORY = "contradictory"
    BUDGET_EXHAUSTED = "budget_exhausted"


class WeightingStatus(Enum):
    BASELINE = "baseline"
    WEIGHTED = "weighted"
    INSUFFICIENT_WEIGHTING = "insufficient_weighting"
    ZERO_TOTAL_WEIGHT = "zero_total_weight"
    NO_SAMPLES = "no_samples"


class Feature(Enum):
    HCP = "hcp"
    SPADES = "spades"
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SHAPE = "shape"


SUIT_FEATURES = dict(zip(SUIT_ORDER, (
    Feature.SPADES, Feature.HEARTS, Feature.DIAMONDS, Feature.CLUBS)))
Outcome = int | tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class EvidenceKey:
    update_index: int
    feature: Feature

    def __post_init__(self) -> None:
        if type(self.update_index) is not int or self.update_index < 0:
            raise ValueError("update_index must be a nonnegative integer")
        if not isinstance(self.feature, Feature):
            raise TypeError("feature must be Feature")


@dataclass(frozen=True, slots=True)
class SoftEvidence:
    key: EvidenceKey
    seat: Seat
    evidence: RangeEvidence | ShapeEvidence


@dataclass(frozen=True, slots=True)
class LikelihoodRule:
    """Explicit likelihood factors, NOT a desired posterior marginal.

    Rules multiply, so supplying multiple rules explicitly asserts a product
    likelihood model. Zero factors are allowed but do not remove legal samples
    or turn the underlying soft evidence into a guarantee.
    """

    key: EvidenceKey
    factors: tuple[tuple[Outcome, ProbabilityValue], ...]
    default: ProbabilityValue
    provenance: ConstraintProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.key, EvidenceKey) or not isinstance(self.provenance, ConstraintProvenance):
            raise TypeError("rule needs typed key and provenance")
        if not isinstance(self.default, ProbabilityValue) or not isinstance(self.factors, tuple):
            raise TypeError("rule needs immutable factors and an explicit default")
        for item in self.factors:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("factors must be immutable outcome/probability pairs")
            value, weight = item
            if not isinstance(weight, ProbabilityValue):
                raise TypeError("likelihood factors must be ProbabilityValue")
            if self.key.feature is Feature.SHAPE:
                if (not isinstance(value, tuple) or len(value) != 4
                        or any(type(n) is not int or n < 0 for n in value) or sum(value) != 13):
                    raise ValueError("shape factors need a legal S.H.D.C shape")
            elif type(value) is not int or not 0 <= value <= (40 if self.key.feature is Feature.HCP else 13):
                raise ValueError("invalid feature outcome")
        if len({value for value, _ in self.factors}) != len(self.factors):
            raise ValueError("duplicate likelihood outcome")

    def factor(self, value: Outcome) -> Fraction:
        return dict(self.factors).get(value, self.default).as_fraction()


@dataclass(frozen=True, slots=True)
class SamplingConfig:
    requested: int = 1000
    max_proposals: int = 100000
    seed: int = 0
    likelihoods: tuple[LikelihoodRule, ...] = ()

    def __post_init__(self) -> None:
        if type(self.seed) is not int:
            raise TypeError("seed must be an integer")
        if type(self.requested) is not int or self.requested <= 0:
            raise ValueError("requested must be a positive integer")
        if type(self.max_proposals) is not int or self.max_proposals <= 0:
            raise ValueError("max_proposals must be a positive integer")
        if not isinstance(self.likelihoods, tuple) or any(not isinstance(r, LikelihoodRule) for r in self.likelihoods):
            raise TypeError("likelihoods must be an immutable tuple of rules")
        if len({r.key for r in self.likelihoods}) != len(self.likelihoods):
            raise ValueError("only one likelihood rule per evidence item")


@dataclass(frozen=True, slots=True)
class HiddenSample:
    """One generated possibility, never the actual source-deal hidden cards."""

    hands: tuple[tuple[Seat, Hand], ...]

    def hand(self, seat: Seat) -> Hand:
        return dict(self.hands)[seat]


@dataclass(frozen=True, slots=True)
class Marginal:
    seat: Seat
    feature: Feature
    outcomes: tuple[tuple[Outcome, ProbabilityValue], ...]
    certainty: Certainty = field(default=Certainty.PROBABILISTIC, init=False)


@dataclass(frozen=True, slots=True)
class HiddenHandResult:
    perspective: Seat
    config: SamplingConfig
    sampling_status: SamplingStatus
    weighting_status: WeightingStatus
    proposals: int
    samples: tuple[HiddenSample, ...]
    rejections: tuple[tuple[str, int], ...]
    weights: tuple[ProbabilityValue, ...]
    effective_sample_size: Fraction
    marginals: tuple[Marginal, ...]
    evidence: tuple[AuctionConstraintUpdate, ...]
    soft_evidence: tuple[SoftEvidence, ...]
    unresolved_soft_evidence: tuple[EvidenceKey, ...]
    conflicts: tuple[ConstraintConflict, ...]
    information_state: AuctionInformationState
    algorithm: str = "uniform-unseen-shuffle-rejection-v1"

    @property
    def requested(self) -> int:
        return self.config.requested

    @property
    def accepted(self) -> int:
        return len(self.samples)

    @property
    def rejection_rate(self) -> float:
        return (self.proposals - self.accepted) / self.proposals if self.proposals else 0.0

    def marginal(self, seat: Seat, feature: Feature) -> Marginal:
        return next(m for m in self.marginals if m.seat is seat and m.feature is feature)


def _value(hand: Hand, feature: Feature) -> Outcome:
    if feature is Feature.HCP:
        return high_card_points(hand)
    shape = tuple(hand.length(suit) for suit in SUIT_ORDER)
    if feature is Feature.SHAPE:
        return shape
    return shape[tuple(SUIT_FEATURES.values()).index(feature)]


def _soft_evidence(state: AuctionInformationState) -> tuple[SoftEvidence, ...]:
    found = []
    for index, update in enumerate(state.updates):
        items = [(SUIT_FEATURES[suit], e) for suit, e in update.suit_lengths]
        if update.hcp is not None:
            items.append((Feature.HCP, update.hcp))
        if update.shapes is not None:
            items.append((Feature.SHAPE, update.shapes))
        found.extend(SoftEvidence(EvidenceKey(index, feature), update.target, evidence)
                     for feature, evidence in items if not evidence.is_hard)
    return tuple(found)


def sample_hidden_hands(state: AuctionInformationState,
                        config: SamplingConfig = SamplingConfig()) -> HiddenHandResult:
    """IID draws from the uniform prior conditional on hard evidence.

    Proposal budget exhaustion is not proof that no legal deal exists.
    With unresolved soft evidence, marginals describe the hard-conditioned prior
    plus any explicitly supplied factors, not an all-evidence posterior.
    """
    if not isinstance(state, AuctionInformationState) or not isinstance(config, SamplingConfig):
        raise TypeError("requires AuctionInformationState and SamplingConfig")
    soft = _soft_evidence(state)
    by_key = {item.key: item for item in soft}
    if any(rule.key not in by_key for rule in config.likelihoods):
        raise ValueError("likelihoods must reference existing soft evidence")
    unresolved = tuple(item.key for item in soft if item.key not in {r.key for r in config.likelihoods})
    conflicts = state.conflicts
    if conflicts:
        return HiddenHandResult(state.perspective, config, SamplingStatus.CONTRADICTORY,
                                WeightingStatus.NO_SAMPLES, 0, (), (), (), Fraction(), (),
                                state.updates, soft, unresolved, conflicts, state)

    seats = (state.partner, *state.opponents)
    information = {seat: state.for_seat(seat) for seat in seats}
    allowed_shapes = {seat: set(information[seat].possible_shapes) for seat in seats}
    unseen = tuple(card for card in full_deck() if card not in state.own_hand.cards)
    rng = random.Random(config.seed)
    samples = []
    rejected = Counter()
    proposals = 0
    while len(samples) < config.requested and proposals < config.max_proposals:
        cards = list(unseen)
        rng.shuffle(cards)
        proposals += 1
        hands = tuple((seat, Hand.from_cards(cards[i * 13:(i + 1) * 13]))
                      for i, seat in enumerate(seats))
        reason = None
        for seat, hand in hands:
            info = information[seat]
            points = high_card_points(hand)
            if not info.hcp.minimum <= points <= info.hcp.maximum:
                reason = f"{seat.value}:hcp"
                break
            for suit in SUIT_ORDER:
                bound = info.suit_range(suit)
                if not bound.minimum <= hand.length(suit) <= bound.maximum:
                    reason = f"{seat.value}:{suit.letter}_length"
                    break
            if reason:
                break
            if _value(hand, Feature.SHAPE) not in allowed_shapes[seat]:
                reason = f"{seat.value}:shape"
                break
        if reason:
            rejected[reason] += 1
        else:
            samples.append(HiddenSample(hands))

    raw = []
    for sample in samples:
        weight = Fraction(1)
        for rule in config.likelihoods:
            item = by_key[rule.key]
            weight *= rule.factor(_value(sample.hand(item.seat), item.key.feature))
        raw.append(weight)
    total = sum(raw, Fraction())
    weights = tuple(ProbabilityValue.from_fraction(w.numerator, w.denominator)
                    for w in (value / total for value in raw)) if total else ()
    if not samples:
        weighting = WeightingStatus.NO_SAMPLES
    elif not total:
        weighting = WeightingStatus.ZERO_TOTAL_WEIGHT
    elif unresolved:
        weighting = WeightingStatus.INSUFFICIENT_WEIGHTING
    else:
        weighting = WeightingStatus.WEIGHTED if config.likelihoods else WeightingStatus.BASELINE
    marginals = []
    if weights:
        for seat in seats:
            for feature in Feature:
                counts = Counter()
                for sample, weight in zip(samples, weights):
                    counts[_value(sample.hand(seat), feature)] += weight.as_fraction()
                marginals.append(Marginal(seat, feature, tuple(
                    (value, ProbabilityValue.from_fraction(weight.numerator, weight.denominator))
                    for value, weight in sorted(counts.items()))))
    ess = Fraction(1) / sum((w.as_fraction() ** 2 for w in weights), Fraction()) if weights else Fraction()
    return HiddenHandResult(
        state.perspective, config,
        SamplingStatus.COMPLETE if len(samples) == config.requested else SamplingStatus.BUDGET_EXHAUSTED,
        weighting, proposals, tuple(samples), tuple(sorted(rejected.items())),
        weights, ess, tuple(marginals), state.updates, soft, unresolved, (), state)


def vacant_place_reference(state: AuctionInformationState, trump: Suit, outstanding: int,
                           *, defender_side_suit: Suit | None = None) -> tuple[OrientedTrumpBreak, ...]:
    """Exact reference for a limited defender-only conditional experiment.

    Unconditional mode ignores partnership shortness. Conditional mode requires
    logically fixed side lengths at BOTH defenders. Range/soft evidence is never
    converted to exact vacant places. This reference is not a posterior for
    additional HCP/shape constraints or unspecified joint conditioning.
    """
    if not isinstance(state, AuctionInformationState):
        raise TypeError("requires AuctionInformationState")
    if not isinstance(trump, Suit) or type(outstanding) is not int or not 0 <= outstanding <= 13:
        raise ValueError("requires a suit and outstanding count in 0..13")
    if state.status is InformationStatus.CONTRADICTORY:
        raise ValueError("contradictory state has no vacant-place reference")
    fit = state.opponent_fit(trump).total
    if not fit.minimum <= outstanding <= fit.maximum:
        raise ValueError("outstanding count contradicts public hard bounds")
    question = VacantPlacesQuestion("PT-A1 defender reference", trump, state.opponents,
                                   declarer_seat=state.perspective)
    if defender_side_suit is None:
        return oriented_trump_break(question, outstanding)
    if not isinstance(defender_side_suit, Suit) or defender_side_suit is trump:
        raise ValueError("defender side suit must differ from trump")
    lengths = tuple(state.for_seat(seat).suit_range(defender_side_suit) for seat in state.opponents)
    if any(bound.minimum != bound.maximum for bound in lengths):
        raise ValueError("reference requires fixed hard lengths for both defenders")
    return oriented_trump_break(
        question, outstanding, side_suit=defender_side_suit,
        side_length_mixture=((lengths[0].minimum, lengths[1].minimum, ProbabilityValue(1, 1)),))
