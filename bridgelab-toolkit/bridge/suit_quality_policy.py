"""Policy interface for interpreting objective suit-quality evidence.

Phase 5R deliberately records only objective suit facts.  This module supplies
the next architectural layer: an explicit policy may interpret those facts for
a system/convention while preserving source traceability.

No production definition of a "good suit" is provided here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from .bidding_rules import BiddingContext, KnowledgeSource
from .evaluation import SuitQualityEvidence
from .models import Suit


class SuitQualityStatus(Enum):
    QUALIFIES = "qualifies"
    DOES_NOT_QUALIFY = "does-not-qualify"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SuitQualityAssessment:
    policy_id: str
    suit: Suit
    status: SuitQualityStatus
    evidence: SuitQualityEvidence
    explanation: str = ""
    sources: tuple[KnowledgeSource, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str):
            raise TypeError("policy_id must be str")
        normalized = self.policy_id.strip()
        if not normalized:
            raise ValueError("policy_id must not be blank")
        object.__setattr__(self, "policy_id", normalized)

        if not isinstance(self.suit, Suit):
            raise TypeError("suit must be Suit")
        if not isinstance(self.status, SuitQualityStatus):
            raise TypeError("status must be SuitQualityStatus")
        if not isinstance(self.evidence, SuitQualityEvidence):
            raise TypeError("evidence must be SuitQualityEvidence")
        if self.evidence.suit is not self.suit:
            raise ValueError("evidence suit must match assessment suit")
        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be str")
        if any(not isinstance(source, KnowledgeSource) for source in self.sources):
            raise TypeError("sources must contain KnowledgeSource values")

        if self.status is not SuitQualityStatus.UNKNOWN:
            if not self.explanation.strip():
                raise ValueError("known quality outcomes require an explanation")
            if not self.sources:
                raise ValueError("known quality outcomes require a source")

    @classmethod
    def unknown(
        cls,
        policy_id: str,
        suit: Suit,
        evidence: SuitQualityEvidence,
        explanation: str = "",
        sources: tuple[KnowledgeSource, ...] = (),
    ) -> "SuitQualityAssessment":
        return cls(policy_id, suit, SuitQualityStatus.UNKNOWN, evidence, explanation, sources)

    @classmethod
    def qualifies(
        cls,
        policy_id: str,
        suit: Suit,
        evidence: SuitQualityEvidence,
        explanation: str,
        sources: tuple[KnowledgeSource, ...],
    ) -> "SuitQualityAssessment":
        return cls(policy_id, suit, SuitQualityStatus.QUALIFIES, evidence, explanation, sources)

    @classmethod
    def does_not_qualify(
        cls,
        policy_id: str,
        suit: Suit,
        evidence: SuitQualityEvidence,
        explanation: str,
        sources: tuple[KnowledgeSource, ...],
    ) -> "SuitQualityAssessment":
        return cls(policy_id, suit, SuitQualityStatus.DOES_NOT_QUALIFY, evidence, explanation, sources)

    @property
    def is_known(self) -> bool:
        return self.status is not SuitQualityStatus.UNKNOWN

    @property
    def qualifies_suit(self) -> bool | None:
        if self.status is SuitQualityStatus.UNKNOWN:
            return None
        return self.status is SuitQualityStatus.QUALIFIES


@runtime_checkable
class SuitQualityPolicy(Protocol):
    @property
    def policy_id(self) -> str: ...

    def assess(
        self,
        context: BiddingContext,
        suit: Suit,
    ) -> SuitQualityAssessment: ...


def assess_suit_quality(
    policy: SuitQualityPolicy,
    context: BiddingContext,
    suit: Suit,
) -> SuitQualityAssessment:
    """Run a policy and enforce identity/evidence integrity."""
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    if not isinstance(suit, Suit):
        raise TypeError("suit must be Suit")

    policy_id = getattr(policy, "policy_id", None)
    if not isinstance(policy_id, str):
        raise TypeError("policy must expose string policy_id")
    normalized = policy_id.strip()
    if not normalized:
        raise ValueError("policy_id must not be blank")

    assessment = policy.assess(context, suit)
    if not isinstance(assessment, SuitQualityAssessment):
        raise TypeError("policy must return SuitQualityAssessment")
    if assessment.policy_id.casefold() != normalized.casefold():
        raise ValueError("assessment policy_id must match policy")
    if assessment.suit is not suit:
        raise ValueError("assessment suit must match requested suit")

    expected = context.evaluation.quality_evidence(suit)
    if assessment.evidence != expected:
        raise ValueError("assessment evidence must match context hand evidence")

    return assessment
