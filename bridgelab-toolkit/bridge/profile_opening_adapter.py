"""Pure, shadow-only opening assessment for one bound profile treatment.

This adapter has no base-opening fallback and does not register a bidding route.
An absent or inapplicable pilot treatment never implies a Pass call.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .auction import Auction, CallType
from .models import Hand, Seat, Vulnerability
from .nisim_nily_six_minor_preempt_policy import SixMinorDecision, SixMinorPreemptAssessment
from .profile_compiler import CompiledProfilePlan
from .system_profiles import SystemProfile
from .treatment_bindings import (
    TreatmentImplementationBinding,
    bind_compiled_directive,
    evaluate_bound_treatment,
)


SIX_MINOR_FAMILY = "opening.three_level.six_minor"


class ProfileOpeningDisposition(Enum):
    NO_BINDING = "NO_BINDING"
    SUPPORTED_CALL = "SUPPORTED_CALL"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True, slots=True)
class ProfileOpeningAssessment:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    family: str
    effective_treatment_id: str | None
    disposition: ProfileOpeningDisposition
    acting_seat: Seat
    opening_position: int
    vulnerability: Vulnerability
    binding: TreatmentImplementationBinding | None
    policy_assessment: SixMinorPreemptAssessment | None
    supported_call: str | None
    reason: str
    production_adopted: bool = False
    adapter_version: str = "30C.1"

    def __post_init__(self) -> None:
        if self.production_adopted is not False:
            raise ValueError("Phase 30C adapter cannot be adopted by production")

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "family": self.family,
            "effective_treatment_id": self.effective_treatment_id,
            "disposition": self.disposition.value,
            "acting_seat": self.acting_seat.value,
            "opening_position": self.opening_position,
            "vulnerability": self.vulnerability.value,
            "binding": None if self.binding is None else self.binding.to_dict(),
            "policy_assessment": (
                None if self.policy_assessment is None else self.policy_assessment.to_dict()
            ),
            "supported_call": self.supported_call,
            "reason": self.reason,
            "production_adopted": self.production_adopted,
            "adapter_version": self.adapter_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def evaluate_profile_opening_shadow(
    plan: CompiledProfilePlan,
    *,
    hand: Hand,
    auction: Auction,
    vulnerability: Vulnerability,
) -> ProfileOpeningAssessment:
    """Assess a live, Pass-only opening position through the effective pilot binding."""
    if not isinstance(plan, CompiledProfilePlan):
        raise TypeError("plan must be CompiledProfilePlan")
    if not isinstance(hand, Hand):
        raise TypeError("hand must be Hand")
    if not isinstance(auction, Auction):
        raise TypeError("auction must be Auction")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("vulnerability must be Vulnerability")

    calls = auction.calls
    if auction.is_complete or len(calls) > 3 or any(
        call.kind is not CallType.PASS for call in calls
    ):
        raise ValueError("adapter requires a live, unopened Pass-only auction")

    seat = auction.next_seat
    position = len(calls) + 1
    directive = plan.directive(SIX_MINOR_FAMILY)
    treatment_id = None if directive is None else directive.effective_treatment_id
    binding = None if directive is None else bind_compiled_directive(directive)
    common = dict(
        profile_id=plan.profile_id,
        profile_version=plan.profile_version,
        base_system=plan.base_system,
        family=SIX_MINOR_FAMILY,
        effective_treatment_id=treatment_id,
        acting_seat=seat,
        opening_position=position,
        vulnerability=vulnerability,
    )
    if binding is None:
        return ProfileOpeningAssessment(
            **common,
            disposition=ProfileOpeningDisposition.NO_BINDING,
            binding=None,
            policy_assessment=None,
            supported_call=None,
            reason="No supported implementation binding for the effective pilot treatment.",
        )

    policy = evaluate_bound_treatment(
        binding, hand=hand, seat=seat, vulnerability=vulnerability, opening_position=position
    )
    supported = {
        SixMinorDecision.THREE_LEVEL: {"3C", "3D"},
        SixMinorDecision.ONE_LEVEL: {"1C", "1D"},
    }
    if policy.decision in supported:
        if policy.preferred_call not in supported[policy.decision]:
            raise ValueError("bound policy returned an unsupported opening call")
        disposition = ProfileOpeningDisposition.SUPPORTED_CALL
        call = policy.preferred_call
    elif policy.decision in (SixMinorDecision.NO_THREE_LEVEL, SixMinorDecision.NOT_APPLICABLE):
        if policy.preferred_call is not None:
            raise ValueError("abstaining bound policy returned a call")
        disposition = ProfileOpeningDisposition.ABSTAIN
        call = None
    else:
        raise ValueError("unrecognized bound policy decision")
    return ProfileOpeningAssessment(
        **common,
        disposition=disposition,
        binding=binding,
        policy_assessment=policy,
        supported_call=call,
        reason=policy.reason,
    )
