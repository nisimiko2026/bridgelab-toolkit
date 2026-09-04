from dataclasses import replace

import pytest

from bridge import (
    Auction,
    BiddingContext,
    Hand,
    KnowledgeSource,
    Seat,
    Suit,
    SuitQualityAssessment,
    SuitQualityStatus,
    SystemContext,
    Vulnerability,
    assess_suit_quality,
)


SOURCE = KnowledgeSource("bidding/systems/2-over-1", "1. Two-over-One Responses are Game Forcing")


def context():
    return BiddingContext.create(
        hand=Hand.parse("AKQ97.JT8.64.532"),
        auction=Auction(Seat.NORTH, ("1H", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", {}),
    )


class FixturePolicy:
    policy_id = "fixture.good-suit"

    def __init__(self, status=SuitQualityStatus.QUALIFIES):
        self.status = status

    def assess(self, ctx, suit):
        evidence = ctx.evaluation.quality_evidence(suit)
        if self.status is SuitQualityStatus.UNKNOWN:
            return SuitQualityAssessment.unknown(self.policy_id, suit, evidence)
        if self.status is SuitQualityStatus.QUALIFIES:
            return SuitQualityAssessment.qualifies(
                self.policy_id, suit, evidence, "Fixture qualifies.", (SOURCE,)
            )
        return SuitQualityAssessment.does_not_qualify(
            self.policy_id, suit, evidence, "Fixture rejects.", (SOURCE,)
        )


def test_qualifies_assessment():
    result = assess_suit_quality(FixturePolicy(), context(), Suit.SPADES)
    assert result.status is SuitQualityStatus.QUALIFIES
    assert result.qualifies_suit is True
    assert result.is_known


def test_does_not_qualify_assessment():
    result = assess_suit_quality(
        FixturePolicy(SuitQualityStatus.DOES_NOT_QUALIFY), context(), Suit.SPADES
    )
    assert result.qualifies_suit is False


def test_unknown_assessment():
    result = assess_suit_quality(
        FixturePolicy(SuitQualityStatus.UNKNOWN), context(), Suit.SPADES
    )
    assert result.qualifies_suit is None
    assert not result.is_known


def test_known_outcome_requires_explanation():
    evidence = context().evaluation.quality_evidence(Suit.SPADES)
    with pytest.raises(ValueError):
        SuitQualityAssessment.qualifies(
            "x", Suit.SPADES, evidence, "", (SOURCE,)
        )


def test_known_outcome_requires_source():
    evidence = context().evaluation.quality_evidence(Suit.SPADES)
    with pytest.raises(ValueError):
        SuitQualityAssessment.qualifies(
            "x", Suit.SPADES, evidence, "yes", ()
        )


def test_unknown_can_be_unsourced():
    evidence = context().evaluation.quality_evidence(Suit.SPADES)
    result = SuitQualityAssessment.unknown("x", Suit.SPADES, evidence)
    assert result.status is SuitQualityStatus.UNKNOWN


def test_evidence_suit_must_match():
    evidence = context().evaluation.quality_evidence(Suit.HEARTS)
    with pytest.raises(ValueError):
        SuitQualityAssessment.unknown("x", Suit.SPADES, evidence)


def test_runner_rejects_fabricated_evidence():
    class BadEvidencePolicy(FixturePolicy):
        def assess(self, ctx, suit):
            wrong = ctx.evaluation.quality_evidence(Suit.HEARTS)
            return SuitQualityAssessment.qualifies(
                self.policy_id, Suit.HEARTS, wrong, "bad", (SOURCE,)
            )
    with pytest.raises(ValueError):
        assess_suit_quality(BadEvidencePolicy(), context(), Suit.SPADES)


def test_runner_rejects_wrong_policy_id():
    class BadIdPolicy(FixturePolicy):
        def assess(self, ctx, suit):
            evidence = ctx.evaluation.quality_evidence(suit)
            return SuitQualityAssessment.qualifies(
                "different", suit, evidence, "bad", (SOURCE,)
            )
    with pytest.raises(ValueError):
        assess_suit_quality(BadIdPolicy(), context(), Suit.SPADES)


def test_runner_rejects_wrong_return_type():
    class BadReturnPolicy:
        policy_id = "bad"
        def assess(self, ctx, suit):
            return True
    with pytest.raises(TypeError):
        assess_suit_quality(BadReturnPolicy(), context(), Suit.SPADES)


def test_blank_policy_id_rejected():
    class BlankPolicy:
        policy_id = " "
        def assess(self, ctx, suit):
            raise AssertionError
    with pytest.raises(ValueError):
        assess_suit_quality(BlankPolicy(), context(), Suit.SPADES)


def test_context_type_validation():
    with pytest.raises(TypeError):
        assess_suit_quality(FixturePolicy(), None, Suit.SPADES)


def test_suit_type_validation():
    with pytest.raises(TypeError):
        assess_suit_quality(FixturePolicy(), context(), "S")


def test_no_production_quality_formula_shipped():
    import bridge.suit_quality_policy as module
    production_classes = [
        name for name in vars(module)
        if name.endswith("Policy") and name != "SuitQualityPolicy"
    ]
    assert production_classes == []
