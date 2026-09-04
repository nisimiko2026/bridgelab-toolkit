"""Theory-neutral policy boundary for Stayman opener dual-major preference.

The policy returns an abstract partnership choice only. It never selects or
constructs a bidding call, and BridgeLab supplies no default policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from .bidding_rules import BiddingContext, KnowledgeSource


class StaymanDualMajorResponse(Enum):
    HEARTS = "hearts"
    SPADES = "spades"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class StaymanDualMajorResponseAssessment:
    policy_id: str
    response: StaymanDualMajorResponse
    explanation: str = ""
    sources: tuple[KnowledgeSource, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str):
            raise TypeError("policy_id must be str")
        policy_id = self.policy_id.strip()
        if not policy_id:
            raise ValueError("policy_id must not be blank")
        object.__setattr__(self, "policy_id", policy_id)
        if not isinstance(self.response, StaymanDualMajorResponse):
            raise TypeError("response must be StaymanDualMajorResponse")
        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be str")
        if any(not isinstance(source, KnowledgeSource) for source in self.sources):
            raise TypeError("sources must contain KnowledgeSource values")
        if (
            self.response is not StaymanDualMajorResponse.UNKNOWN
            and (not self.explanation.strip() or not self.sources)
        ):
            raise ValueError("known responses require explanation and source")


@runtime_checkable
class StaymanDualMajorResponsePolicy(Protocol):
    @property
    def policy_id(self) -> str: ...

    def assess(self, context: BiddingContext) -> StaymanDualMajorResponseAssessment: ...


def assess_stayman_dual_major_response(
    policy: StaymanDualMajorResponsePolicy, context: BiddingContext
) -> StaymanDualMajorResponseAssessment:
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    policy_id = getattr(policy, "policy_id", None)
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise ValueError("policy must expose nonblank string policy_id")
    result = policy.assess(context)
    if not isinstance(result, StaymanDualMajorResponseAssessment):
        raise TypeError("policy must return StaymanDualMajorResponseAssessment")
    if result.policy_id.casefold() != policy_id.strip().casefold():
        raise ValueError("assessment policy_id must match policy")
    return result
