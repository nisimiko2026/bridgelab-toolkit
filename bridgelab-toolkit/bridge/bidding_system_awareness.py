"""System-awareness helpers for external bidding advisers.

A7.5 — System Awareness.

Derive disagreement context only from explicit evidence metadata. Unknown
system information stays unknown; provider names and recommended calls are
never used to infer a bidding system.
"""
from __future__ import annotations

from dataclasses import dataclass

from .decision_evidence import DecisionEvidence, DisagreementContext


@dataclass(frozen=True, slots=True)
class BiddingSystemRelationship:
    bridgelab_system_id: str | None
    external_system_id: str | None
    external_system_known: bool
    same_system: bool | None

    def __post_init__(self) -> None:
        for name in ("bridgelab_system_id", "external_system_id"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{name} must be None or a non-blank string")
                object.__setattr__(self, name, value.strip())
        if not isinstance(self.external_system_known, bool):
            raise TypeError("external_system_known must be bool")
        if self.same_system is not None and not isinstance(self.same_system, bool):
            raise TypeError("same_system must be bool or None")
        if not self.external_system_known and self.same_system is not None:
            raise ValueError("unknown external system cannot have same_system")


def bidding_system_relationship(
    bridgelab: DecisionEvidence[object],
    external: DecisionEvidence[object],
) -> BiddingSystemRelationship:
    """Describe the explicit system relationship between two observations."""
    if not isinstance(bridgelab, DecisionEvidence):
        raise TypeError("bridgelab must be DecisionEvidence")
    if not isinstance(external, DecisionEvidence):
        raise TypeError("external must be DecisionEvidence")

    left = bridgelab.system_id
    right = external.system_id

    if right is None:
        return BiddingSystemRelationship(
            bridgelab_system_id=left,
            external_system_id=None,
            external_system_known=False,
            same_system=None,
        )

    same = None if left is None else left.casefold() == right.casefold()
    return BiddingSystemRelationship(
        bridgelab_system_id=left,
        external_system_id=right,
        external_system_known=True,
        same_system=same,
    )


def system_aware_disagreement_context(
    bridgelab: DecisionEvidence[object],
    external: DecisionEvidence[object],
    *,
    same_convention: bool | None = None,
    same_treatment: bool | None = None,
    same_partnership_agreement: bool | None = None,
    bridgelab_policy_expected: bool = False,
    engine_defect_evidence: bool = False,
) -> DisagreementContext:
    """Build explicit disagreement context without guessing system identity."""
    relationship = bidding_system_relationship(bridgelab, external)
    return DisagreementContext(
        external_system_known=relationship.external_system_known,
        same_system=relationship.same_system,
        same_convention=same_convention,
        same_treatment=same_treatment,
        same_partnership_agreement=same_partnership_agreement,
        bridgelab_policy_expected=bridgelab_policy_expected,
        engine_defect_evidence=engine_defect_evidence,
    )


def system_aware_disagreement_contexts(
    bridgelab: DecisionEvidence[object],
    external: tuple[DecisionEvidence[object], ...],
) -> tuple[DisagreementContext, ...]:
    """Build one independent system context per external adviser."""
    if not isinstance(external, tuple):
        raise TypeError("external must be a tuple")
    return tuple(
        system_aware_disagreement_context(bridgelab, observation)
        for observation in external
    )
