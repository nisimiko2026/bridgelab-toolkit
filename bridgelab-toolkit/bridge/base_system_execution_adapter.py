"""Phase 30I legacy context compatibility for an approved base continuation.

This prepares a SystemContext. It does not select an engine, execute a base
opening, or convert a shadow assessment into a production recommendation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .base_system_composition import BaseSystemContinuationRequest
from .bidding_rules import SystemContext
from .profile_compiler import CompiledProfilePlan
from .system_profiles import SystemProfile, classify_system_profile


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


def _legacy_context(base_system: SystemProfile) -> SystemContext:
    if base_system is SystemProfile.TWO_OVER_ONE_GF:
        # Migration compatibility for legacy 2/1 rules. This is not an
        # optional partnership selection in the typed base-system model.
        return SystemContext.from_mapping("TWO_OVER_ONE_GF", {"two_over_one": "game_force"})
    if base_system is SystemProfile.SAYC:
        return SystemContext("SAYC")
    raise ValueError(f"unsupported base system: {base_system!r}")


@dataclass(frozen=True, slots=True)
class BaseSystemExecutionContext:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    family: str
    system_context: SystemContext
    adapter_version: str = "30I.1"
    production_adopted: bool = False

    def __post_init__(self) -> None:
        for name in ("profile_id", "profile_version", "family", "adapter_version"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        if not isinstance(self.base_system, SystemProfile) or self.base_system is SystemProfile.UNKNOWN:
            raise ValueError("base_system must be a supported SystemProfile")
        if not isinstance(self.system_context, SystemContext):
            raise TypeError("system_context must be canonical SystemContext")
        if self.system_context != _legacy_context(self.base_system):
            raise ValueError("system_context must represent only the declared base system")
        if classify_system_profile(self.system_context) is not self.base_system:
            raise ValueError("legacy system identity differs from declared base system")
        if self.production_adopted is not False:
            raise ValueError("Phase 30I does not activate production bidding")

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "family": self.family,
            "system_context": {
                "system": self.system_context.system,
                "options": [list(pair) for pair in self.system_context.options],
            },
            "adapter_version": self.adapter_version,
            "production_adopted": self.production_adopted,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class BaseSystemExecutionCapability:
    """Verification report supplied with observed component-test outcomes."""

    two_over_one_response_component_verified: bool
    two_over_one_rebid_component_verified: bool
    legacy_context_adapter_ready: bool = True
    opening_component_ready: bool = False
    generic_base_execution_ready: bool = False
    production_bidding_changed: bool = False
    production_adopted: bool = False
    phase: str = "30I"
    version: str = "30I.1"

    def __post_init__(self) -> None:
        for name in (
            "two_over_one_response_component_verified",
            "two_over_one_rebid_component_verified",
            "legacy_context_adapter_ready",
            "opening_component_ready",
            "generic_base_execution_ready",
            "production_bidding_changed",
            "production_adopted",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be bool")
        if self.opening_component_ready or self.generic_base_execution_ready:
            raise ValueError("Phase 30I has no executable 2/1 base opening or generic base engine")
        if self.production_bidding_changed or self.production_adopted:
            raise ValueError("Phase 30I cannot claim production activation")

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "legacy_context_adapter_ready": self.legacy_context_adapter_ready,
            "two_over_one_response_component_verified": self.two_over_one_response_component_verified,
            "two_over_one_rebid_component_verified": self.two_over_one_rebid_component_verified,
            "opening_component_ready": self.opening_component_ready,
            "generic_base_execution_ready": self.generic_base_execution_ready,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "version": self.version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def adapt_base_system_continuation(
    plan: CompiledProfilePlan,
    request: BaseSystemContinuationRequest,
) -> BaseSystemExecutionContext:
    """Preserve approved handoff identity while preparing legacy rule input."""
    if not isinstance(plan, CompiledProfilePlan):
        raise TypeError("plan must be CompiledProfilePlan")
    if not isinstance(request, BaseSystemContinuationRequest):
        raise TypeError("request must be BaseSystemContinuationRequest")
    if (plan.profile_id, plan.profile_version, plan.base_system) != (
        request.profile_id, request.profile_version, request.base_system
    ):
        raise ValueError("continuation request does not match compiled plan identity")
    context = _legacy_context(plan.base_system)
    return BaseSystemExecutionContext(
        profile_id=request.profile_id,
        profile_version=request.profile_version,
        base_system=request.base_system,
        family=request.family,
        system_context=context,
    )
