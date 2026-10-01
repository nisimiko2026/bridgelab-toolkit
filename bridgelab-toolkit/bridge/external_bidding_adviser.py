"""Provider-neutral adapter boundary for external bidding advisers.

External advisers produce observations, not BridgeLab policy.  This module
normalizes an external transport response into the existing CapabilityResult
and DecisionEvidence contracts without routing, voting or overriding the
selected system/convention/partnership agreement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .auction import Call
from .bidding_rules import BiddingContext
from .capability_providers import (
    BiddingAdviser,
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderEvidence,
    ProviderStatus,
)
from .decision_evidence import DecisionEvidence, EvidenceScope


@dataclass(frozen=True, slots=True)
class ExternalBiddingObservation:
    """Transport-neutral observation returned by an external adviser."""

    status: ProviderStatus
    recommendation: str | None = None
    alternatives: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    model_id: str | None = None
    notes: tuple[str, ...] = ()
    explanation: str = ""
    elapsed_seconds: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ProviderStatus):
            raise TypeError("status must be ProviderStatus")

        object.__setattr__(self, "alternatives", tuple(self.alternatives))
        object.__setattr__(self, "source_ids", tuple(self.source_ids))
        object.__setattr__(self, "notes", tuple(self.notes))

        if self.status is ProviderStatus.SUCCESS:
            if not isinstance(self.recommendation, str) or not self.recommendation.strip():
                raise ValueError(
                    "successful external observation needs a recommendation"
                )
            object.__setattr__(
                self,
                "recommendation",
                self.recommendation.strip(),
            )
        elif self.recommendation is not None or self.alternatives:
            raise ValueError(
                "non-success external observation cannot contain recommendations"
            )

        for name in ("alternatives", "source_ids", "notes"):
            values = getattr(self, name)
            for value in values:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"{name} must contain only non-blank strings"
                    )

        object.__setattr__(
            self,
            "alternatives",
            tuple(value.strip() for value in self.alternatives),
        )
        object.__setattr__(
            self,
            "source_ids",
            tuple(value.strip() for value in self.source_ids),
        )
        object.__setattr__(
            self,
            "notes",
            tuple(value.strip() for value in self.notes),
        )

        if self.model_id is not None:
            if not isinstance(self.model_id, str) or not self.model_id.strip():
                raise ValueError(
                    "model_id must be None or a non-blank string"
                )
            object.__setattr__(self, "model_id", self.model_id.strip())

        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be a string")

        if self.elapsed_seconds is not None:
            if not isinstance(self.elapsed_seconds, (int, float)):
                raise TypeError(
                    "elapsed_seconds must be numeric or None"
                )
            if self.elapsed_seconds < 0:
                raise ValueError(
                    "elapsed_seconds cannot be negative"
                )


@runtime_checkable
class ExternalBiddingTransport(Protocol):
    """Transport/provider-specific call boundary.

    BEN REST, a local model, a subprocess or another adviser may implement
    this protocol without changing BridgeLab's capability contracts.
    """

    def observe(
        self,
        context: BiddingContext,
    ) -> ExternalBiddingObservation:
        ...


class ExternalBiddingAdviserAdapter:
    """Adapt one external bidding transport to BridgeLab's BiddingAdviser."""

    def __init__(
        self,
        *,
        descriptor: ProviderDescriptor,
        transport: ExternalBiddingTransport,
    ) -> None:
        if not isinstance(descriptor, ProviderDescriptor):
            raise TypeError("descriptor must be ProviderDescriptor")

        if descriptor.capability is not Capability.BIDDING:
            raise ValueError(
                "external bidding adviser requires BIDDING capability"
            )

        if not isinstance(transport, ExternalBiddingTransport):
            raise TypeError(
                "transport must implement ExternalBiddingTransport"
            )

        self.descriptor = descriptor
        self._transport = transport

    def advise(
        self,
        context: BiddingContext,
    ) -> CapabilityResult[Call]:
        if not isinstance(context, BiddingContext):
            raise TypeError("context must be BiddingContext")

        observation = self._transport.observe(context)

        if not isinstance(observation, ExternalBiddingObservation):
            raise TypeError(
                "external bidding transport must return "
                "ExternalBiddingObservation"
            )

        recommendation = None
        alternatives: tuple[Call, ...] = ()

        if observation.status is ProviderStatus.SUCCESS:
            recommendation = _parse_call(
                observation.recommendation,
                "recommendation",
            )
            alternatives = tuple(
                _parse_call(value, "alternative")
                for value in observation.alternatives
            )

        return CapabilityResult(
            provider=self.descriptor,
            status=observation.status,
            recommendation=recommendation,
            alternatives=alternatives,
            evidence=ProviderEvidence(
                source_ids=observation.source_ids,
                model_id=observation.model_id,
                notes=observation.notes,
            ),
            explanation=observation.explanation,
            elapsed_seconds=observation.elapsed_seconds,
        )

    def evidence(
        self,
        context: BiddingContext,
        *,
        system_id: str | None = None,
        convention_id: str | None = None,
        treatment_id: str | None = None,
        partnership_id: str | None = None,
        confidence: float | None = None,
    ) -> DecisionEvidence[Call]:
        """Return the provider observation as evidence, never as policy."""

        return DecisionEvidence(
            result=self.advise(context),
            scope=EvidenceScope.PROVIDER,
            system_id=system_id,
            convention_id=convention_id,
            treatment_id=treatment_id,
            partnership_id=partnership_id,
            confidence=confidence,
        )


def _parse_call(value: str | None, name: str) -> Call:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"external {name} must be a non-blank bridge call"
        )

    try:
        return Call.parse(value.strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"external {name} is not a valid bridge call: {value!r}"
        ) from exc


