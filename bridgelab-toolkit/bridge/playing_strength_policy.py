"""Policy interface for source-grounded playing-strength judgments.

Some bidding sources use qualitative requirements such as ``suitable playing
strength`` without defining an executable formula.  BridgeLab therefore keeps
that judgment behind an explicit application/partnership policy.

This module intentionally ships no production playing-strength formula and no
default policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from .bidding_rules import BiddingContext, KnowledgeSource


class PlayingStrengthStatus(Enum):
    QUALIFIES = "qualifies"
    DOES_NOT_QUALIFY = "does-not-qualify"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PlayingStrengthAssessment:
    policy_id: str
    status: PlayingStrengthStatus
    explanation: str = ""
    sources: tuple[KnowledgeSource, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str):
            raise TypeError("policy_id must be str")
        normalized = self.policy_id.strip()
        if not normalized:
            raise ValueError("policy_id must not be blank")
        object.__setattr__(self, "policy_id", normalized)

        if not isinstance(self.status, PlayingStrengthStatus):
            raise TypeError("status must be PlayingStrengthStatus")
        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be str")
        if any(not isinstance(source, KnowledgeSource) for source in self.sources):
            raise TypeError("sources must contain KnowledgeSource values")

        if self.status is not PlayingStrengthStatus.UNKNOWN:
            if not self.explanation.strip():
                raise ValueError("known playing-strength outcomes require an explanation")
            if not self.sources:
                raise ValueError("known playing-strength outcomes require a source")

    @classmethod
    def unknown(
        cls,
        policy_id: str,
        explanation: str = "",
        sources: tuple[KnowledgeSource, ...] = (),
    ) -> "PlayingStrengthAssessment":
        return cls(policy_id, PlayingStrengthStatus.UNKNOWN, explanation, sources)

    @classmethod
    def qualifies(
        cls,
        policy_id: str,
        explanation: str,
        sources: tuple[KnowledgeSource, ...],
    ) -> "PlayingStrengthAssessment":
        return cls(policy_id, PlayingStrengthStatus.QUALIFIES, explanation, sources)

    @classmethod
    def does_not_qualify(
        cls,
        policy_id: str,
        explanation: str,
        sources: tuple[KnowledgeSource, ...],
    ) -> "PlayingStrengthAssessment":
        return cls(policy_id, PlayingStrengthStatus.DOES_NOT_QUALIFY, explanation, sources)

    @property
    def is_known(self) -> bool:
        return self.status is not PlayingStrengthStatus.UNKNOWN

    @property
    def qualifies_strength(self) -> bool | None:
        if self.status is PlayingStrengthStatus.UNKNOWN:
            return None
        return self.status is PlayingStrengthStatus.QUALIFIES


@runtime_checkable
class PlayingStrengthPolicy(Protocol):
    @property
    def policy_id(self) -> str: ...

    def assess(self, context: BiddingContext) -> PlayingStrengthAssessment: ...


def assess_playing_strength(
    policy: PlayingStrengthPolicy,
    context: BiddingContext,
) -> PlayingStrengthAssessment:
    """Run a playing-strength policy and enforce policy/result integrity."""
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")

    policy_id = getattr(policy, "policy_id", None)
    if not isinstance(policy_id, str):
        raise TypeError("policy must expose string policy_id")
    normalized = policy_id.strip()
    if not normalized:
        raise ValueError("policy_id must not be blank")

    assessment = policy.assess(context)
    if not isinstance(assessment, PlayingStrengthAssessment):
        raise TypeError("policy must return PlayingStrengthAssessment")
    if assessment.policy_id.casefold() != normalized.casefold():
        raise ValueError("assessment policy_id must match policy")

    return assessment
