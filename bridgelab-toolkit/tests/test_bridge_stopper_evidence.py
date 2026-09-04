from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from bridge import (
    Hand,
    Rank,
    Suit,
    SuitHonorEvidence,
    all_suit_honor_evidence,
    evaluate_hand,
    suit_honor_evidence,
)


class SuitHonorEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hand = Hand.parse("AQ84.KJ6.T75.932")

    def test_one_suit_evidence_contains_length_and_top_honors(self) -> None:
        evidence = suit_honor_evidence(self.hand, Suit.SPADES)
        self.assertEqual(evidence.suit, Suit.SPADES)
        self.assertEqual(evidence.length, 4)
        self.assertEqual(evidence.honors, (Rank.ACE, Rank.QUEEN))

    def test_ten_is_recorded_as_raw_evidence(self) -> None:
        evidence = suit_honor_evidence(self.hand, Suit.DIAMONDS)
        self.assertEqual(evidence.honors, (Rank.TEN,))
        self.assertTrue(evidence.has_ten)

    def test_low_cards_do_not_appear_as_honors(self) -> None:
        evidence = suit_honor_evidence(self.hand, Suit.CLUBS)
        self.assertEqual(evidence.length, 3)
        self.assertEqual(evidence.honors, ())
        self.assertEqual(evidence.honor_count, 0)

    def test_boolean_honor_accessors_are_objective(self) -> None:
        evidence = suit_honor_evidence(self.hand, Suit.HEARTS)
        self.assertFalse(evidence.has_ace)
        self.assertTrue(evidence.has_king)
        self.assertFalse(evidence.has_queen)
        self.assertTrue(evidence.has_jack)
        self.assertFalse(evidence.has_ten)
        self.assertEqual(evidence.honor_count, 2)

    def test_all_suit_evidence_uses_shdc_order(self) -> None:
        evidence = all_suit_honor_evidence(self.hand)
        self.assertEqual(
            [item.suit for item in evidence],
            [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS],
        )
        self.assertEqual([item.length for item in evidence], [4, 3, 3, 3])

    def test_hand_evaluation_embeds_same_evidence(self) -> None:
        evaluation = evaluate_hand(self.hand)
        self.assertEqual(
            evaluation.honor_evidence(Suit.SPADES),
            suit_honor_evidence(self.hand, Suit.SPADES),
        )

    def test_evidence_is_immutable(self) -> None:
        evidence = suit_honor_evidence(self.hand, Suit.SPADES)
        with self.assertRaises(FrozenInstanceError):
            evidence.length = 5  # type: ignore[misc]

    def test_function_requires_hand(self) -> None:
        with self.assertRaises(TypeError):
            suit_honor_evidence(None, Suit.SPADES)  # type: ignore[arg-type]

    def test_function_requires_suit(self) -> None:
        with self.assertRaises(TypeError):
            suit_honor_evidence(self.hand, "S")  # type: ignore[arg-type]

    def test_evaluation_accessor_requires_suit(self) -> None:
        evaluation = evaluate_hand(self.hand)
        with self.assertRaises(TypeError):
            evaluation.honor_evidence("S")  # type: ignore[arg-type]

    def test_no_stopper_classification_is_exposed(self) -> None:
        evidence = suit_honor_evidence(self.hand, Suit.SPADES)
        self.assertFalse(hasattr(evidence, "is_stopper"))
        self.assertFalse(hasattr(evidence, "stopper"))
        self.assertFalse(hasattr(evidence, "stopper_quality"))


if __name__ == "__main__":
    unittest.main()
