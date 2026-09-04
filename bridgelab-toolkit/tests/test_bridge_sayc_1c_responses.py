from __future__ import annotations

import unittest

from bridge import Auction, BiddingContext, Call, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc_responses import (
    SaycResponseToOneClubOneDiamondRule,
    SaycResponseToOneClubOneHeartRule,
    SaycResponseToOneClubOneNotrumpRule,
    SaycResponseToOneClubOneSpadeRule,
    SaycResponseToOneClubPassRule,
    create_sayc_one_club_response_engine,
    sayc_one_club_response_rules,
)


def ctx(hand: str, calls=("1C", "P"), system="SAYC") -> BiddingContext:
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext(system),
    )


class SaycOneClubResponseTests(unittest.TestCase):
    def test_registry_is_fixed_and_ordered(self) -> None:
        self.assertEqual(
            [r.rule_id for r in sayc_one_club_response_rules()],
            [
                "sayc.response.1c.pass",
                "sayc.response.1c.1h",
                "sayc.response.1c.1s",
                "sayc.response.1c.1d",
                "sayc.response.1c.1nt",
            ],
        )

    def test_weak_hand_passes(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("J842.976.854.Q92")
        )
        self.assertEqual(result.recommended_call, Call.pass_())

    def test_six_hcp_four_hearts_without_four_spades_bids_1h(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("Q84.J982.K64.983")
        )
        self.assertEqual(result.recommended_call, Call.parse("1H"))

    def test_six_hcp_four_spades_without_four_hearts_bids_1s(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("J982.Q84.K64.983")
        )
        self.assertEqual(result.recommended_call, Call.parse("1S"))

    def test_both_four_card_majors_are_deliberately_unresolved(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("J982.Q843.K64.98")
        )
        self.assertFalse(result.has_recommendation)

    def test_both_majors_longer_hearts_bids_1h(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("J982.KQ843.64.98")
        )
        self.assertEqual(result.recommended_call, Call.parse("1H"))

    def test_both_majors_longer_spades_bids_1s(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("KQJ82.J843.64.98")
        )
        self.assertEqual(result.recommended_call, Call.parse("1S"))

    def test_both_five_card_majors_remain_unresolved(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("KJ982.QJ843.64.9")
        )
        self.assertFalse(result.has_recommendation)

    def test_longer_diamonds_no_major_bids_1d(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("K73.82.AQ742.J83")
        )
        self.assertEqual(result.recommended_call, Call.parse("1D"))

    def test_diamond_rule_requires_diamonds_longer_than_clubs(self) -> None:
        decision = SaycResponseToOneClubOneDiamondRule().evaluate(
            ctx("K73.82.AQ74.J843")
        )
        self.assertFalse(decision.applicable)

    def test_diamond_rule_rejects_four_card_major(self) -> None:
        decision = SaycResponseToOneClubOneDiamondRule().evaluate(
            ctx("K873.82.AQ74.J83")
        )
        self.assertFalse(decision.applicable)

    def test_rules_require_exact_uncontested_1c_response_position(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("Q84.J982.K64.983", calls=("1D", "P"))
        )
        self.assertFalse(result.has_recommendation)

    def test_rules_do_not_apply_after_opponent_action(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("Q84.J982.K64.983", calls=("1C", "1H"))
        )
        self.assertFalse(result.has_recommendation)

    def test_rules_require_sayc(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("Q84.J982.K64.983", system="Acol")
        )
        self.assertFalse(result.has_recommendation)

    def test_full_system_name_is_accepted(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("Q84.J982.K64.983", system="Standard American Yellow Card")
        )
        self.assertEqual(result.recommended_call, Call.parse("1H"))

    def test_pass_source_is_strength_categories(self) -> None:
        decision = SaycResponseToOneClubPassRule().evaluate(
            ctx("J842.976.854.Q92")
        )
        self.assertEqual(
            [s.serialize() for s in decision.sources],
            ["bidding/natural-bids/responses/response-to-1-club#Strength Categories"],
        )

    def test_major_sources_point_to_canonical_sections(self) -> None:
        heart = SaycResponseToOneClubOneHeartRule().evaluate(
            ctx("Q84.J982.K64.983")
        )
        spade = SaycResponseToOneClubOneSpadeRule().evaluate(
            ctx("J982.Q84.K64.983")
        )
        expected = {
            "bidding/natural-bids/responses/response-to-1-club#Responder's Priorities",
            "bidding/natural-bids/responses/response-to-1-club#Responses with Major Suits",
        }
        self.assertEqual({s.serialize() for s in heart.sources}, expected)
        self.assertEqual({s.serialize() for s in spade.sources}, expected)

    def test_diamond_sources_are_canonical(self) -> None:
        decision = SaycResponseToOneClubOneDiamondRule().evaluate(
            ctx("K73.82.AQ742.J83")
        )
        self.assertEqual(
            {s.serialize() for s in decision.sources},
            {
                "bidding/natural-bids/responses/response-to-1-club#Responses with Major Suits",
                "bidding/natural-bids/responses/response-to-1-club#Responding with Diamonds",
            },
        )


    def test_balanced_six_to_ten_without_four_card_major_bids_1nt(self) -> None:
        result = create_sayc_one_club_response_engine().evaluate(
            ctx("K73.Q82.J74.Q843")
        )
        self.assertEqual(result.recommended_call, Call.parse("1NT"))

    def test_one_notrump_rejects_four_card_major(self) -> None:
        decision = SaycResponseToOneClubOneNotrumpRule().evaluate(
            ctx("K873.Q82.J74.Q83")
        )
        self.assertFalse(decision.applicable)

    def test_one_notrump_rejects_unbalanced_hand(self) -> None:
        decision = SaycResponseToOneClubOneNotrumpRule().evaluate(
            ctx("K73.Q8.J7.Q98432")
        )
        self.assertFalse(decision.applicable)

    def test_one_notrump_rejects_above_ten_hcp(self) -> None:
        decision = SaycResponseToOneClubOneNotrumpRule().evaluate(
            ctx("A73.K82.Q74.Q843")
        )
        self.assertFalse(decision.applicable)

    def test_rule_candidates_are_legal_in_position(self) -> None:
        for hand in (
            "J842.976.854.Q92",
            "Q84.J982.K64.983",
            "J982.Q84.K64.983",
            "K73.82.AQ742.J83",
        ):
            position = ctx(hand)
            result = create_sayc_one_club_response_engine().evaluate(position)
            self.assertTrue(position.auction.is_legal(result.recommended_call))


if __name__ == "__main__":
    unittest.main()
