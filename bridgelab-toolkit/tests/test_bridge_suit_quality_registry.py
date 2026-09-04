import pytest

from bridge import (
    Auction, BiddingContext, Hand, KnowledgeSource, PolicyRegistry, Seat, Suit,
    SuitQualityAssessment, SuitQualityStatus, SystemContext, Vulnerability,
)
from bridge.policy_registry import (
    SUIT_QUALITY_POLICY_OPTION,
    assess_configured_suit_quality,
    configured_suit_quality_policy_id,
    resolve_suit_quality_policy,
)


SOURCE = KnowledgeSource("bidding/systems/2-over-1", "1. Two-over-One Responses are Game Forcing")


class QualityPolicy:
    def __init__(self, policy_id, status=SuitQualityStatus.QUALIFIES):
        self.policy_id = policy_id
        self.status = status

    def assess(self, context, suit):
        evidence = context.evaluation.quality_evidence(suit)
        if self.status is SuitQualityStatus.UNKNOWN:
            return SuitQualityAssessment.unknown(self.policy_id, suit, evidence)
        if self.status is SuitQualityStatus.QUALIFIES:
            return SuitQualityAssessment.qualifies(
                self.policy_id, suit, evidence, "fixture qualifies", (SOURCE,)
            )
        return SuitQualityAssessment.does_not_qualify(
            self.policy_id, suit, evidence, "fixture rejects", (SOURCE,)
        )


def system(policy_id=None):
    options = {}
    if policy_id is not None:
        options[SUIT_QUALITY_POLICY_OPTION] = policy_id
    return SystemContext.from_mapping("SAYC", options)


def context(policy_id=None):
    return BiddingContext.create(
        hand=Hand.parse("AKQ97.JT8.64.532"),
        auction=Auction(Seat.NORTH, ("1H", "P")),
        vulnerability=Vulnerability.NONE,
        system=system(policy_id),
    )


def test_quality_registry_ids_are_sorted():
    registry = PolicyRegistry.from_suit_quality_policies(
        [QualityPolicy("zeta"), QualityPolicy("Alpha")]
    )
    assert registry.suit_quality_policy_ids == ("Alpha", "zeta")


def test_quality_lookup_is_case_insensitive():
    policy = QualityPolicy("GoodSuit")
    registry = PolicyRegistry.from_suit_quality_policies([policy])
    assert registry.suit_quality_policy("goodsuit") is policy


def test_duplicate_quality_ids_rejected_case_insensitively():
    with pytest.raises(ValueError):
        PolicyRegistry.from_suit_quality_policies(
            [QualityPolicy("x"), QualityPolicy("X")]
        )


def test_blank_quality_id_rejected():
    with pytest.raises(ValueError):
        PolicyRegistry.from_suit_quality_policies([QualityPolicy(" ")])


def test_combined_registry_preserves_both_roles():
    class Stopper:
        policy_id = "stop"
        def assess(self, context, suit):
            raise AssertionError
    quality = QualityPolicy("quality")
    registry = PolicyRegistry.from_policies(
        stopper_policies=[Stopper()],
        suit_quality_policies=[quality],
    )
    assert registry.stopper_policy_ids == ("stop",)
    assert registry.suit_quality_policy_ids == ("quality",)


def test_configured_quality_policy_id():
    assert configured_suit_quality_policy_id(system("  Quality ")) == "Quality"


def test_missing_configuration_returns_none():
    assert configured_suit_quality_policy_id(system()) is None


def test_resolve_configured_quality_policy():
    policy = QualityPolicy("quality")
    registry = PolicyRegistry.from_suit_quality_policies([policy])
    assert resolve_suit_quality_policy(system("QUALITY"), registry) is policy


def test_unregistered_configured_policy_returns_none():
    registry = PolicyRegistry.from_suit_quality_policies([QualityPolicy("other")])
    assert resolve_suit_quality_policy(system("quality"), registry) is None


def test_assess_configured_quality():
    registry = PolicyRegistry.from_suit_quality_policies([QualityPolicy("quality")])
    result = assess_configured_suit_quality(context("quality"), registry, Suit.SPADES)
    assert result.status is SuitQualityStatus.QUALIFIES
    assert result.evidence == context("quality").evaluation.quality_evidence(Suit.SPADES)


def test_assess_without_configuration_returns_none():
    registry = PolicyRegistry.from_suit_quality_policies([QualityPolicy("quality")])
    assert assess_configured_suit_quality(context(), registry, Suit.SPADES) is None


def test_unknown_assessment_remains_assessment_not_none():
    registry = PolicyRegistry.from_suit_quality_policies(
        [QualityPolicy("quality", SuitQualityStatus.UNKNOWN)]
    )
    result = assess_configured_suit_quality(context("quality"), registry, Suit.SPADES)
    assert result is not None
    assert result.status is SuitQualityStatus.UNKNOWN


def test_registry_type_validation():
    with pytest.raises(TypeError):
        resolve_suit_quality_policy(system("quality"), None)


def test_context_type_validation():
    with pytest.raises(TypeError):
        assess_configured_suit_quality(None, PolicyRegistry(), Suit.SPADES)


def test_suit_type_validation():
    with pytest.raises(TypeError):
        assess_configured_suit_quality(context(), PolicyRegistry(), "S")
