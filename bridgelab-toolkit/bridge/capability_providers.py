"""Provider-neutral capability contracts for BridgeLab external/internal advisers.

The contracts in this module describe *capabilities*, not preferred engines.
They do not route, vote, or override BridgeLab system/convention/partnership
policy.  Provider output is evidence that callers may compare explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, Protocol, TypeVar, runtime_checkable

from .auction import Call
from .bidding_rules import BiddingContext
from .deals import Deal
from .declarer_play_state import DeclarerPlayState
from .models import Card
from .opening_lead_state import OpeningLeadState
from .trick_solver import TrickSolverResult


class Capability(str, Enum):
    BIDDING = "bidding"
    OPENING_LEAD = "opening-lead"
    PLAY = "play"
    DOUBLE_DUMMY = "double-dummy"
    DEAL_EVALUATION = "deal-evaluation"


class ProviderStatus(str, Enum):
    SUCCESS = "success"
    ABSTAIN = "abstain"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    provider_id: str
    capability: Capability
    implementation: str
    version: str | None = None

    def __post_init__(self) -> None:
        for name in ("provider_id", "implementation"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be blank")
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.capability, Capability):
            raise TypeError("capability must be Capability")
        if self.version is not None:
            if not isinstance(self.version, str) or not self.version.strip():
                raise ValueError("version must be None or a non-blank string")
            object.__setattr__(self, "version", self.version.strip())


@dataclass(frozen=True, slots=True)
class ProviderEvidence:
    """Opaque provenance attached to one provider observation."""

    source_ids: tuple[str, ...] = ()
    model_id: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_ids", _clean_tuple(self.source_ids, "source_ids"))
        object.__setattr__(self, "notes", _clean_tuple(self.notes, "notes"))
        if self.model_id is not None:
            if not isinstance(self.model_id, str) or not self.model_id.strip():
                raise ValueError("model_id must be None or a non-blank string")
            object.__setattr__(self, "model_id", self.model_id.strip())


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CapabilityResult(Generic[T]):
    provider: ProviderDescriptor
    status: ProviderStatus
    recommendation: T | None = None
    alternatives: tuple[T, ...] = ()
    evidence: ProviderEvidence = field(default_factory=ProviderEvidence)
    explanation: str = ""
    elapsed_seconds: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider, ProviderDescriptor):
            raise TypeError("provider must be ProviderDescriptor")
        if not isinstance(self.status, ProviderStatus):
            raise TypeError("status must be ProviderStatus")
        object.__setattr__(self, "alternatives", tuple(self.alternatives))
        if self.status is ProviderStatus.SUCCESS and self.recommendation is None:
            raise ValueError("successful capability result needs a recommendation")
        if self.status is not ProviderStatus.SUCCESS:
            if self.recommendation is not None or self.alternatives:
                raise ValueError("non-success result cannot contain recommendations")
        if self.elapsed_seconds is not None and self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds cannot be negative")
        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be a string")


@runtime_checkable
class BiddingAdviser(Protocol):
    descriptor: ProviderDescriptor

    def advise(self, context: BiddingContext) -> CapabilityResult[Call]: ...


@runtime_checkable
class OpeningLeadAdviser(Protocol):
    descriptor: ProviderDescriptor

    def advise(self, state: OpeningLeadState) -> CapabilityResult[Card]: ...


@runtime_checkable
class PlayAdviser(Protocol):
    descriptor: ProviderDescriptor

    def advise(self, state: DeclarerPlayState) -> CapabilityResult[Card]: ...


@runtime_checkable
class DoubleDummyProvider(Protocol):
    descriptor: ProviderDescriptor

    def solve(self, deal: Deal, *args, **kwargs) -> TrickSolverResult: ...


@runtime_checkable
class DealEvaluator(Protocol):
    descriptor: ProviderDescriptor

    def evaluate(self, deal: Deal) -> CapabilityResult[float]: ...


def _clean_tuple(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    cleaned: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must contain only non-blank strings")
        cleaned.append(value.strip())
    return tuple(cleaned)
