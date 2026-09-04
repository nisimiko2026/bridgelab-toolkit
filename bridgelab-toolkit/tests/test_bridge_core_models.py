from __future__ import annotations

import unittest

from bridge.models import Card, Hand, Rank, Seat, Suit, Vulnerability


class SuitRankCardTests(unittest.TestCase):
    def test_suit_parsing_and_symbols(self):
        self.assertIs(Suit.parse("spades"), Suit.SPADES)
        self.assertIs(Suit.parse("♥"), Suit.HEARTS)
        self.assertEqual(Suit.DIAMONDS.letter, "D")

    def test_rank_parsing(self):
        self.assertIs(Rank.parse("10"), Rank.TEN)
        self.assertIs(Rank.parse("t"), Rank.TEN)
        self.assertEqual(Rank.ACE.symbol, "A")

    def test_card_parsing_and_serialization(self):
        self.assertEqual(Card.parse("AS"), Card(Suit.SPADES, Rank.ACE))
        self.assertEqual(Card.parse("10h").serialize(), "TH")
        self.assertEqual(str(Card.parse("Q♦")), "Q♦")

    def test_invalid_card_rejected(self):
        with self.assertRaises(ValueError):
            Card.parse("1S")


class SeatVulnerabilityTests(unittest.TestCase):
    def test_clockwise_seat_rotation_and_partner(self):
        self.assertIs(Seat.NORTH.next(), Seat.EAST)
        self.assertIs(Seat.WEST.next(), Seat.NORTH)
        self.assertIs(Seat.NORTH.partner(), Seat.SOUTH)
        self.assertTrue(Seat.EAST.is_partner(Seat.WEST))

    def test_vulnerability_by_partnership(self):
        self.assertTrue(Vulnerability.NS.is_vulnerable(Seat.NORTH))
        self.assertTrue(Vulnerability.NS.is_vulnerable(Seat.SOUTH))
        self.assertFalse(Vulnerability.NS.is_vulnerable(Seat.EAST))
        self.assertTrue(Vulnerability.BOTH.is_vulnerable(Seat.WEST))
        self.assertFalse(Vulnerability.NONE.is_vulnerable(Seat.NORTH))


class HandTests(unittest.TestCase):
    SAMPLE = "AKQ.JT9.876.5432"

    def test_parse_canonical_hand(self):
        hand = Hand.parse(self.SAMPLE)
        self.assertEqual(len(hand.cards), 13)
        self.assertEqual(hand.shape, (3, 3, 3, 4))
        self.assertEqual(hand.serialize(), self.SAMPLE)

    def test_void_serialization(self):
        hand = Hand.parse("AKQJT98765432.-.-.-")
        self.assertEqual(hand.shape, (13, 0, 0, 0))
        self.assertEqual(hand.serialize(), "AKQJT98765432.-.-.-")

    def test_duplicate_card_in_same_suit_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            Hand.parse("AAK.QJT.876.5432")

    def test_wrong_card_count_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly 13"):
            Hand.parse("AKQ.JT9.876.543")

    def test_wrong_suit_group_count_rejected(self):
        with self.assertRaisesRegex(ValueError, "four dot-separated"):
            Hand.parse("AKQ.JT9.8765432")

    def test_cards_in_returns_rank_order(self):
        hand = Hand.parse(self.SAMPLE)
        self.assertEqual(
            tuple(card.rank for card in hand.cards_in(Suit.CLUBS)),
            (Rank.FIVE, Rank.FOUR, Rank.THREE, Rank.TWO),
        )

    def test_hand_is_immutable(self):
        hand = Hand.parse(self.SAMPLE)
        with self.assertRaises(Exception):
            hand.cards = frozenset()
