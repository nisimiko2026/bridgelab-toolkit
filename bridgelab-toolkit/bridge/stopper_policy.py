"""BridgeLab stopper-policy contract.

The system-neutral hand evaluator records only objective suit length and honor
evidence.  This module defines the boundary where a bidding system or explicit
partnership agreement may interpret that evidence as stopped, unstopped, or
unknown.

No concrete stopper formula is supplied here.  A production policy must be
source- or agreement-grounded and must expose its provenance through
``KnowledgeSource`` values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from .bidding_rules import BiddingContext, KnowledgeSource
from .evaluation import SuitHonorEvidence
from .models import Suit


class StopperStatus(Enum):
    """Outcome of applying one explicit stopper policy."""

    STOPPED = "stopped"
    NOT_STOPPED = "not-stopped"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class StopperAssessment:
    """Immutable result of interpreting one suit under one stopper policy.

    Known conclusions (``STOPPED`` or ``NOT_STOPPED``) require an explanation
    and at least one provenance source.  ``UNKNOWN`` is a first-class result and
    may be returned when the configured policy cannot classify the holding.
    """

    policy_id: str
    suit: Suit
    status: StopperStatus
    evidence: SuitHonorEvidence
    explanation: str = ""
    sources: tuple[KnowledgeSource, ...] = ()

    def __post_init__(self) -> None:
        policy_id = self.policy_id.strip()
        if not policy_id:
            raise ValueError("policy_id must not be blank")
        object.__setattr__(self, "policy_id", policy_id)

        if not isinstance(self.suit, Suit):
            raise TypeError("suit must be Suit")
        if not isinstance(self.status, StopperStatus):
            raise TypeError("status must be StopperStatus")
        if not isinstance(self.evidence, SuitHonorEvidence):
            raise TypeError("evidence must be SuitHonorEvidence")
        if self.evidence.suit is not self.suit:
            raise ValueError("assessment suit must match evidence suit")

        explanation = self.explanation.strip()
        object.__setattr__(self, "explanation", explanation)

        if not all(isinstance(source, KnowledgeSource) for source in self.sources):
            raise TypeError("sources must contain KnowledgeSource values")

        if self.status is not StopperStatus.UNKNOWN:
            if not explanation:
                raise ValueError("known stopper assessment requires an explanation")
            if not self.sources:
                raise ValueError("known stopper assessment requires at least one source")

    @classmethod
    def unknown(
        cls,
        *,
        policy_id: str,
        evidence: SuitHonorEvidence,
        explanation: str = "",
    ) -> "StopperAssessment":
        return cls(
            policy_id=policy_id,
            suit=evidence.suit,
            status=StopperStatus.UNKNOWN,
            evidence=evidence,
            explanation=explanation,
        )

    @classmethod
    def stopped(
        cls,
        *,
        policy_id: str,
        evidence: SuitHonorEvidence,
        explanation: str,
        sources: tuple[KnowledgeSource, ...],
    ) -> "StopperAssessment":
        return cls(
            policy_id=policy_id,
            suit=evidence.suit,
            status=StopperStatus.STOPPED,
            evidence=evidence,
            explanation=explanation,
            sources=sources,
        )

    @classmethod
    def not_stopped(
        cls,
        *,
        policy_id: str,
        evidence: SuitHonorEvidence,
        explanation: str,
        sources: tuple[KnowledgeSource, ...],
    ) -> "StopperAssessment":
        return cls(
            policy_id=policy_id,
            suit=evidence.suit,
            status=StopperStatus.NOT_STOPPED,
            evidence=evidence,
            explanation=explanation,
            sources=sources,
        )

    @property
    def is_known(self) -> bool:
        return self.status is not StopperStatus.UNKNOWN

    @property
    def is_stopped(self) -> bool | None:
        if self.status is StopperStatus.UNKNOWN:
            return None
        return self.status is StopperStatus.STOPPED


@runtime_checkable
class StopperPolicy(Protocol):
    """Structural contract for system- or partnership-defined stopper logic."""

    @property
    def policy_id(self) -> str: ...

    def assess(self, context: BiddingContext, suit: Suit) -> StopperAssessment: ...


def assess_stopper(
    policy: StopperPolicy,
    context: BiddingContext,
    suit: Suit,
) -> StopperAssessment:
    """Apply one stopper policy and enforce the common policy contract.

    The returned assessment must use the exact objective evidence already
    present in ``context.evaluation``.  This prevents a policy implementation
    from silently substituting or fabricating hand facts.
    """
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    if not isinstance(suit, Suit):
        raise TypeError("suit must be Suit")

    try:
        policy_id = policy.policy_id
    except AttributeError as exc:
        raise TypeError("stopper policy must expose policy_id") from exc
    if not isinstance(policy_id, str):
        raise TypeError("stopper policy policy_id must be a string")
    normalized_id = policy_id.strip()
    if not normalized_id:
        raise ValueError("stopper policy policy_id must not be blank")

    assessment = policy.assess(context, suit)
    if not isinstance(assessment, StopperAssessment):
        raise TypeError("stopper policy must return StopperAssessment")
    if assessment.policy_id != normalized_id:
        raise ValueError(
            f"assessment policy_id {assessment.policy_id!r} does not match "
            f"policy {normalized_id!r}"
        )
    if assessment.suit is not suit:
        raise ValueError("stopper policy returned an assessment for the wrong suit")

    expected = context.evaluation.honor_evidence(suit)
    if assessment.evidence != expected:
        raise ValueError(
            "stopper policy assessment evidence does not match "
            "BiddingContext hand evidence"
        )

    return assessment
