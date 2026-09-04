from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from bridge import (
    Auction,
    BiddingContext,
    Hand,
    KnowledgeSource,
    Seat,
    StopperAssessment,
    StopperStatus,
    Suit,
    SystemContext,
    Vulnerability,
    assess_stopper,
)


SOURCE = (
    KnowledgeSource("bidding/natural-bids/responses/response-to-1-diamond", "Notrump Responses"),
)


def context() -> BiddingContext:
    return BiddingContext.create(
        hand=Hand.parse("AQ84.KJ6.T75.932"),
        auction=Auction(Seat.NORTH, ("1D", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("SAYC"),
    )


class _UnknownPolicy:
    policy_id = "fixture.unknown"

    def assess(self, ctx: BiddingContext, suit: Suit) -> StopperAssessment:
        return StopperAssessment.unknown(
            policy_id=self.policy_id,
            evidence=ctx.evaluation.honor_evidence(suit),
            explanation="Fixture policy intentionally has no rule for this holding.",
        )


class _KnownPolicy:
    policy_id = "fixture.known"

    def __init__(self, stopped: bool) -> None:
        self._stopped = stopped

    def assess(self, ctx: BiddingContext, suit: Suit) -> StopperAssessment:
        evidence = ctx.evaluation.honor_evidence(suit)
        if self._stopped:
            return StopperAssessment.stopped(
                policy_id=self.policy_id,
                evidence=evidence,
                explanation="Fixture source-defined stopped holding.",
                sources=SOURCE,
            )
        return StopperAssessment.not_stopped(
            policy_id=self.policy_id,
            evidence=evidence,
            explanation="Fixture source-defined unstopped holding.",
            sources=SOURCE,
        )


class _WrongEvidencePolicy:
    policy_id = "fixture.wrong-evidence"

    def assess(self, ctx: BiddingContext, suit: Suit) -> StopperAssessment:
        wrong = ctx.evaluation.honor_evidence(Suit.SPADES)
        return StopperAssessment.unknown(
            policy_id=self.policy_id,
            evidence=wrong,
        )


class _WrongIdPolicy:
    policy_id = "fixture.correct-id"

    def assess(self, ctx: BiddingContext, suit: Suit) -> StopperAssessment:
        return StopperAssessment.unknown(
            policy_id="fixture.other-id",
            evidence=ctx.evaluation.honor_evidence(suit),
        )


class StopperPolicyContractTests(unittest.TestCase):
    def test_unknown_is_first_class_result(self) -> None:
        result = assess_stopper(_UnknownPolicy(), context(), Suit.DIAMONDS)
        self.assertEqual(result.status, StopperStatus.UNKNOWN)
        self.assertIsNone(result.is_stopped)
        self.assertFalse(result.is_known)

    def test_known_stopped_result_requires_traceable_source(self) -> None:
        result = assess_stopper(_KnownPolicy(True), context(), Suit.DIAMONDS)
        self.assertEqual(result.status, StopperStatus.STOPPED)
        self.assertTrue(result.is_stopped)
        self.assertTrue(result.is_known)
        self.assertEqual(result.sources, SOURCE)

    def test_known_not_stopped_result_is_distinct(self) -> None:
        result = assess_stopper(_KnownPolicy(False), context(), Suit.DIAMONDS)
        self.assertEqual(result.status, StopperStatus.NOT_STOPPED)
        self.assertFalse(result.is_stopped)

    def test_known_assessment_without_explanation_is_rejected(self) -> None:
        evidence = context().evaluation.honor_evidence(Suit.DIAMONDS)
        with self.assertRaises(ValueError):
            StopperAssessment(
                policy_id="x",
                suit=Suit.DIAMONDS,
                status=StopperStatus.STOPPED,
                evidence=evidence,
                sources=SOURCE,
            )

    def test_known_assessment_without_source_is_rejected(self) -> None:
        evidence = context().evaluation.honor_evidence(Suit.DIAMONDS)
        with self.assertRaises(ValueError):
            StopperAssessment(
                policy_id="x",
                suit=Suit.DIAMONDS,
                status=StopperStatus.NOT_STOPPED,
                evidence=evidence,
                explanation="Known conclusion.",
            )

    def test_assessment_is_immutable(self) -> None:
        result = assess_stopper(_UnknownPolicy(), context(), Suit.DIAMONDS)
        with self.assertRaises(FrozenInstanceError):
            result.status = StopperStatus.STOPPED  # type: ignore[misc]

    def test_assessment_suit_must_match_evidence(self) -> None:
        evidence = context().evaluation.honor_evidence(Suit.DIAMONDS)
        with self.assertRaises(ValueError):
            StopperAssessment(
                policy_id="x",
                suit=Suit.CLUBS,
                status=StopperStatus.UNKNOWN,
                evidence=evidence,
            )

    def test_runner_rejects_evidence_not_from_context(self) -> None:
        with self.assertRaisesRegex(ValueError, "wrong suit|does not match"):
            assess_stopper(_WrongEvidencePolicy(), context(), Suit.DIAMONDS)

    def test_runner_rejects_policy_id_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "policy_id"):
            assess_stopper(_WrongIdPolicy(), context(), Suit.DIAMONDS)

    def test_runner_requires_context(self) -> None:
        with self.assertRaises(TypeError):
            assess_stopper(_UnknownPolicy(), None, Suit.DIAMONDS)  # type: ignore[arg-type]

    def test_runner_requires_suit(self) -> None:
        with self.assertRaises(TypeError):
            assess_stopper(_UnknownPolicy(), context(), "D")  # type: ignore[arg-type]

    def test_no_concrete_production_stopper_formula_is_shipped(self) -> None:
        import bridge.stopper_policy as module

        exported_policy_classes = [
            name for name in dir(module)
            if name.endswith("Policy") and name != "StopperPolicy"
        ]
        self.assertEqual(exported_policy_classes, [])


if __name__ == "__main__":
    unittest.main()
