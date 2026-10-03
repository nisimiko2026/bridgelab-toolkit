"""Multi-adviser bidding contract for BridgeLab.

A7.1 — Multi-Adviser Contract.

This layer gathers evidence from explicitly requested registered bidding
advisers. It does not rank, vote, select, fall back, or promote external
recommendations into BridgeLab policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from .bidding_rules import BiddingContext
from .capability_providers import Capability
from .capability_registry import CapabilityProviderRegistry
from .decision_evidence import DecisionEvidence


@dataclass(frozen=True, slots=True)
class BiddingAdviserRequest:
    provider_id: str
    system_id: str | None = None
    convention_id: str | None = None
    treatment_id: str | None = None
    partnership_id: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        object.__setattr__(self, "provider_id", self.provider_id.strip())
        for name in ("system_id", "convention_id", "treatment_id", "partnership_id"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{name} must be None or a non-blank string")
                object.__setattr__(self, name, value.strip())
        if self.confidence is not None:
            if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
                raise TypeError("confidence must be numeric or None")
            if not 0.0 <= float(self.confidence) <= 1.0:
                raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class BiddingAdviserEvidence:
    provider_id: str
    evidence: DecisionEvidence[object]

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        object.__setattr__(self, "provider_id", self.provider_id.strip())
        if not isinstance(self.evidence, DecisionEvidence):
            raise TypeError("evidence must be DecisionEvidence")


@dataclass(frozen=True, slots=True)
class MultiAdviserBiddingResult:
    observations: tuple[BiddingAdviserEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.observations, tuple):
            raise TypeError("observations must be a tuple")
        if not all(isinstance(x, BiddingAdviserEvidence) for x in self.observations):
            raise TypeError("observations must contain BiddingAdviserEvidence")
        ids = tuple(x.provider_id.casefold() for x in self.observations)
        if len(set(ids)) != len(ids):
            raise ValueError("provider_id values must be unique")

    @property
    def total(self) -> int:
        return len(self.observations)

    @property
    def evidence(self) -> tuple[DecisionEvidence[object], ...]:
        return tuple(x.evidence for x in self.observations)

    def observation(self, provider_id: str) -> BiddingAdviserEvidence:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        key = provider_id.strip().casefold()
        for item in self.observations:
            if item.provider_id.casefold() == key:
                return item
        raise KeyError(provider_id.strip())


def gather_bidding_adviser_evidence(
    *,
    registry: CapabilityProviderRegistry,
    context: BiddingContext,
    requests: Iterable[BiddingAdviserRequest],
) -> MultiAdviserBiddingResult:
    """Gather independent evidence in caller-specified request order."""
    if not isinstance(registry, CapabilityProviderRegistry):
        raise TypeError("registry must be CapabilityProviderRegistry")
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    try:
        items = tuple(requests)
    except TypeError as exc:
        raise TypeError("requests must be an iterable") from exc
    if not all(isinstance(x, BiddingAdviserRequest) for x in items):
        raise TypeError("requests must contain BiddingAdviserRequest")
    keys = tuple(x.provider_id.casefold() for x in items)
    if len(set(keys)) != len(keys):
        raise ValueError("requested provider_id values must be unique")

    observations = []
    for request in items:
        provider = registry.require(Capability.BIDDING, request.provider_id)
        evidence_method = getattr(provider, "evidence", None)
        if not callable(evidence_method):
            raise TypeError(
                f"bidding provider {request.provider_id!r} must expose evidence()"
            )
        evidence = evidence_method(
            context,
            system_id=request.system_id,
            convention_id=request.convention_id,
            treatment_id=request.treatment_id,
            partnership_id=request.partnership_id,
            confidence=request.confidence,
        )
        if not isinstance(evidence, DecisionEvidence):
            raise TypeError(
                f"bidding provider {request.provider_id!r} evidence() must return DecisionEvidence"
            )
        observations.append(BiddingAdviserEvidence(request.provider_id, evidence))
    return MultiAdviserBiddingResult(tuple(observations))
