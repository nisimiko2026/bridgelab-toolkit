from __future__ import annotations

import unittest

from bridge import (
    Auction,
    BiddingContext,
    BiddingEngine,
    Call,
    Hand,
    KnowledgeSource,
    RuleDecision,
    Seat,
    SystemContext,
    Vulnerability,
)


SOURCE = (KnowledgeSource("bidding/systems/sayc", "Fixture"),)


class _Rule:
    def __init__(
        self,
        rule_id: str,
        candidate: str | None,
        *,
        priority: int = 0,
        reason: str = "fixture miss",
    ) -> None:
        self.rule_id = rule_id
        self._candidate = candidate
        self._priority = priority
        self._reason = reason

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if self._candidate is None:
            return RuleDecision.not_applicable(self.rule_id, self._reason)
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse(self._candidate),
            explanation=f"Fixture recommendation from {self.rule_id}.",
            sources=SOURCE,
            priority=self._priority,
        )


class _IllegalRule:
    rule_id = "illegal"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1C"),
            explanation="Fixture illegal call.",
            sources=SOURCE,
        )


class BiddingEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hand = Hand.parse("AK84.QJ6.A75.K92")
        self.system = SystemContext("SAYC")

    def context(self, calls=()) -> BiddingContext:
        return BiddingContext.create(
            hand=self.hand,
            auction=Auction(Seat.NORTH, calls),
            vulnerability=Vulnerability.NONE,
            system=self.system,
        )

    def test_empty_registry_returns_no_recommendation(self) -> None:
        result = BiddingEngine().evaluate(self.context())
        self.assertFalse(result.has_recommendation)
        self.assertIsNone(result.recommended)
        self.assertIsNone(result.recommended_call)
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.decisions, ())

    def test_single_applicable_rule_is_recommended(self) -> None:
        engine = BiddingEngine([_Rule("open.1c", "1C", priority=10)])
        result = engine.evaluate(self.context())
        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.recommended_call, Call.parse("1C"))
        self.assertEqual(result.recommended.rule_id, "open.1c")
        self.assertEqual(result.alternatives, ())

    def test_higher_priority_wins(self) -> None:
        engine = BiddingEngine([
            _Rule("low", "1C", priority=1),
            _Rule("high", "1D", priority=9),
        ])
        result = engine.evaluate(self.context())
        self.assertEqual(result.recommended.rule_id, "high")
        self.assertEqual([d.rule_id for d in result.alternatives], ["low"])

    def test_registration_order_breaks_priority_ties(self) -> None:
        engine = BiddingEngine([
            _Rule("first", "1H", priority=5),
            _Rule("second", "1S", priority=5),
        ])
        result = engine.evaluate(self.context())
        self.assertEqual(result.recommended.rule_id, "first")
        self.assertEqual(result.alternatives[0].rule_id, "second")

    def test_duplicate_candidate_calls_are_collapsed_in_ranked_candidates(self) -> None:
        engine = BiddingEngine([
            _Rule("stronger", "1C", priority=10),
            _Rule("weaker-same-call", "1C", priority=3),
            _Rule("other", "1D", priority=2),
        ])
        result = engine.evaluate(self.context())
        self.assertEqual([d.rule_id for d in result.candidates], ["stronger", "other"])
        self.assertEqual(
            [d.rule_id for d in result.decisions],
            ["stronger", "weaker-same-call", "other"],
        )

    def test_non_applicable_rules_remain_in_trace(self) -> None:
        engine = BiddingEngine([
            _Rule("miss", None),
            _Rule("hit", "1C"),
        ])
        result = engine.evaluate(self.context())
        self.assertEqual(result.recommended.rule_id, "hit")
        self.assertEqual(len(result.decisions), 2)
        self.assertFalse(result.decisions[0].applicable)
        self.assertEqual(result.decisions[0].explanation, "fixture miss")

    def test_decision_trace_preserves_registration_order(self) -> None:
        engine = BiddingEngine([
            _Rule("a", "1C", priority=1),
            _Rule("b", "1D", priority=100),
            _Rule("c", None),
        ])
        result = engine.evaluate(self.context())
        self.assertEqual([d.rule_id for d in result.decisions], ["a", "b", "c"])
        self.assertEqual(result.recommended.rule_id, "b")

    def test_illegal_rule_candidate_is_rejected_by_common_contract(self) -> None:
        engine = BiddingEngine([_IllegalRule()])
        with self.assertRaisesRegex(ValueError, "illegal call"):
            engine.evaluate(self.context(["1S"]))

    def test_duplicate_rule_ids_are_rejected_case_insensitively(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            BiddingEngine([_Rule("Rule.One", "1C"), _Rule("rule.one", "1D")])

    def test_blank_rule_id_is_rejected_at_registration(self) -> None:
        with self.assertRaises(ValueError):
            BiddingEngine([_Rule("  ", "1C")])

    def test_non_string_rule_id_is_rejected_at_registration(self) -> None:
        rule = _Rule("x", "1C")
        rule.rule_id = 42
        with self.assertRaises(TypeError):
            BiddingEngine([rule])

    def test_context_type_is_enforced(self) -> None:
        engine = BiddingEngine()
        with self.assertRaises(TypeError):
            engine.evaluate(None)  # type: ignore[arg-type]

    def test_rule_sources_survive_engine_ranking(self) -> None:
        engine = BiddingEngine([_Rule("source-test", "1C")])
        result = engine.evaluate(self.context())
        self.assertEqual(
            result.recommended.sources[0].serialize(),
            "bidding/systems/sayc#Fixture",
        )

    def test_engine_registry_is_immutable_tuple_view(self) -> None:
        rules = [_Rule("a", "1C")]
        engine = BiddingEngine(rules)
        rules.append(_Rule("b", "1D"))
        self.assertEqual(len(engine.rules), 1)
        self.assertIsInstance(engine.rules, tuple)


if __name__ == "__main__":
    unittest.main()
