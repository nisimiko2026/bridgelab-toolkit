"""Theory-neutral policy boundary for responder strength after Stayman.

BridgeLab supplies the classification contract but no default classifier and
no numeric thresholds.  This module never selects a bidding call.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from .bidding_rules import BiddingContext, KnowledgeSource


class StaymanContinuationStrength(Enum):
    GAME_GOING = "game-going"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class StaymanContinuationStrengthAssessment:
    policy_id: str
    classification: StaymanContinuationStrength
    explanation: str = ""
    sources: tuple[KnowledgeSource, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str):
            raise TypeError("policy_id must be str")
        policy_id = self.policy_id.strip()
        if not policy_id:
            raise ValueError("policy_id must not be blank")
        object.__setattr__(self, "policy_id", policy_id)
        if not isinstance(self.classification, StaymanContinuationStrength):
            raise TypeError("classification must be StaymanContinuationStrength")
        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be str")
        if any(not isinstance(source, KnowledgeSource) for source in self.sources):
            raise TypeError("sources must contain KnowledgeSource values")
        if (
            self.classification is not StaymanContinuationStrength.UNKNOWN
            and (not self.explanation.strip() or not self.sources)
        ):
            raise ValueError("known classifications require explanation and source")


@runtime_checkable
class StaymanContinuationStrengthPolicy(Protocol):
    @property
    def policy_id(self) -> str: ...

    def assess(
        self, context: BiddingContext
    ) -> StaymanContinuationStrengthAssessment: ...


def assess_stayman_continuation_strength(
    policy: StaymanContinuationStrengthPolicy, context: BiddingContext
) -> StaymanContinuationStrengthAssessment:
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    policy_id = getattr(policy, "policy_id", None)
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise ValueError("policy must expose nonblank string policy_id")
    result = policy.assess(context)
    if not isinstance(result, StaymanContinuationStrengthAssessment):
        raise TypeError("policy must return StaymanContinuationStrengthAssessment")
    if result.policy_id.casefold() != policy_id.strip().casefold():
        raise ValueError("assessment policy_id must match policy")
    return result

