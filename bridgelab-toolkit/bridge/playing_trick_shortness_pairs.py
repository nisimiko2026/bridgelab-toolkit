"""Exact, reversible low-card shortness controls for PT-1B (no bidding logic)."""

from __future__ import annotations

from dataclasses import dataclass
import random

from .deals import Deal
from .models import Card, Hand, Rank, Seat, Suit
from .playing_trick_calibration import CalibrationCase, ShortnessKind


@dataclass(frozen=True, slots=True)
class CardExchange:
    """The two physical card moves in one partnership exchange."""

    added_card: Card
    added_from: Seat
    added_to: Seat
    removed_card: Card
    removed_from: Seat
    removed_to: Seat
    source_shape_before: tuple[int, int, int, int]
    opposite_shape_before: tuple[int, int, int, int]
    source_shape_after: tuple[int, int, int, int]
    opposite_shape_after: tuple[int, int, int, int]

    @property
    def added_suit(self) -> Suit:
        return self.added_card.suit

    @property
    def removed_suit(self) -> Suit:
        return self.removed_card.suit

    def inverse(self) -> CardExchange:
        return CardExchange(self.removed_card, self.removed_to, self.removed_from,
                            self.added_card, self.added_to, self.added_from,
                            self.source_shape_after, self.opposite_shape_after,
                            self.source_shape_before, self.opposite_shape_before)


@dataclass(frozen=True, slots=True)
class SelectedControl:
    deal: Deal
    exchanges: tuple[CardExchange, ...]
    candidate_exchange_count: int
    selected_exchange_index: int


@dataclass(frozen=True, slots=True)
class ReciprocalControls:
    reciprocal: Deal
    north_removed: Deal
    south_removed: Deal
    neither: Deal
    north_exchange: CardExchange
    south_exchange: CardExchange
    south_exchange_after_north: CardExchange
    north_exchange_after_south: CardExchange
    candidate_exchange_count: int
    selected_exchange_index: int


def _spots(hand: Hand, suit: Suit) -> tuple[Card, ...]:
    return tuple(sorted((card for card in hand.cards_in(suit)
                         if card.rank < Rank.JACK), key=lambda card: int(card.rank)))


def _exchange(deal: Deal, added: Card, added_from: Seat, removed: Card,
              removed_from: Seat) -> tuple[Deal, CardExchange]:
    if added_from.partner() is not removed_from or added_from is removed_from:
        raise ValueError("cards must move between partners")
    to_hand, from_hand = deal.hand(removed_from), deal.hand(added_from)
    if added not in from_hand.cards or removed not in to_hand.cards:
        raise ValueError("exchange cards absent from specified source hands")
    if added.rank >= Rank.JACK or removed.rank >= Rank.JACK:
        raise ValueError("only low spot cards may move")
    mapping = deal.mapping
    mapping[removed_from] = Hand.from_cards(to_hand.cards - {removed} | {added})
    mapping[added_from] = Hand.from_cards(from_hand.cards - {added} | {removed})
    result = Deal(deal.seed, tuple((seat, mapping[seat]) for seat in Seat))
    record = CardExchange(added, added_from, removed_from, removed,
                          removed_from, added_from, to_hand.shape, from_hand.shape,
                          result.hand(removed_from).shape, result.hand(added_from).shape)
    return result, record


def apply_exchange(deal: Deal, exchange: CardExchange) -> Deal:
    if (deal.hand(exchange.added_to).shape != exchange.source_shape_before
            or deal.hand(exchange.added_from).shape != exchange.opposite_shape_before):
        raise ValueError("exchange starting shapes do not match")
    result, actual = _exchange(deal, exchange.added_card, exchange.added_from,
                               exchange.removed_card, exchange.removed_from)
    if actual != exchange:
        raise ValueError("exchange record does not match physical card moves")
    return result


def _preserved(source: Deal, control: Deal, trump: Suit) -> bool:
    from .evaluation import evaluate_hand
    if any(source.hand(seat) != control.hand(seat)
           for seat in (Seat.EAST, Seat.WEST)):
        return False
    for seat in (Seat.NORTH, Seat.SOUTH):
        before, after = source.hand(seat), control.hand(seat)
        if before.length(trump) != after.length(trump):
            return False
        if evaluate_hand(before).hcp != evaluate_hand(after).hcp:
            return False
        for suit in Suit:
            if {card for card in before.cards_in(suit) if card.rank >= Rank.JACK} != {
                    card for card in after.cards_in(suit) if card.rank >= Rank.JACK}:
                return False
    return True


def singleton_candidates(deal: Deal, short_hand: Seat, studied_suit: Suit,
                         trump: Suit) -> tuple[tuple[Deal, CardExchange], ...]:
    """Enumerate all legal one-step controls in stable suit/rank order.

    Compensation suit and opposite studied holding remain at least doubletons,
    so the exchange does not create another studied shortness exposure.
    """
    if short_hand not in (Seat.NORTH, Seat.SOUTH) or studied_suit is trump:
        raise ValueError("partnership short hand and nontrump suit required")
    other = short_hand.partner()
    if deal.hand(short_hand).length(studied_suit) not in (1, 2):
        return ()
    if deal.hand(other).length(studied_suit) < 3:
        return ()
    results = []
    for incoming in _spots(deal.hand(other), studied_suit):
        for suit in Suit:
            if suit in (studied_suit, trump) or deal.hand(short_hand).length(suit) < 3:
                continue
            for outgoing in _spots(deal.hand(short_hand), suit):
                control, exchange = _exchange(deal, incoming, other, outgoing, short_hand)
                if _preserved(deal, control, trump):
                    results.append((control, exchange))
    return tuple(results)


