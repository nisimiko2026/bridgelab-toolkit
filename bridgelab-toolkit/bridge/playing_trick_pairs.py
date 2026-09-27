"""Targeted, reproducible paired trump-allocation experiments.

One low trump moves from North to South while one low card in an unstudied
side suit moves back. The 52-card deck, defenders, partnership HCP, honors,
entries, and studied ruffable losers remain identical within a pair/triple.
"""

from __future__ import annotations

from dataclasses import dataclass

from .deals import Deal
from .models import Card, Hand, Rank, Seat, Suit
from .playing_trick_calibration import (
    CalibrationCase, ShortnessKind, analyze_case, generate_conditioned_case,
)


@dataclass(frozen=True, slots=True)
class MatchedSet:
    pair_id: str
    cases: tuple[CalibrationCase, ...]

    def __post_init__(self) -> None:
        if len(self.cases) not in (2, 3):
            raise ValueError("matched set needs two or three structural variants")
        first = self.cases[0]
        for case in self.cases[1:]:
            if not (
                case.partnership_trumps == first.partnership_trumps
                and case.partnership_hcp == first.partnership_hcp
                and case.trump_honors_north == first.trump_honors_north
                and case.trump_honors_south == first.trump_honors_south
                and case.side_honors_north == first.side_honors_north
                and case.side_honors_south == first.side_honors_south
                and case.side_ace_entries == first.side_ace_entries
                and case.defender_trump_split == first.defender_trump_split
                and tuple((s.hand, s.suit, s.ruffable_losers) for s in case.short_suits)
                == tuple((s.hand, s.suit, s.ruffable_losers) for s in first.short_suits)
            ):
                raise ValueError("matched set changed a controlled feature")


def _transfer_low_trump(deal: Deal, trump: Suit,
                        studied_suits: frozenset[Suit]) -> Deal | None:
    north, south = deal.hand(Seat.NORTH), deal.hand(Seat.SOUTH)
    trump_candidates = sorted(
        (card for card in north.cards_in(trump) if card.rank < Rank.JACK),
        key=lambda card: int(card.rank),
    )
    side_candidates = sorted(
        (card for card in south.cards if card.suit is not trump
         and card.suit not in studied_suits and card.rank < Rank.JACK),
        key=lambda card: (int(card.suit), int(card.rank)),
    )
    if not trump_candidates or not side_candidates:
        return None
    moving_trump, moving_side = trump_candidates[0], side_candidates[0]
    north_cards = north.cards - {moving_trump} | {moving_side}
    south_cards = south.cards - {moving_side} | {moving_trump}
    return Deal(deal.seed, (
        (Seat.NORTH, Hand.from_cards(north_cards)),
        (Seat.EAST, deal.hand(Seat.EAST)),
        (Seat.SOUTH, Hand.from_cards(south_cards)),
        (Seat.WEST, deal.hand(Seat.WEST)),
    ))


def build_matched_set(seed: int, source_structure: tuple[int, int],
                      kind: ShortnessKind, *, trump: Suit = Suit.SPADES) -> MatchedSet | None:
    if source_structure not in ((6, 3), (7, 3)):
        raise ValueError("PT-1A paired source must be 6-3 or 7-3")
    if kind not in (ShortnessKind.SHORT_HAND_SINGLETON,
                    ShortnessKind.RECIPROCAL_SINGLETONS):
        raise ValueError("PT-1A pairs require a studied singleton kind")
    base = generate_conditioned_case(seed, source_structure, kind, trump)
    deal = Deal.parse(base.deal_id, seed=seed)
    studied = tuple((item.hand, item.suit) for item in base.short_suits)
    excluded = frozenset(suit for _, suit in studied)
    cases = [base]
    for step in range(1 if source_structure == (6, 3) else 2):
        transformed = _transfer_low_trump(deal, trump, excluded)
        if transformed is None:
            return None
        deal = transformed
        next_kind = (ShortnessKind.EQUAL_HAND_SINGLETON
                     if kind is ShortnessKind.SHORT_HAND_SINGLETON
                     and deal.hand(Seat.NORTH).length(trump) == deal.hand(Seat.SOUTH).length(trump)
                     else kind)
        cases.append(analyze_case(deal, trump, next_kind, studied))
    expected = ((6, 3), (5, 4)) if source_structure == (6, 3) \
        else ((7, 3), (6, 4), (5, 5))
    if tuple(case.trump_structure for case in cases) != expected:
        raise AssertionError("paired transfer did not produce requested structures")
    return MatchedSet(f"{source_structure[0]}-{source_structure[1]}:{kind.value}:{seed}", tuple(cases))


@dataclass(frozen=True, slots=True)
class MatchedBatch:
    source_structure: tuple[int, int]
    kind: ShortnessKind
    seed: int
    generated: int
    accepted: int
    sets: tuple[MatchedSet, ...]


def generate_matched_sets(source_structure: tuple[int, int], kind: ShortnessKind,
                          *, seed: int, accepted_target: int,
                          max_generated: int | None = None) -> MatchedBatch:
    if not isinstance(accepted_target, int) or isinstance(accepted_target, bool) or accepted_target < 0:
        raise ValueError("accepted target must be a nonnegative integer")
    if max_generated is None:
        max_generated = max(accepted_target * 10, 1)
    generated = 0
    sets: list[MatchedSet] = []
    while len(sets) < accepted_target:
        if generated >= max_generated:
            raise RuntimeError("matched accepted target not reached")
        matched = build_matched_set(seed + generated, source_structure, kind)
        generated += 1
        if matched is not None:
            sets.append(matched)
    return MatchedBatch(source_structure, kind, seed, generated, len(sets), tuple(sets))
