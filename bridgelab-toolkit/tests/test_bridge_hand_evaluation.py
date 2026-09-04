from __future__ import annotations

import unittest

from bridge.evaluation import (
    ShapeClass,
    classify_shape,
    controls,
    distribution,
    evaluate_hand,
    high_card_points,
    suit_lengths,
)
from bridge.models import Hand, Suit


class HandEvaluationTests(unittest.TestCase):
    def test_hcp_uses_standard_4321_scale(self) -> None:
        hand = Hand.parse("AK84.QJ6.A75.K92")
        self.assertEqual(high_card_points(hand), 17)

    def test_controls_count_aces_twice_and_kings_once(self) -> None:
        hand = Hand.parse("AK84.QJ6.A75.K92")
        self.assertEqual(controls(hand), 6)

    def test_suit_lengths_use_shdc_order(self) -> None:
        hand = Hand.parse("AKQJ9.876.54.AT3")
        self.assertEqual(suit_lengths(hand), (5, 3, 2, 3))

    def test_distribution_is_sorted_shape(self) -> None:
        hand = Hand.parse("AKQJ9.876.54.AT3")
        self.assertEqual(distribution(hand), (5, 3, 3, 2))

    def test_4333_is_balanced(self) -> None:
        hand = Hand.parse("AKQJ.KQJ.876.543")
        self.assertEqual(classify_shape(hand), ShapeClass.BALANCED)

    def test_4432_is_balanced(self) -> None:
        hand = Hand.parse("AKQJ.KQJ9.876.54")
        self.assertEqual(classify_shape(hand), ShapeClass.BALANCED)

    def test_5332_is_balanced(self) -> None:
        hand = Hand.parse("AKQJ9.KQJ.876.54")
        self.assertEqual(classify_shape(hand), ShapeClass.BALANCED)

    def test_5422_is_semi_balanced(self) -> None:
        hand = Hand.parse("AKQJ9.KQJ9.87.54")
        self.assertEqual(classify_shape(hand), ShapeClass.SEMI_BALANCED)

    def test_6322_is_semi_balanced(self) -> None:
        hand = Hand.parse("AKQJ98.KQJ.87.54")
        self.assertEqual(classify_shape(hand), ShapeClass.SEMI_BALANCED)

    def test_5431_is_unbalanced(self) -> None:
        hand = Hand.parse("AKQJ9.KQJ8.876.5")
        self.assertEqual(classify_shape(hand), ShapeClass.UNBALANCED)

    def test_evaluate_hand_reports_shortage_facts(self) -> None:
        hand = Hand.parse("AKQJ98.KQJ8.876.-")
        result = evaluate_hand(hand)
        self.assertEqual(result.suit_lengths, (6, 4, 3, 0))
        self.assertEqual(result.distribution, (6, 4, 3, 0))
        self.assertEqual(result.voids, 1)
        self.assertEqual(result.singletons, 0)
        self.assertEqual(result.doubletons, 0)
        self.assertTrue(result.has_void)
        self.assertTrue(result.is_unbalanced)

    def test_evaluate_hand_reports_longest_suit(self) -> None:
        hand = Hand.parse("AKQJ9.KQJ8.87.54")
        result = evaluate_hand(hand)
        self.assertEqual(result.longest_length, 5)
        self.assertEqual(result.longest_suits, (Suit.SPADES,))

    def test_evaluate_hand_reports_tied_longest_suits(self) -> None:
        hand = Hand.parse("AKQJ.KQJ9.876.54")
        result = evaluate_hand(hand)
        self.assertEqual(result.longest_length, 4)
        self.assertEqual(result.longest_suits, (Suit.SPADES, Suit.HEARTS))

    def test_length_accessor(self) -> None:
        hand = Hand.parse("AKQJ9.KQJ.876.54")
        result = evaluate_hand(hand)
        self.assertEqual(result.length(Suit.SPADES), 5)
        self.assertEqual(result.length(Suit.CLUBS), 2)

    def test_non_hand_inputs_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            high_card_points("AKQJ.KQJ.876.543")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            controls(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
