"""Decision evidence and disagreement classification for BridgeLab.

This layer records observations; it does not vote, rank providers, or mutate
system/convention/partnership policy.  Classification is deliberately driven
by explicit context supplied by callers rather than inferred from provider
names or observed bids.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from .capability_providers import CapabilityResult, ProviderStatus


class EvidenceScope(str, Enum):
    CORE = "core"
    SYSTEM = "system"
    CONVENTION = "convention"
    TREATMENT = "treatment"
    PARTNERSHIP = "partnership"
    PROVIDER = "provider"
    EXPERT_CORPUS = "expert-corpus"
    SIMULATION = "simulation"
    DOUBLE_DUMMY = "double-dummy"


class DisagreementKind(str, Enum):
    AGREEMENT = "agreement"
    SYSTEM_DIFFERENCE = "system-difference"
    CONVENTION_DIFFERENCE = "convention-difference"
    TREATMENT_DIFFERENCE = "treatment-difference"
    PARTNERSHIP_AGREEMENT = "partnership-agreement"
    JUDGMENT_DIFFERENCE = "judgment-difference"
    BRIDGELAB_ABSTAIN = "bridgelab-abstain"
    EXTERNAL_MODEL_ABSTAIN = "external-model-abstain"
    UNKNOWN_EXTERNAL_SYSTEM = "unknown-external-system"
    POSSIBLE_POLICY_GAP = "possible-policy-gap"
    POSSIBLE_ENGINE_DEFECT = "possible-engine-defect"


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class DecisionEvidence(Generic[T]):
    """One immutable observation about a decision."""

    result: CapabilityResult[T]
    scope: EvidenceScope = EvidenceScope.PROVIDER
    system_id: str | None = None
    convention_id: str | None = None
    treatment_id: str | None = None
    partnership_id: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.result, CapabilityResult):
            raise TypeError("result must be CapabilityResult")
        if not isinstance(self.scope, EvidenceScope):
            raise TypeError("scope must be EvidenceScope")
        for name in ("system_id", "convention_id", "treatment_id", "partnership_id"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{name} must be None or a non-blank string")
                object.__setattr__(self, name, value.strip())
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    @property
    def recommendation(self) -> T | None:
        return self.result.recommendation


@dataclass(frozen=True, slots=True)
class DisagreementContext:
    """Known semantic relationship between two observations.

    Unknown values stay unknown.  In particular, external_system_known=False
    prevents an expert/model observation from being treated as evidence of a
    defect in the selected convention card.
    """

    external_system_known: bool = True
    same_system: bool | None = None
    same_convention: bool | None = None
    same_treatment: bool | None = None
    same_partnership_agreement: bool | None = None
    bridgelab_policy_expected: bool = False
    engine_defect_evidence: bool = False


@dataclass(frozen=True, slots=True)
class Disagreement:
    kind: DisagreementKind
    left_provider_id: str
    right_provider_id: str
    explanation: str


def classify_disagreement(
    left: DecisionEvidence[object],
    right: DecisionEvidence[object],
    *,
    context: DisagreementContext = DisagreementContext(),
) -> Disagreement:
    """Classify two observations without selecting a winner."""
    lp = left.result.provider.provider_id
    rp = right.result.provider.provider_id

    if left.result.status is ProviderStatus.ABSTAIN:
        return Disagreement(DisagreementKind.BRIDGELAB_ABSTAIN, lp, rp,
                            "Left observation abstained; no recommendation was fabricated.")
    if right.result.status is ProviderStatus.ABSTAIN:
        return Disagreement(DisagreementKind.EXTERNAL_MODEL_ABSTAIN, lp, rp,
                            "Right observation abstained; no recommendation was fabricated.")

    if (left.result.status is ProviderStatus.SUCCESS
            and right.result.status is ProviderStatus.SUCCESS
            and left.recommendation == right.recommendation):
        return Disagreement(DisagreementKind.AGREEMENT, lp, rp,
                            "Both observations recommend the same action.")

    if not context.external_system_known:
        return Disagreement(DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM, lp, rp,
                            "External system is unknown; the difference cannot be attributed to policy.")
    if context.same_system is False:
        return Disagreement(DisagreementKind.SYSTEM_DIFFERENCE, lp, rp,
                            "The observations are governed by different bidding systems.")
    if context.same_convention is False:
        return Disagreement(DisagreementKind.CONVENTION_DIFFERENCE, lp, rp,
                            "The observations use different convention selections.")
    if context.same_treatment is False:
        return Disagreement(DisagreementKind.TREATMENT_DIFFERENCE, lp, rp,
                            "The observations use different treatments of the convention.")
    if context.same_partnership_agreement is False:
        return Disagreement(DisagreementKind.PARTNERSHIP_AGREEMENT, lp, rp,
                            "The observations use different partnership agreements.")
    if context.engine_defect_evidence:
        return Disagreement(DisagreementKind.POSSIBLE_ENGINE_DEFECT, lp, rp,
                            "Independent evidence indicates a possible engine implementation defect.")
    if context.bridgelab_policy_expected:
        return Disagreement(DisagreementKind.POSSIBLE_POLICY_GAP, lp, rp,
                            "The same known policy was expected to apply; review policy coverage explicitly.")
    return Disagreement(DisagreementKind.JUDGMENT_DIFFERENCE, lp, rp,
                        "No explicit system/convention/treatment difference explains the recommendations.")