def select_singleton_control(case: CalibrationCase, *, length: int,
                             selection_seed: int) -> SelectedControl | None:
    if case.shortness_kind not in (ShortnessKind.SHORT_HAND_SINGLETON,
                                   ShortnessKind.LONG_HAND_SINGLETON,
                                   ShortnessKind.EQUAL_HAND_SINGLETON):
        raise ValueError("ordinary singleton source required")
    if length not in (2, 3):
        raise ValueError("control length must be 2 or 3")
    item = case.short_suits[0]
    source = Deal.parse(case.deal_id, seed=case.deal_seed)
    first = singleton_candidates(source, item.hand, item.suit, case.trump_suit)
    if length == 2:
        paths = tuple((deal, (exchange,)) for deal, exchange in first)
    else:
        paths = tuple((final, (exchange, second))
                      for intermediate, exchange in first
                      for final, second in singleton_candidates(
                          intermediate, item.hand, item.suit, case.trump_suit))
    if not paths:
        return None
    index = random.Random(selection_seed).randrange(len(paths))
    control, exchanges = paths[index]
    if control.hand(item.hand).length(item.suit) != length:
        raise AssertionError("incorrect control length")
    replay = control
    for exchange in reversed(exchanges):
        replay = apply_exchange(replay, exchange.inverse())
    if replay.serialize() != source.serialize() or not _preserved(source, control, case.trump_suit):
        raise AssertionError("control failed exact preservation or reverse replay")
    return SelectedControl(control, exchanges, len(paths), index)


def reciprocal_candidates(case: CalibrationCase) -> tuple[ReciprocalControls, ...]:
    if case.shortness_kind is not ShortnessKind.RECIPROCAL_SINGLETONS:
        raise ValueError("reciprocal singleton source required")
    source = Deal.parse(case.deal_id, seed=case.deal_seed)
    north_suit = next(item.suit for item in case.short_suits if item.hand is Seat.NORTH)
    south_suit = next(item.suit for item in case.short_suits if item.hand is Seat.SOUTH)
    compensation = next(suit for suit in Suit
                        if suit not in (case.trump_suit, north_suit, south_suit))
    north, south = source.hand(Seat.NORTH), source.hand(Seat.SOUTH)
    if (south.length(north_suit) < 3 or north.length(south_suit) < 3
            or north.length(compensation) < 3 or south.length(compensation) < 3):
        return ()
    results = []
    for x in _spots(south, north_suit):
        for y in _spots(north, south_suit):
            for zn in _spots(north, compensation):
                for zs in _spots(south, compensation):
                    north_removed, nx = _exchange(source, x, Seat.SOUTH, zn, Seat.NORTH)
                    south_removed, sx = _exchange(source, y, Seat.NORTH, zs, Seat.SOUTH)
                    neither, sx_after = _exchange(north_removed, y, Seat.NORTH, zs, Seat.SOUTH)
                    reverse_path, nx_after = _exchange(south_removed, x, Seat.SOUTH, zn, Seat.NORTH)
                    if neither.serialize() != reverse_path.serialize():
                        raise AssertionError("reciprocal square does not commute")
                    if not all(_preserved(source, variant, case.trump_suit)
                               for variant in (north_removed, south_removed, neither)):
                        continue
                    if (apply_exchange(north_removed, nx.inverse()).serialize() != source.serialize()
                            or apply_exchange(south_removed, sx.inverse()).serialize() != source.serialize()
                            or apply_exchange(neither, sx_after.inverse()).serialize() != north_removed.serialize()
                            or apply_exchange(neither, nx_after.inverse()).serialize() != south_removed.serialize()):
                        raise AssertionError("reciprocal control failed reverse replay")
                    results.append(ReciprocalControls(source, north_removed,
                                                      south_removed, neither, nx, sx,
                                                      sx_after, nx_after, 0, 0))
    return tuple(results)


def select_reciprocal_controls(case: CalibrationCase, *,
                               selection_seed: int) -> ReciprocalControls | None:
    candidates = reciprocal_candidates(case)
    if not candidates:
        return None
    index = random.Random(selection_seed).randrange(len(candidates))
    chosen = candidates[index]
    return ReciprocalControls(chosen.reciprocal, chosen.north_removed,
                              chosen.south_removed, chosen.neither,
                              chosen.north_exchange, chosen.south_exchange,
                              chosen.south_exchange_after_north,
                              chosen.north_exchange_after_south,
                              len(candidates), index)


def select_direct_reciprocal_control(case: CalibrationCase, *,
                                     selection_seed: int) -> SelectedControl | None:
    """Remove both studied singletons with one cross-suit low-card exchange."""
    if case.shortness_kind is not ShortnessKind.RECIPROCAL_SINGLETONS:
        raise ValueError("reciprocal singleton source required")
    source = Deal.parse(case.deal_id, seed=case.deal_seed)
    north_suit = next(item.suit for item in case.short_suits if item.hand is Seat.NORTH)
    south_suit = next(item.suit for item in case.short_suits if item.hand is Seat.SOUTH)
    north, south = source.hand(Seat.NORTH), source.hand(Seat.SOUTH)
    if north.length(south_suit) < 3 or south.length(north_suit) < 3:
        return None
    paths = []
    for x in _spots(south, north_suit):
        for y in _spots(north, south_suit):
            control, exchange = _exchange(source, x, Seat.SOUTH, y, Seat.NORTH)
            if _preserved(source, control, case.trump_suit):
                paths.append((control, exchange))
    if not paths:
        return None
    index = random.Random(selection_seed).randrange(len(paths))
    control, exchange = paths[index]
    if apply_exchange(control, exchange.inverse()).serialize() != source.serialize():
        raise AssertionError("direct reciprocal control failed reverse replay")
    return SelectedControl(control, (exchange,), len(paths), index)
