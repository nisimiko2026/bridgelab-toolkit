from __future__ import annotations

import unittest

from bridge import Auction, BiddingContext, Call, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc_1d_responses import (
    SaycResponseToOneDiamondOneHeartRule,
    SaycResponseToOneDiamondOneSpadeRule,
    SaycResponseToOneDiamondPassRule,
    create_sayc_one_diamond_response_engine,
    sayc_one_diamond_response_rules,
)


def ctx(hand: str, calls=("1D", "P"), system="SAYC") -> BiddingContext:
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext(system),
    )


class SaycOneDiamondResponseTests(unittest.TestCase):
    def test_registry_is_fixed_and_ordered(self) -> None:
        self.assertEqual(
            [r.rule_id for r in sayc_one_diamond_response_rules()],
            [
                "sayc.response.1d.pass",
                "sayc.response.1d.1h",
                "sayc.response.1d.1s",
            ],
        )

    def test_weak_hand_passes(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("J842.976.854.Q92")
        )
        self.assertEqual(result.recommended_call, Call.pass_())

    def test_four_hearts_bids_1h(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("Q84.J982.K64.983")
        )
        self.assertEqual(result.recommended_call, Call.parse("1H"))

    def test_four_spades_without_four_hearts_bids_1s(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("J982.Q84.K64.983")
        )
        self.assertEqual(result.recommended_call, Call.parse("1S"))

    def test_both_four_card_majors_bid_hearts_first(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("J982.Q843.K64.98")
        )
        self.assertEqual(result.recommended_call, Call.parse("1H"))

    def test_five_five_majors_also_follow_source_hearts_first_instruction(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("QJ982.KJ843.64.8")
        )
        self.assertEqual(result.recommended_call, Call.parse("1H"))

    def test_spade_rule_is_not_applicable_with_four_hearts(self) -> None:
        decision = SaycResponseToOneDiamondOneSpadeRule().evaluate(
            ctx("J982.Q843.K64.98")
        )
        self.assertFalse(decision.applicable)

    def test_major_response_requires_six_hcp(self) -> None:
        heart = SaycResponseToOneDiamondOneHeartRule().evaluate(
            ctx("J84.J982.Q64.983")
        )
        spade = SaycResponseToOneDiamondOneSpadeRule().evaluate(
            ctx("J982.J84.Q64.983")
        )
        self.assertFalse(heart.applicable)
        self.assertFalse(spade.applicable)

    def test_no_major_clear_case_is_deliberately_unresolved(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("K83.Q92.J873.Q42")
        )
        self.assertFalse(result.has_recommendation)

    def test_diamond_support_case_is_deliberately_unresolved(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("K83.Q92.J8732.Q2")
        )
        self.assertFalse(result.has_recommendation)

    def test_club_response_case_is_deliberately_unresolved(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("K83.92.J83.AQ742")
        )
        self.assertFalse(result.has_recommendation)

    def test_rules_require_exact_uncontested_1d_response_position(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("Q84.J982.K64.983", calls=("1C", "P"))
        )
        self.assertFalse(result.has_recommendation)

    def test_rules_do_not_apply_after_opponent_action(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("Q84.J982.K64.983", calls=("1D", "1S"))
        )
        self.assertFalse(result.has_recommendation)

    def test_rules_require_sayc(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("Q84.J982.K64.983", system="Acol")
        )
        self.assertFalse(result.has_recommendation)

    def test_full_system_name_is_accepted(self) -> None:
        result = create_sayc_one_diamond_response_engine().evaluate(
            ctx("Q84.J982.K64.983", system="Standard American Yellow Card")
        )
        self.assertEqual(result.recommended_call, Call.parse("1H"))

    def test_pass_source_is_strength_categories(self) -> None:
        decision = SaycResponseToOneDiamondPassRule().evaluate(
            ctx("J842.976.854.Q92")
        )
        self.assertEqual(
            [s.serialize() for s in decision.sources],
            ["bidding/natural-bids/responses/response-to-1-diamond#Strength Categories"],
        )

    def test_heart_sources_include_explicit_major_sections(self) -> None:
        decision = SaycResponseToOneDiamondOneHeartRule().evaluate(
            ctx("Q84.J982.K64.983")
        )
        self.assertEqual(
            {s.serialize() for s in decision.sources},
            {
                "bidding/natural-bids/responses/response-to-1-diamond#Responder's Priorities",
                "bidding/natural-bids/responses/response-to-1-diamond#Responding with a Major Suit",
                "bidding/natural-bids/responses/response-to-1-diamond#1♥",
            },
        )

    def test_spade_sources_include_explicit_major_sections(self) -> None:
        decision = SaycResponseToOneDiamondOneSpadeRule().evaluate(
            ctx("J982.Q84.K64.983")
        )
        self.assertEqual(
            {s.serialize() for s in decision.sources},
            {
                "bidding/natural-bids/responses/response-to-1-diamond#Responder's Priorities",
                "bidding/natural-bids/responses/response-to-1-diamond#Responding with a Major Suit",
                "bidding/natural-bids/responses/response-to-1-diamond#1♠",
            },
        )

    def test_rule_candidates_are_legal_in_position(self) -> None:
        for hand in (
            "J842.976.854.Q92",
            "Q84.J982.K64.983",
            "J982.Q84.K64.983",
            "J982.Q843.K64.98",
        ):
            position = ctx(hand)
            result = create_sayc_one_diamond_response_engine().evaluate(position)
            self.assertIsNotNone(result.recommended_call)
            self.assertTrue(position.auction.is_legal(result.recommended_call))


if __name__ == "__main__":
    unittest.main()
