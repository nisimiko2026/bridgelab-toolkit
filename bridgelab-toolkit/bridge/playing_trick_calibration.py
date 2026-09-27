"""System-neutral PT-1 deal calibration and observable ruffing features.

Structural capacities below are card counts, never playing-trick credits.
Trick outcomes and marginal values stay unavailable until a solver exists.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
from functools import lru_cache
from math import comb
import random
from typing import Callable

from .deals import Deal, full_deck
from .evaluation import evaluate_hand
from .models import Card, Hand, Rank, Seat, Suit


TRUMP_STRUCTURES = ((5, 3), (6, 3), (5, 4), (7, 3),
                    (6, 4), (5, 5), (7, 4), (6, 5))
HONORS = (Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK)


class ShortnessKind(str, Enum):
    BASELINE = "baseline"
    SHORT_HAND_SINGLETON = "short-hand-singleton"
    LONG_HAND_SINGLETON = "long-hand-singleton"
    EQUAL_HAND_SINGLETON = "equal-hand-singleton"
    RECIPROCAL_SINGLETONS = "reciprocal-singletons"
    MIXED_SHORTNESS = "mixed-shortness"


class CrossruffStage(str, Enum):
    NONE = "none"
    INDEPENDENT_SHORTNESS = "independent-shortness"
    CROSSRUFF_AVAILABLE = "crossruff-available"
    CROSSRUFF_ESTABLISHED = "crossruff-established"


def shortness_activation_round(length: int) -> int | None:
    """Rounds of a side suit that must be played before a ruff is possible."""
    if not isinstance(length, int) or isinstance(length, bool) or length < 0:
        raise ValueError("side-suit length must be a nonnegative integer")
    return length if length <= 2 else None


@dataclass(frozen=True, slots=True)
class ShortSuitEvidence:
    hand: Seat
    suit: Suit
    length: int
    activation_round: int
    opposite_length: int
    certain_top_rank_winners: int
    ruffable_losers: int


@dataclass(frozen=True, slots=True)
class CalibrationCase:
    deal_seed: int
    deal_id: str
    trump_suit: Suit
    trump_structure: tuple[int, int]
    shortness_kind: ShortnessKind
    long_trump_hand: Seat | None
    short_trump_hand: Seat | None
    equal_trumps: bool
    partnership_trumps: int
    north_trumps: int
    south_trumps: int
    trump_honors_north: tuple[str, ...]
    trump_honors_south: tuple[str, ...]
    outstanding_trumps: int
    defender_trumps_east: tuple[str, ...]
    defender_trumps_west: tuple[str, ...]
    defender_trump_split: tuple[int, int]
    partnership_hcp: int
    side_honors_north: tuple[str, ...]
    side_honors_south: tuple[str, ...]
    short_suits: tuple[ShortSuitEvidence, ...]
    short_hand_ruff_capacity: int | None
    trump_numerical_control: tuple[int, int]
    trump_honor_control: tuple[str, ...]
    reciprocal_ruff_capacity: int
    side_ace_entries: tuple[int, int]
    potential_overruff_higher_trumps: tuple[int, ...]
    crossruff_stage: CrossruffStage
    natural_playing_tricks: float | None = None
    double_dummy_tricks: int | None = None
    useful_ruffs: int | None = None
    trump_cards_consumed: int | None = None
    marginal_ruff_value: float | None = None
    single_hand_ruffing_value: float | None = None
    crossruff_value: float | None = None
    control_cost: float | None = None
    overruff_result: float | None = None
    adjusted_playing_tricks: float | None = None

    def matched_stratum(self) -> tuple[object, ...]:
        """Exact observable matching keys; no outcome is inferred from a match."""
        return (self.trump_structure, self.partnership_hcp,
                self.trump_honors_north, self.trump_honors_south,
                self.side_honors_north, self.side_honors_south,
                tuple(item.ruffable_losers for item in self.short_suits),
                self.side_ace_entries, self.defender_trump_split)

    def comparison_stratum(self) -> tuple[object, ...]:
        """Coarse cross-structure strata within a fixed total-trump family.

        Trump allocation is the comparison exposure, so it cannot itself be
        matched. All remaining keys are observed before trick outcomes.
        """
        return (self.partnership_trumps, self.partnership_hcp // 2,
                tuple(sorted(self.trump_honor_control)),
                len(self.side_honors_north) + len(self.side_honors_south),
                sum(item.ruffable_losers for item in self.short_suits),
                sum(self.side_ace_entries),
                tuple(sorted(self.defender_trump_split)))


def _honors(hand: Hand, suit: Suit) -> tuple[str, ...]:
    return tuple(card.rank.symbol for card in hand.cards_in(suit) if card.rank in HONORS)


def _short_evidence(deal: Deal, hand: Seat, suit: Suit) -> ShortSuitEvidence:
    short = deal.hand(hand)
    opposite = deal.hand(hand.partner())
    length = short.length(suit)
    activation = shortness_activation_round(length)
    if activation is None:
        raise ValueError("studied side suit must be void, singleton, or doubleton")
    opposite_ranks = {card.rank for card in opposite.cards_in(suit)}
    # Only the uninterrupted top sequence *in the opposite hand* is excluded.
    # This is a conservative rank-based proxy, not a play or entry assertion.
    top_winners = 0
    for rank_number in range(14, 1, -1):
        if Rank(rank_number) not in opposite_ranks:
            break
        top_winners += 1
    losers = max(0, opposite.length(suit) - top_winners - activation)
    return ShortSuitEvidence(hand, suit, length, activation,
                             opposite.length(suit), top_winners, losers)


def analyze_case(deal: Deal, trump: Suit, kind: ShortnessKind,
                 short_suits: tuple[tuple[Seat, Suit], ...]) -> CalibrationCase:
    if not isinstance(trump, Suit) or not isinstance(kind, ShortnessKind):
        raise TypeError("typed trump suit and shortness kind required")
    north, south = deal.hand(Seat.NORTH), deal.hand(Seat.SOUTH)
    n, s = north.length(trump), south.length(trump)
    structure = tuple(sorted((n, s), reverse=True))
    if structure not in TRUMP_STRUCTURES:
        raise ValueError("unsupported principal trump structure")
    evidence = tuple(_short_evidence(deal, seat, suit) for seat, suit in short_suits)
    if kind is ShortnessKind.BASELINE and evidence:
        raise ValueError("baseline cannot have studied short suits")
    if kind is not ShortnessKind.BASELINE and not evidence:
        raise ValueError("shortness case needs studied short suits")
    if kind in (ShortnessKind.SHORT_HAND_SINGLETON, ShortnessKind.LONG_HAND_SINGLETON,
                ShortnessKind.EQUAL_HAND_SINGLETON):
        if len(evidence) != 1 or evidence[0].length != 1:
            raise ValueError("single-singleton label requires exactly one studied singleton")
    if kind is ShortnessKind.RECIPROCAL_SINGLETONS and (
        len(evidence) != 2 or any(item.length != 1 for item in evidence)
        or len({item.hand for item in evidence}) != 2
        or len({item.suit for item in evidence}) != 2
    ):
        raise ValueError("reciprocal-singleton label requires different singletons in both hands")
    if any(item.suit is trump for item in evidence):
        raise ValueError("shortness suit cannot be trump")
    if n == s:
        long_hand = short_hand = None
    else:
        long_hand = Seat.NORTH if n > s else Seat.SOUTH
        short_hand = long_hand.partner()
    if kind is ShortnessKind.SHORT_HAND_SINGLETON and short_hand is not None \
            and evidence[0].hand is not short_hand:
        raise ValueError("short-hand singleton is in the wrong hand")
    if kind is ShortnessKind.LONG_HAND_SINGLETON and long_hand is not None \
            and evidence[0].hand is not long_hand:
        raise ValueError("long-hand singleton is in the wrong hand")
    if kind is ShortnessKind.EQUAL_HAND_SINGLETON and not n == s:
        raise ValueError("equal-hand singleton requires equal trump lengths")
    if kind in (ShortnessKind.SHORT_HAND_SINGLETON, ShortnessKind.LONG_HAND_SINGLETON) and n == s:
        raise ValueError("equal trump lengths require equal-hand singleton label")
    east = tuple(card.rank.symbol for card in deal.hand(Seat.EAST).cards_in(trump))
    west = tuple(card.rank.symbol for card in deal.hand(Seat.WEST).cards_in(trump))
    trump_honors_n = _honors(north, trump)
    trump_honors_s = _honors(south, trump)
    side_honors_n = tuple(f"{suit.letter}{rank}" for suit in Suit if suit is not trump
                          for rank in _honors(north, suit))
    side_honors_s = tuple(f"{suit.letter}{rank}" for suit in Suit if suit is not trump
                          for rank in _honors(south, suit))
    entries = tuple(sum(Card(suit, Rank.ACE) in hand.cards for suit in Suit if suit is not trump)
                    for hand in (north, south))
    overruff = tuple(sum(card.rank > min(c.rank for c in deal.hand(item.hand).cards_in(trump))
                         for defender in (Seat.EAST, Seat.WEST)
                         for card in deal.hand(defender).cards_in(trump))
                     if deal.hand(item.hand).length(trump) else 0 for item in evidence)
    stage = CrossruffStage.NONE
    if len(evidence) >= 2 and len({item.hand for item in evidence}) >= 2 \
            and len({item.suit for item in evidence}) >= 2:
        stage = CrossruffStage.INDEPENDENT_SHORTNESS
        if all(item.ruffable_losers > 0 for item in evidence) and n and s and all(entries):
            stage = CrossruffStage.CROSSRUFF_AVAILABLE
    # "Established" is reserved for solver/play evidence; static shape never sets it.
    return CalibrationCase(
        deal.seed, deal.serialize(), trump, structure, kind, long_hand, short_hand,
        n == s, n + s, n, s, trump_honors_n, trump_honors_s, 13 - n - s,
        east, west, (len(east), len(west)), evaluate_hand(north).hcp + evaluate_hand(south).hcp,
        side_honors_n, side_honors_s, evidence,
        s if n > s else n if s > n else None,
        (n + s, 13 - n - s), trump_honors_n + trump_honors_s,
        min((item.ruffable_losers for item in evidence), default=0)
        if len(evidence) >= 2 and len({item.hand for item in evidence}) >= 2
        and len({item.suit for item in evidence}) >= 2 else 0,
        entries, overruff, stage,
    )


@lru_cache(maxsize=None)
def _length_patterns(structure: tuple[int, int], kind: ShortnessKind) -> tuple[tuple[tuple[int, ...], tuple[int, ...], int], ...]:
    n_trumps, s_trumps = structure
    patterns = []
    for n0 in range(14 - n_trumps):
        for n1 in range(14 - n_trumps - n0):
            n2 = 13 - n_trumps - n0 - n1
            if n2 > 13:
                continue
            for s0 in range(14 - s_trumps):
                for s1 in range(14 - s_trumps - s0):
                    s2 = 13 - s_trumps - s0 - s1
                    ns, ss = (n0, n1, n2), (s0, s1, s2)
                    if s2 > 13 or any(a + b > 13 for a, b in zip(ns, ss)):
                        continue
                    if kind is ShortnessKind.BASELINE and not all(x >= 2 for x in ns + ss):
                        continue
                    if kind is ShortnessKind.SHORT_HAND_SINGLETON and not (ss[0] == 1 and ns[0] >= 2):
                        continue
                    if kind is ShortnessKind.EQUAL_HAND_SINGLETON and not (
                        (ss[0] == 1 and ns[0] >= 2) or (ns[0] == 1 and ss[0] >= 2)
                    ):
                        continue
                    if kind is ShortnessKind.LONG_HAND_SINGLETON and not (ns[0] == 1 and ss[0] >= 2):
                        continue
                    if kind is ShortnessKind.RECIPROCAL_SINGLETONS and not (
                        ns[0] == 1 and ss[1] == 1 and ns[1] >= 2 and ss[0] >= 2
                    ):
                        continue
                    weight = 1
                    for a, b in zip(ns, ss):
                        weight *= comb(13, a) * comb(13 - a, b)
                    patterns.append((ns, ss, weight))
    if not patterns:
        raise ValueError("no legal side-suit patterns")
    return tuple(patterns)


def generate_conditioned_case(seed: int, structure: tuple[int, int],
                              kind: ShortnessKind, trump: Suit = Suit.SPADES) -> CalibrationCase:
    """Sample legal deals conditional on the requested structure and side lengths.

    Shape patterns receive their card-allocation combinatorial weights. Given
    partnership hands, the 26 remaining cards are shuffled uniformly to E/W.
    Thus known partnership shortness does not bias the defender split.
    """
    if structure not in TRUMP_STRUCTURES or not isinstance(kind, ShortnessKind) or not isinstance(trump, Suit):
        raise ValueError("unsupported structure, kind, or trump")
    if kind is ShortnessKind.MIXED_SHORTNESS:
        raise ValueError("mixed void/doubleton patterns are represented by analyze_case, not sampled in PT-1")
    rng = random.Random(seed)
    sides = tuple(suit for suit in Suit if suit is not trump)
    patterns = _length_patterns(structure, kind)
    ns, ss, _ = rng.choices(patterns, weights=[p[2] for p in patterns], k=1)[0]
    deck = full_deck()
    north_cards: list[Card] = []
    south_cards: list[Card] = []
    trumps = [card for card in deck if card.suit is trump]
    rng.shuffle(trumps)
    north_cards.extend(trumps[:structure[0]])
    south_cards.extend(trumps[structure[0]:sum(structure)])
    for suit, n_count, s_count in zip(sides, ns, ss):
        cards = [card for card in deck if card.suit is suit]
        rng.shuffle(cards)
        north_cards.extend(cards[:n_count])
        south_cards.extend(cards[n_count:n_count + s_count])
    used = set(north_cards + south_cards)
    remaining = [card for card in deck if card not in used]
    rng.shuffle(remaining)
    deal = Deal(seed, ((Seat.NORTH, Hand.from_cards(north_cards)),
                       (Seat.EAST, Hand.from_cards(remaining[:13])),
                       (Seat.SOUTH, Hand.from_cards(south_cards)),
                       (Seat.WEST, Hand.from_cards(remaining[13:]))))
    if kind is ShortnessKind.BASELINE:
        shorts: tuple[tuple[Seat, Suit], ...] = ()
    elif kind is ShortnessKind.SHORT_HAND_SINGLETON:
        shorts = ((Seat.SOUTH, sides[0]),)
    elif kind is ShortnessKind.EQUAL_HAND_SINGLETON:
        shorts = ((Seat.NORTH if deal.hand(Seat.NORTH).length(sides[0]) == 1
                   else Seat.SOUTH, sides[0]),)
    elif kind is ShortnessKind.LONG_HAND_SINGLETON:
        shorts = ((Seat.NORTH, sides[0]),)
    else:
        shorts = ((Seat.NORTH, sides[0]), (Seat.SOUTH, sides[1]))
    return analyze_case(deal, trump, kind, shorts)


@dataclass(frozen=True, slots=True)
class CalibrationBatch:
    structure: tuple[int, int]
    kind: ShortnessKind
    seed: int
    generated: int
    accepted: int
    records: tuple[CalibrationCase, ...]

    def summary(self) -> dict[str, object]:
        split = Counter(f"{a}-{b}" for case in self.records for a, b in (case.defender_trump_split,))
        honor = Counter(len(case.trump_honor_control) for case in self.records)
        losers = Counter(sum(item.ruffable_losers for item in case.short_suits) for case in self.records)
        unavailable = {name: None for name in (
            "mean_delta_tricks", "median_delta_tricks", "standard_deviation",
            "confidence_interval", "p_gain_0", "p_gain_ge_1", "p_gain_ge_2", "p_gain_ge_3")}
        return {"structure": list(self.structure), "kind": self.kind.value,
                "seed": self.seed, "generated": self.generated, "accepted": self.accepted,
                "outcome_status": "unavailable-no-double-dummy-solver",
                **unavailable,
                "by_oriented_defender_split": dict(sorted(split.items())),
                "by_trump_honor_count": dict(sorted(honor.items())),
                "by_ruffable_losers": dict(sorted(losers.items()))}


def run_calibration(structure: tuple[int, int], kind: ShortnessKind, *,
                    seed: int, accepted_target: int,
                    accept: Callable[[CalibrationCase], bool] | None = None,
                    max_generated: int | None = None) -> CalibrationBatch:
    if accepted_target < 0 or isinstance(accepted_target, bool):
        raise ValueError("accepted target must be nonnegative")
    if max_generated is None:
        max_generated = max(accepted_target * 10, 1)
    records: list[CalibrationCase] = []
    generated = 0
    while len(records) < accepted_target:
        if generated >= max_generated:
            raise RuntimeError("accepted target not reached within generation limit")
        case = generate_conditioned_case(seed + generated, structure, kind)
        generated += 1
        if accept is None or accept(case):
            records.append(case)
    return CalibrationBatch(structure, kind, seed, generated, len(records), tuple(records))
