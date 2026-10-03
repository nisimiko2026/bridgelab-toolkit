"""Failure-isolated multi-adviser bidding evidence.

A7.4 — Abstention / Failure Isolation.

Provider-reported ABSTAIN, UNAVAILABLE, and FAILED results remain ordinary
evidence. Unexpected provider exceptions are converted to FAILED evidence so
one adviser cannot prevent later explicitly requested advisers from running.
Configuration/contract errors are not swallowed.
"""
from __future__ import annotations

from dataclasses import dataclass

from .bidding_rules import BiddingContext
from .capability_providers import (
    Capability,
    CapabilityResult,
    ProviderEvidence,
    ProviderStatus,
)
from .capability_registry import CapabilityProviderRegistry
from .decision_evidence import DecisionEvidence, EvidenceScope
from .multi_bidding_adviser import (
    BiddingAdviserEvidence,
    BiddingAdviserRequest,
    MultiAdviserBiddingResult,
)


@dataclass(frozen=True, slots=True)
class AdviserFailure:
    provider_id: str
    exception_type: str
    message: str

    def __post_init__(self) -> None:
        for name in ("provider_id", "exception_type"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-blank string")
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.message, str):
            raise TypeError("message must be a string")


@dataclass(frozen=True, slots=True)
class IsolatedMultiAdviserBiddingResult:
    gathered: MultiAdviserBiddingResult
    failures: tuple[AdviserFailure, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.gathered, MultiAdviserBiddingResult):
            raise TypeError("gathered must be MultiAdviserBiddingResult")
        if not isinstance(self.failures, tuple):
            raise TypeError("failures must be a tuple")
        if not all(isinstance(x, AdviserFailure) for x in self.failures):
            raise TypeError("failures must contain AdviserFailure")

    @property
    def evidence(self) -> tuple[DecisionEvidence[object], ...]:
        return self.gathered.evidence


def gather_bidding_adviser_evidence_isolated(
    *,
    registry: CapabilityProviderRegistry,
    context: BiddingContext,
    requests: tuple[BiddingAdviserRequest, ...],
) -> IsolatedMultiAdviserBiddingResult:
    """Gather all requested advisers while isolating runtime provider failures."""
    if not isinstance(registry, CapabilityProviderRegistry):
        raise TypeError("registry must be CapabilityProviderRegistry")
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    if not isinstance(requests, tuple):
        raise TypeError("requests must be a tuple")
    if not all(isinstance(x, BiddingAdviserRequest) for x in requests):
        raise TypeError("requests must contain BiddingAdviserRequest")
    keys = tuple(x.provider_id.casefold() for x in requests)
    if len(set(keys)) != len(keys):
        raise ValueError("requested provider_id values must be unique")

    observations: list[BiddingAdviserEvidence] = []
    failures: list[AdviserFailure] = []

    for request in requests:
        # Registry/configuration errors are deliberate caller errors and remain
        # visible rather than being mislabeled as provider runtime failures.
        provider = registry.require(Capability.BIDDING, request.provider_id)
        evidence_method = getattr(provider, "evidence", None)
        if not callable(evidence_method):
            raise TypeError(
                f"bidding provider {request.provider_id!r} must expose evidence()"
            )

        try:
            evidence = evidence_method(
                context,
                system_id=request.system_id,
                convention_id=request.convention_id,
                treatment_id=request.treatment_id,
                partnership_id=request.partnership_id,
                confidence=request.confidence,
            )
        except Exception as exc:
            failure = AdviserFailure(
                provider_id=request.provider_id,
                exception_type=type(exc).__name__,
                message=str(exc),
            )
            failures.append(failure)
            evidence = _failed_evidence(
                provider=provider,
                request=request,
                failure=failure,
            )

        if not isinstance(evidence, DecisionEvidence):
            raise TypeError(
                f"bidding provider {request.provider_id!r} evidence() must return DecisionEvidence"
            )
        observations.append(BiddingAdviserEvidence(request.provider_id, evidence))

    return IsolatedMultiAdviserBiddingResult(
        gathered=MultiAdviserBiddingResult(tuple(observations)),
        failures=tuple(failures),
    )


def _failed_evidence(
    *,
    provider: object,
    request: BiddingAdviserRequest,
    failure: AdviserFailure,
) -> DecisionEvidence[object]:
    descriptor = getattr(provider, "descriptor", None)
    result = CapabilityResult(
        provider=descriptor,
        status=ProviderStatus.FAILED,
        evidence=ProviderEvidence(
            notes=(
                "Provider raised an exception during evidence collection.",
                f"{failure.exception_type}: {failure.message}",
            ),
        ),
        explanation="Provider runtime failure was isolated; no recommendation was fabricated.",
    )
    return DecisionEvidence(
        result=result,
        scope=EvidenceScope.PROVIDER,
        system_id=request.system_id,
        convention_id=request.convention_id,
        treatment_id=request.treatment_id,
        partnership_id=request.partnership_id,
        confidence=request.confidence,
    )
