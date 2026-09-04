from __future__ import annotations

import unittest

from bridge.auction import Auction, Call
from bridge.bidding_rules import (
    BiddingContext,
    BiddingRule,
    KnowledgeSource,
    RuleDecision,
    SystemContext,
    evaluate_rule,
)
from bridge.models import Hand, Seat, Vulnerability


class _AlwaysOneClub:
    rule_id = "test.open-one-club"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1C"),
            explanation="Fixture rule for contract testing only.",
            sources=(KnowledgeSource("bidding/principles/opening-bids", "Fixture"),),
            priority=10,
        )


class _NeverRule:
    rule_id = "test.never"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        return RuleDecision.not_applicable(self.rule_id, "fixture miss")


class _IllegalRule:
    rule_id = "test.illegal"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1C"),
            explanation="Fixture illegal recommendation.",
            sources=(KnowledgeSource("bidding/test-source"),),
        )


class _WrongIdRule:
    rule_id = "test.expected"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        return RuleDecision.not_applicable("test.other")


class _WrongReturnRule:
    rule_id = "test.bad-return"

    def evaluate(self, context: BiddingContext):
        return None


class BiddingRuleInterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hand = Hand.parse("AK84.QJ6.A75.K92")
        self.system = SystemContext.from_mapping("SAYC", {"forcing_1nt": False})

    def test_knowledge_source_normalizes_article_id(self) -> None:
        source = KnowledgeSource(r"/bidding\systems\sayc.md/", " Overview ")
        self.assertEqual(source.article_id, "bidding/systems/sayc")
        self.assertEqual(source.heading, "Overview")
        self.assertEqual(source.serialize(), "bidding/systems/sayc#Overview")

    def test_knowledge_source_rejects_blank_article(self) -> None:
        with self.assertRaises(ValueError):
            KnowledgeSource("   ")

    def test_system_context_is_deterministic(self) -> None:
        context = SystemContext.from_mapping(" SAYC ", {"z": 1, "A": True})
        self.assertEqual(context.system, "SAYC")
        self.assertEqual(context.options, (("A", "True"), ("z", "1")))
        self.assertEqual(context.option("a"), "True")
        self.assertEqual(context.option("missing", "fallback"), "fallback")

    def test_system_context_rejects_duplicate_option_keys_case_insensitively(self) -> None:
        with self.assertRaises(ValueError):
            SystemContext("SAYC", (("Feature", "on"), ("feature", "off")))

    def test_context_create_evaluates_hand_and_uses_next_seat(self) -> None:
        auction = Auction(Seat.NORTH)
        context = BiddingContext.create(
            hand=self.hand,
            auction=auction,
            vulnerability=Vulnerability.NONE,
            system=self.system,
        )
        self.assertIs(context.seat, Seat.NORTH)
        self.assertEqual(context.evaluation.hcp, 17)

    def test_context_rejects_wrong_seat(self) -> None:
        auction = Auction(Seat.NORTH)
        with self.assertRaises(ValueError):
            BiddingContext.create(
                hand=self.hand,
                auction=auction,
                vulnerability=Vulnerability.NONE,
                system=self.system,
                seat=Seat.EAST,
            )

    def test_context_rejects_completed_auction(self) -> None:
        auction = Auction(Seat.NORTH, ["P", "P", "P", "P"])
        with self.assertRaises(ValueError):
            BiddingContext.create(
                hand=self.hand,
                auction=auction,
                vulnerability=Vulnerability.NONE,
                system=self.system,
            )

    def test_applicable_decision_requires_candidate(self) -> None:
        with self.assertRaises(ValueError):
            RuleDecision(rule_id="x", applicable=True, explanation="why", sources=(KnowledgeSource("a"),))

    def test_applicable_decision_requires_explanation(self) -> None:
        with self.assertRaises(ValueError):
            RuleDecision.recommend(
                rule_id="x",
                candidate=Call.parse("1C"),
                explanation=" ",
                sources=(KnowledgeSource("a"),),
            )

    def test_applicable_decision_requires_source(self) -> None:
        with self.assertRaises(ValueError):
            RuleDecision.recommend(
                rule_id="x",
                candidate=Call.parse("1C"),
                explanation="why",
                sources=(),
            )

    def test_not_applicable_decision_has_no_candidate_or_sources(self) -> None:
        decision = RuleDecision.not_applicable("x", "not this hand")
        self.assertFalse(decision.applicable)
        self.assertIsNone(decision.candidate)
        self.assertEqual(decision.sources, ())
        self.assertEqual(decision.explanation, "not this hand")

    def test_protocol_accepts_structural_rule(self) -> None:
        self.assertIsInstance(_AlwaysOneClub(), BiddingRule)

    def test_evaluate_rule_accepts_legal_source_grounded_recommendation(self) -> None:
        context = BiddingContext.create(
            hand=self.hand,
            auction=Auction(Seat.NORTH),
            vulnerability=Vulnerability.NS,
            system=self.system,
        )
        decision = evaluate_rule(_AlwaysOneClub(), context)
        self.assertTrue(decision.applicable)
        self.assertEqual(decision.candidate, Call.parse("1C"))
        self.assertEqual(decision.priority, 10)
        self.assertEqual(decision.sources[0].article_id, "bidding/principles/opening-bids")

    def test_evaluate_rule_accepts_non_applicable_result(self) -> None:
        context = BiddingContext.create(
            hand=self.hand,
            auction=Auction(Seat.NORTH),
            vulnerability=Vulnerability.BOTH,
            system=self.system,
        )
        decision = evaluate_rule(_NeverRule(), context)
        self.assertFalse(decision.applicable)

    def test_evaluate_rule_rejects_illegal_candidate(self) -> None:
        auction = Auction(Seat.NORTH, ["1S"])
        context = BiddingContext.create(
            hand=self.hand,
            auction=auction,
            vulnerability=Vulnerability.NONE,
            system=self.system,
        )
        with self.assertRaisesRegex(ValueError, "illegal call"):
            evaluate_rule(_IllegalRule(), context)

    def test_evaluate_rule_rejects_rule_id_mismatch(self) -> None:
        context = BiddingContext.create(
            hand=self.hand,
            auction=Auction(Seat.NORTH),
            vulnerability=Vulnerability.NONE,
            system=self.system,
        )
        with self.assertRaisesRegex(ValueError, "does not match"):
            evaluate_rule(_WrongIdRule(), context)

    def test_evaluate_rule_rejects_wrong_return_type(self) -> None:
        context = BiddingContext.create(
            hand=self.hand,
            auction=Auction(Seat.NORTH),
            vulnerability=Vulnerability.NONE,
            system=self.system,
        )
        with self.assertRaises(TypeError):
            evaluate_rule(_WrongReturnRule(), context)


if __name__ == "__main__":
    unittest.main()
