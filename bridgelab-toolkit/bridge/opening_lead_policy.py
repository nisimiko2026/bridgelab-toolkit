"""Source-bounded partnership policy for future opening-lead engines.

This module represents agreements only.  It deliberately has no hand, state,
or card-selection input and cannot produce an opening-lead recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bidding_rules import KnowledgeSource


class OpeningLeadLengthMethod(str, Enum):
    """Partnership method for leading from length."""

    FOURTH_BEST = "fourth-best"
    THIRD_AND_FIFTH = "third-and-fifth"
    OTHER = "other"
    UNKNOWN = "unknown"


class OpeningLeadHonorStyle(str, Enum):
    """Partnership treatment of touching honor sequences."""

    STANDARD = "standard"
    RUSINOW = "rusinow"
    UNKNOWN = "unknown"


class OpeningLeadTopOfNothing(str, Enum):
    """Whether the partnership plays Top of Nothing."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class OpeningLeadPolicy:
    """One explicit, immutable opening-lead partnership agreement."""

    policy_id: str
    length_method: OpeningLeadLengthMethod = OpeningLeadLengthMethod.UNKNOWN
    honor_style: OpeningLeadHonorStyle = OpeningLeadHonorStyle.UNKNOWN
    top_of_nothing: OpeningLeadTopOfNothing = OpeningLeadTopOfNothing.UNKNOWN
    explanation: str = "Opening-lead partnership agreement is unresolved."
    sources: tuple[KnowledgeSource, ...] = ()

    def __post_init__(self) -> None:
        policy_id = self.policy_id.strip() if isinstance(self.policy_id, str) else ""
        if not policy_id:
            raise ValueError("opening-lead policy_id must not be blank")
        object.__setattr__(self, "policy_id", policy_id)
        if not isinstance(self.length_method, OpeningLeadLengthMethod):
            raise TypeError("length_method must be OpeningLeadLengthMethod")
        if not isinstance(self.honor_style, OpeningLeadHonorStyle):
            raise TypeError("honor_style must be OpeningLeadHonorStyle")
        if not isinstance(self.top_of_nothing, OpeningLeadTopOfNothing):
            raise TypeError("top_of_nothing must be OpeningLeadTopOfNothing")
        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be a string")
        explanation = self.explanation.strip()
        if not explanation:
            raise ValueError("opening-lead policy explanation must not be blank")
        object.__setattr__(self, "explanation", explanation)
        if not isinstance(self.sources, tuple) or not all(
            isinstance(source, KnowledgeSource) for source in self.sources
        ):
            raise TypeError("sources must be a tuple of KnowledgeSource values")


@dataclass(frozen=True, slots=True)
class OpeningLeadPolicyAssessment:
    """Deterministic assessment of an explicit or missing policy."""

    length_method: OpeningLeadLengthMethod
    honor_style: OpeningLeadHonorStyle
    top_of_nothing: OpeningLeadTopOfNothing
    explanation: str
    sources: tuple[KnowledgeSource, ...]
    policy_id: str | None

    @property
    def is_resolved(self) -> bool:
        return any(
            value is not unknown
            for value, unknown in (
                (self.length_method, OpeningLeadLengthMethod.UNKNOWN),
                (self.honor_style, OpeningLeadHonorStyle.UNKNOWN),
                (self.top_of_nothing, OpeningLeadTopOfNothing.UNKNOWN),
            )
        )


def assess_opening_lead_policy(
    policy: OpeningLeadPolicy | None,
) -> OpeningLeadPolicyAssessment:
    """Describe policy choices without examining a hand or selecting a card."""

    if policy is None:
        return OpeningLeadPolicyAssessment(
            OpeningLeadLengthMethod.UNKNOWN,
            OpeningLeadHonorStyle.UNKNOWN,
            OpeningLeadTopOfNothing.UNKNOWN,
            "No opening-lead partnership policy is configured.",
            (),
            None,
        )
    if not isinstance(policy, OpeningLeadPolicy):
        raise TypeError("policy must be OpeningLeadPolicy or None")
    return OpeningLeadPolicyAssessment(
        policy.length_method,
        policy.honor_style,
        policy.top_of_nothing,
        policy.explanation,
        policy.sources,
        policy.policy_id,
    )
