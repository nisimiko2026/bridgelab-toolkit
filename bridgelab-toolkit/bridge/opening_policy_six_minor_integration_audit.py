"""Phase 29U integration of the Nisim–Nily exact-six-minor policy.

Additive audit/consolidation layer only. It composes Phase 29S with Phase 29T.
Historical modules remain unchanged and no production route is registered.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .auction import Auction
from .models import Hand, Vulnerability
from .nisim_nily_six_minor_preempt_policy import (
    SixMinorDecision,
    SixMinorPreemptAssessment,
    assess_six_minor_three_level_preempt,
)
from .opening_policy_consolidation_audit import (
    Assessment,
    Classification,
    assess_opening_policy,
)


class _Serializable:
    __slots__ = ()

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True, slots=True)
class IntegratedOpeningAssessment(_Serializable):
    base: Assessment
    six_minor: SixMinorPreemptAssessment
    classification: Classification
    supported_call: str | None
    resolved_blockers: tuple[str, ...]
    unresolved_blockers: tuple[str, ...]
    integration_applied: bool
    reason: str
    production_adopted: bool = False
    policy_version: str = "nisim-nily.opening-policy-six-minor@29U.1"


_SIX_MINOR_RESOLVED_BLOCKERS = frozenset(
    ("preempt", "later_seat", "individual_review")
)


def assess_opening_policy_with_six_minor(
    hand: Hand,
    *,
    auction: Auction,
    vulnerability: Vulnerability,
) -> IntegratedOpeningAssessment:
    """Compose Phase 29S with Phase 29T without changing production."""
    if not isinstance(auction, Auction):
        raise TypeError("canonical Auction required")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("canonical Vulnerability required")

    base = assess_opening_policy(
        hand,
        auction=auction,
        vulnerability=vulnerability,
    )
    six_minor = assess_six_minor_three_level_preempt(
        hand,
        seat=auction.next_seat,
        vulnerability=vulnerability,
        opening_position=len(auction.calls) + 1,
    )

    if six_minor.decision is SixMinorDecision.NOT_APPLICABLE:
        return IntegratedOpeningAssessment(
            base,
            six_minor,
            base.classification,
            base.supported_call,
            (),
            base.unresolved_blockers,
            False,
            "Phase 29T is not applicable; Phase 29S is preserved.",
        )

    if six_minor.decision is SixMinorDecision.ONE_LEVEL:
        return IntegratedOpeningAssessment(
            base,
            six_minor,
            Classification.OPENING_SUPPORTED,
            six_minor.preferred_call,
            (),
            (),
            True,
            "Phase 29T Rule-of-20 priority supplies the exact one-level minor call.",
        )

    if six_minor.decision is SixMinorDecision.THREE_LEVEL:
        resolved = tuple(
            blocker
            for blocker in base.unresolved_blockers
            if blocker in _SIX_MINOR_RESOLVED_BLOCKERS
        )
        remaining = tuple(
            blocker
            for blocker in base.unresolved_blockers
            if blocker not in _SIX_MINOR_RESOLVED_BLOCKERS
        )
        if remaining:
            return IntegratedOpeningAssessment(
                base,
                six_minor,
                Classification.UNRESOLVED,
                None,
                resolved,
                remaining,
                True,
                "Phase 29T resolves the exact-six-minor preempt, but independent Phase 29S blockers remain.",
            )
        return IntegratedOpeningAssessment(
            base,
            six_minor,
            Classification.PARTNERSHIP_TREATMENT_SUPPORTED,
            six_minor.preferred_call,
            resolved,
            (),
            True,
            "Phase 29T positively resolves the exact-six-minor preempt and superseded generic review blockers.",
        )

    return IntegratedOpeningAssessment(
        base,
        six_minor,
        base.classification,
        base.supported_call,
        (),
        base.unresolved_blockers,
        True,
        "Phase 29T rejects the three-level exception but does not authorize Pass or another opening; Phase 29S is preserved.",
    )
