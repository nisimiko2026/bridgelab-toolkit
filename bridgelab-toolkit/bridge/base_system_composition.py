"""Typed shadow ownership contract between profile openings and base systems.

The result can request continuation by the declared base system, but never
executes a base router or converts a call into a production recommendation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .profile_compiler import CompilationAction, CompiledProfilePlan
from .profile_opening_adapter import ProfileOpeningAssessment, ProfileOpeningDisposition
from .system_profiles import SystemProfile


class BaseSystemCompositionDisposition(str, Enum):
    PARTNERSHIP_CALL = "PARTNERSHIP_CALL"
    BASE_SYSTEM_CONTINUATION = "BASE_SYSTEM_CONTINUATION"
    PROFILE_OVERRIDE_BLOCKS_BASE = "PROFILE_OVERRIDE_BLOCKS_BASE"
    UNRESOLVED = "UNRESOLVED"


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


@dataclass(frozen=True, slots=True)
class BaseSystemContinuationRequest:
    """Handoff to a future base-system layer, not an executable fallback."""

    profile_id: str
    profile_version: str
    base_system: SystemProfile
    family: str
    reason: str
    contract_version: str = "30G.1"

    def __post_init__(self) -> None:
        for name in ("profile_id", "profile_version", "family", "reason", "contract_version"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        if not isinstance(self.base_system, SystemProfile) or self.base_system is SystemProfile.UNKNOWN:
            raise ValueError("base_system must be a known SystemProfile")

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "family": self.family,
            "reason": self.reason,
            "contract_version": self.contract_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class BaseSystemCompositionAssessment:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    family: str
    compilation_action: CompilationAction | None
    profile_disposition: ProfileOpeningDisposition
    composition_disposition: BaseSystemCompositionDisposition
    partnership_call: str | None
    base_continuation: BaseSystemContinuationRequest | None
    reason: str
    production_adopted: bool = False
    composition_version: str = "30G.1"

    def __post_init__(self) -> None:
        for name in ("profile_id", "profile_version", "family", "reason", "composition_version"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        if not isinstance(self.base_system, SystemProfile) or self.base_system is SystemProfile.UNKNOWN:
            raise ValueError("base_system must be a known SystemProfile")
        if self.compilation_action is not None and not isinstance(self.compilation_action, CompilationAction):
            raise TypeError("compilation_action must be CompilationAction or None")
        if not isinstance(self.profile_disposition, ProfileOpeningDisposition):
            raise TypeError("profile_disposition must be ProfileOpeningDisposition")
        if not isinstance(self.composition_disposition, BaseSystemCompositionDisposition):
            raise TypeError("composition_disposition must be BaseSystemCompositionDisposition")
        if self.production_adopted is not False:
            raise ValueError("Phase 30G composition cannot be adopted by production")

        if self.composition_disposition is BaseSystemCompositionDisposition.PARTNERSHIP_CALL:
            if self.profile_disposition is not ProfileOpeningDisposition.SUPPORTED_CALL:
                raise ValueError("PARTNERSHIP_CALL requires a supported profile call")
            if self.compilation_action in (None, CompilationAction.REMOVE):
                raise ValueError("absent or removed treatment cannot own a call")
            if self.partnership_call is None:
                raise ValueError("PARTNERSHIP_CALL requires an explicit call")
            if _nonblank(self.partnership_call, "partnership_call").upper() in ("P", "PASS"):
                raise ValueError("Pass is not a supported partnership opening call")
            if self.base_continuation is not None:
                raise ValueError("PARTNERSHIP_CALL cannot request base continuation")
        elif self.composition_disposition is BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION:
            if self.profile_disposition is ProfileOpeningDisposition.SUPPORTED_CALL:
                raise ValueError("supported profile call cannot request base continuation")
            if self.compilation_action in (CompilationAction.REMOVE, CompilationAction.REPLACE):
                raise ValueError("removed or replaced meaning cannot request base continuation")
            if self.partnership_call is not None:
                raise ValueError("base continuation cannot contain a partnership call")
            request = self.base_continuation
            if not isinstance(request, BaseSystemContinuationRequest):
                raise ValueError("base continuation requires a typed request")
            if (request.profile_id, request.profile_version, request.base_system, request.family) != (
                self.profile_id, self.profile_version, self.base_system, self.family
            ):
                raise ValueError("base continuation request must match composition identity")
        else:
            if self.profile_disposition is ProfileOpeningDisposition.SUPPORTED_CALL:
                raise ValueError("supported profile call cannot be blocked or unresolved")
            if self.partnership_call is not None or self.base_continuation is not None:
                raise ValueError("blocked or unresolved composition cannot contain a call or continuation")

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "family": self.family,
            "compilation_action": None if self.compilation_action is None else self.compilation_action.value,
            "profile_disposition": self.profile_disposition.value,
            "composition_disposition": self.composition_disposition.value,
            "partnership_call": self.partnership_call,
            "base_continuation": None if self.base_continuation is None else self.base_continuation.to_dict(),
            "reason": self.reason,
            "production_adopted": self.production_adopted,
            "composition_version": self.composition_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compose_profile_opening_with_base(
    plan: CompiledProfilePlan,
    assessment: ProfileOpeningAssessment,
) -> BaseSystemCompositionAssessment:
    """Resolve semantic ownership without evaluating the declared base system."""
    if not isinstance(plan, CompiledProfilePlan):
        raise TypeError("plan must be CompiledProfilePlan")
    if not isinstance(assessment, ProfileOpeningAssessment):
        raise TypeError("assessment must be ProfileOpeningAssessment")
    if (assessment.profile_id, assessment.profile_version, assessment.base_system) != (
        plan.profile_id, plan.profile_version, plan.base_system
    ):
        raise ValueError("assessment does not belong to the supplied compiled plan")
    family = _nonblank(assessment.family, "family").casefold()
    directive = plan.directive(family)
    effective_id = None if directive is None else directive.effective_treatment_id
    if assessment.effective_treatment_id != effective_id:
        raise ValueError("assessment treatment does not match the compiled directive")
    if assessment.binding is not None and (
        assessment.binding.family != family
        or assessment.binding.treatment_id != effective_id
    ):
        raise ValueError("assessment binding does not match the compiled directive")
    if assessment.disposition is ProfileOpeningDisposition.SUPPORTED_CALL:
        if directive is None or directive.action is CompilationAction.REMOVE:
            raise ValueError("an absent or removed treatment cannot own a call")
        call = _nonblank(assessment.supported_call, "supported_call")
        if call.upper() in ("P", "PASS"):
            raise ValueError("Pass is not a supported partnership opening call")
        disposition = BaseSystemCompositionDisposition.PARTNERSHIP_CALL
        reason = "The effective treatment supplied an explicit opening call."
        continuation = None
    else:
        if assessment.supported_call is not None:
            raise ValueError("an assessment without SUPPORTED_CALL cannot contain a call")
        call = None
        action = None if directive is None else directive.action
        if action in (CompilationAction.REMOVE, CompilationAction.REPLACE):
            disposition = BaseSystemCompositionDisposition.PROFILE_OVERRIDE_BLOCKS_BASE
            reason = "The profile removed or replaced the base meaning; base continuation is forbidden."
        elif action is CompilationAction.ADD:
            evaluated = (
                assessment.disposition is ProfileOpeningDisposition.ABSTAIN
                and assessment.binding is not None
                and assessment.policy_assessment is not None
            )
            if evaluated:
                disposition = BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION
                reason = "The added treatment was evaluated and abstained; base semantics remain available."
            else:
                disposition = BaseSystemCompositionDisposition.UNRESOLVED
                reason = "An explicitly added treatment lacks a confirmed executable assessment."
        elif action is CompilationAction.KEEP or directive is None:
            if assessment.disposition is ProfileOpeningDisposition.NO_BINDING or (
                action is CompilationAction.KEEP
                and assessment.disposition is ProfileOpeningDisposition.ABSTAIN
                and assessment.binding is not None
                and assessment.policy_assessment is not None
            ):
                disposition = BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION
                reason = "No partnership call displaced the preserved base-system meaning."
            else:
                disposition = BaseSystemCompositionDisposition.UNRESOLVED
                reason = "The no-call assessment is inconsistent with preserved base ownership."
        else:
            disposition = BaseSystemCompositionDisposition.UNRESOLVED
            reason = "The compiled ownership action is unsupported."
        continuation = (
            BaseSystemContinuationRequest(
                plan.profile_id, plan.profile_version, plan.base_system, family, reason
            )
            if disposition is BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION
            else None
        )
    return BaseSystemCompositionAssessment(
        profile_id=plan.profile_id,
        profile_version=plan.profile_version,
        base_system=plan.base_system,
        family=family,
        compilation_action=None if directive is None else directive.action,
        profile_disposition=assessment.disposition,
        composition_disposition=disposition,
        partnership_call=call,
        base_continuation=continuation,
        reason=reason,
    )


@dataclass(frozen=True, slots=True)
class BaseSystemCompositionCapability:
    phase: str = "30G"
    composition_contract_ready: bool = True
    base_continuation_request_ready: bool = True
    base_execution_ready: bool = False
    production_bidding_changed: bool = False
    production_adopted: bool = False
    version: str = "30G.1"

    def __post_init__(self) -> None:
        if self.base_execution_ready is not False:
            raise ValueError("Phase 30G does not execute base systems")
        if self.production_bidding_changed is not False or self.production_adopted is not False:
            raise ValueError("Phase 30G cannot claim production activation")

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "composition_contract_ready": self.composition_contract_ready,
            "base_continuation_request_ready": self.base_continuation_request_ready,
            "base_execution_ready": self.base_execution_ready,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "version": self.version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
