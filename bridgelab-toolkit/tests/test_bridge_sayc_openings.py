from __future__ import annotations

import unittest

from bridge import (
    Auction,
    BiddingContext,
    Call,
    Hand,
    Seat,
    SystemContext,
    Vulnerability,
)
from bridge.sayc import (
    SaycOneClubOpeningRule,
    SaycOneDiamondOpeningRule,
    SaycOneHeartOpeningRule,
    SaycOneNotrumpOpeningRule,
    SaycOneSpadeOpeningRule,
    create_sayc_opening_engine,
    sayc_opening_rules,
)


def context(hand_text: str, calls=(), system: str = "SAYC") -> BiddingContext:
    return BiddingContext.create(
        hand=Hand.parse(hand_text),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext(system),
    )


class SaycOpeningRulesTests(unittest.TestCase):
    def test_registry_contains_exact_controlled_subset(self) -> None:
        rules = sayc_opening_rules()
        self.assertEqual(
            [rule.rule_id for rule in rules],
            [
                "sayc.opening.1nt",
                "sayc.opening.1h",
                "sayc.opening.1s",
                "sayc.opening.1c",
                "sayc.opening.1d",
            ],
        )

    def test_clear_16_hcp_balanced_hand_opens_1nt(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ84.KJ6.A75.K92")
        )
        self.assertEqual(result.recommended_call, Call.parse("1NT"))
        self.assertEqual(result.recommended.rule_id, "sayc.opening.1nt")

    def test_1nt_source_trace_points_to_canonical_articles(self) -> None:
        decision = SaycOneNotrumpOpeningRule().evaluate(
            context("AQ84.KJ6.A75.K92")
        )
        self.assertEqual(
            [source.serialize() for source in decision.sources],
            [
                "bidding/systems/sayc#Opening Bid Requirements",
                "bidding/natural-bids/opening-bids/1nt-opening#Typical Requirements",
                "bidding/natural-bids/opening-bids/1nt-opening#Balanced Distribution",
            ],
        )

    def test_14_hcp_balanced_hand_does_not_trigger_1nt_rule(self) -> None:
        decision = SaycOneNotrumpOpeningRule().evaluate(
            context("AQ84.KJ6.975.K92")
        )
        self.assertFalse(decision.applicable)

    def test_18_hcp_balanced_hand_does_not_trigger_1nt_rule(self) -> None:
        decision = SaycOneNotrumpOpeningRule().evaluate(
            context("AQ84.AJ6.A75.K92")
        )
        self.assertFalse(decision.applicable)

    def test_five_card_major_is_deliberately_excluded_from_1nt_subset(self) -> None:
        decision = SaycOneNotrumpOpeningRule().evaluate(
            context("AQJ84.KJ6.A75.K9")
        )
        self.assertFalse(decision.applicable)

    def test_longer_five_card_hearts_open_1h(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("K84.AQJ76.A75.92")
        )
        self.assertEqual(result.recommended_call, Call.parse("1H"))

    def test_longer_five_card_spades_open_1s(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQJ76.K84.A75.92")
        )
        self.assertEqual(result.recommended_call, Call.parse("1S"))

    def test_five_five_majors_are_deliberately_left_unresolved(self) -> None:
        engine = create_sayc_opening_engine()
        result = engine.evaluate(context("AQJ76.KQJ84.A7.2"))
        self.assertFalse(result.has_recommendation)

    def test_longer_clubs_open_1c(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ84.KJ6.7.KJ932")
        )
        self.assertEqual(result.recommended_call, Call.parse("1C"))

    def test_three_three_minors_open_1c(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ84.KJ76.A75.K9")
        )
        # 4-4-3-2, 14 HCP: not 1NT; no five-card major; 3 diamonds, 2 clubs
        self.assertNotEqual(result.recommended_call, Call.parse("1C"))

        result = create_sayc_opening_engine().evaluate(
            context("K984.QJ6.A75.K92")
        )
        self.assertEqual(result.recommended_call, Call.parse("1C"))

    def test_longer_diamonds_open_1d(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ84.KJ6.AJ932.7")
        )
        self.assertEqual(result.recommended_call, Call.parse("1D"))

    def test_four_four_minors_open_1d(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ8.K6.AJ93.9432")
        )
        self.assertEqual(result.recommended_call, Call.parse("1D"))

    def test_equal_five_five_minors_are_left_unresolved(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ.K.AJ932.QJ932")
        )
        self.assertFalse(result.has_recommendation)

    def test_rules_accept_passes_before_an_unopened_position(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ84.KJ6.A75.K92", calls=["P"])
        )
        self.assertEqual(result.recommended_call, Call.parse("1NT"))

    def test_rules_do_not_apply_after_a_bid(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ84.KJ6.A75.K92", calls=["1C"])
        )
        self.assertFalse(result.has_recommendation)

    def test_rules_do_not_apply_to_non_sayc_system(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context("AQ84.KJ6.A75.K92", system="Acol")
        )
        self.assertFalse(result.has_recommendation)

    def test_full_system_name_is_accepted(self) -> None:
        result = create_sayc_opening_engine().evaluate(
            context(
                "AQ84.KJ6.A75.K92",
                system="Standard American Yellow Card",
            )
        )
        self.assertEqual(result.recommended_call, Call.parse("1NT"))

    def test_major_rules_require_opening_values_in_controlled_subset(self) -> None:
        hand = context("KJ876.Q84.A75.92")
        self.assertFalse(SaycOneSpadeOpeningRule().evaluate(hand).applicable)

    def test_minor_rules_require_opening_values_in_controlled_subset(self) -> None:
        hand = context("Q84.J76.A75.K932")
        self.assertFalse(SaycOneClubOpeningRule().evaluate(hand).applicable)
        self.assertFalse(SaycOneDiamondOpeningRule().evaluate(hand).applicable)

    def test_major_rule_sources_are_canonical(self) -> None:
        heart = SaycOneHeartOpeningRule().evaluate(
            context("K84.AQJ76.A75.92")
        )
        spade = SaycOneSpadeOpeningRule().evaluate(
            context("AQJ76.K84.A75.92")
        )
        self.assertIn(
            "bidding/systems/sayc#Five-Card Majors",
            [s.serialize() for s in heart.sources],
        )
        self.assertIn(
            "bidding/natural-bids/opening-bids/1-spade#Spade Length",
            [s.serialize() for s in spade.sources],
        )


if __name__ == "__main__":
    unittest.main()
