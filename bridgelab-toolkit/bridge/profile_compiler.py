"""Pure, non-production comparison of base and effective agreement families.

The plan describes semantic changes only. It contains no route, engine,
matcher, implementation registry, or treatment-to-route binding.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .partnership_profiles import (
    AgreementResolution,
    AgreementSourceScope,
    ResolvedAgreement,
    ResolvedBiddingProfile,
)
from .system_profiles import SystemProfile


class CompilationAction(Enum):
    KEEP = "KEEP"
    ADD = "ADD"
    REMOVE = "REMOVE"
    REPLACE = "REPLACE"


def _nonblank(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be blank")
    return value


def _parameters(value: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, tuple):
        raise TypeError("parameters must be a tuple")
    normalized: dict[str, str] = {}
    for pair in value:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError("parameters must contain (key, value) tuples")
        key, item = pair
        key = _nonblank(key, "parameter key").casefold()
        if key in normalized:
            raise ValueError(f"duplicate parameter key: {key}")
        if not isinstance(item, str):
            raise TypeError("parameter value must be a string")
        normalized[key] = item.strip()
    return tuple(sorted(normalized.items()))


def _metadata(value: tuple[str, ...], field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    normalized = {_nonblank(item, field) for item in value}
    return tuple(sorted(normalized, key=lambda item: (item.casefold(), item)))


@dataclass(frozen=True, slots=True)
class CompiledAgreementDirective:
    family: str
    action: CompilationAction
    base_treatment_id: str | None
    effective_treatment_id: str | None
    base_parameters: tuple[tuple[str, str], ...] = ()
    effective_parameters: tuple[tuple[str, str], ...] = ()
    effective_source_scope: AgreementSourceScope | None = None
    effective_resolution: AgreementResolution | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", _nonblank(self.family, "family").casefold())
        if not isinstance(self.action, CompilationAction):
            raise TypeError("action must be CompilationAction")
        if self.base_treatment_id is not None:
            object.__setattr__(self, "base_treatment_id", _nonblank(self.base_treatment_id, "base_treatment_id"))
        if self.effective_treatment_id is not None:
            object.__setattr__(self, "effective_treatment_id", _nonblank(self.effective_treatment_id, "effective_treatment_id"))
        object.__setattr__(self, "base_parameters", _parameters(self.base_parameters))
        object.__setattr__(self, "effective_parameters", _parameters(self.effective_parameters))

        base_exists = self.base_treatment_id is not None
        effective_exists = self.effective_treatment_id is not None
        if not base_exists and self.base_parameters:
            raise ValueError("absent base treatment cannot have parameters")
        if not effective_exists:
            if self.effective_parameters or self.effective_source_scope is not None or self.effective_resolution is not None:
                raise ValueError("absent effective treatment cannot have parameters or provenance")
        elif not isinstance(self.effective_source_scope, AgreementSourceScope) or not isinstance(
            self.effective_resolution, AgreementResolution
        ):
            raise TypeError("effective treatment requires typed source scope and resolution")

        same_signature = (
            self.base_treatment_id, self.base_parameters
        ) == (
            self.effective_treatment_id, self.effective_parameters
        )
        valid = {
            CompilationAction.KEEP: base_exists and effective_exists and same_signature,
            CompilationAction.ADD: not base_exists and effective_exists,
            CompilationAction.REMOVE: base_exists and not effective_exists,
            CompilationAction.REPLACE: base_exists and effective_exists and not same_signature,
        }
        if not valid[self.action]:
            raise ValueError(f"invalid {self.action.value} treatment state")

    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "action": self.action.value,
            "base_treatment_id": self.base_treatment_id,
            "effective_treatment_id": self.effective_treatment_id,
            "base_parameters": [list(pair) for pair in self.base_parameters],
            "effective_parameters": [list(pair) for pair in self.effective_parameters],
            "effective_source_scope": None if self.effective_source_scope is None else self.effective_source_scope.value,
            "effective_resolution": None if self.effective_resolution is None else self.effective_resolution.value,
        }


@dataclass(frozen=True, slots=True)
class CompiledProfilePlan:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    directives: tuple[CompiledAgreementDirective, ...]
    capabilities: tuple[str, ...]
    sources: tuple[str, ...]
    production_adopted: bool = False
    compiler_version: str = "30A.1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _nonblank(self.profile_id, "profile_id"))
        object.__setattr__(self, "profile_version", _nonblank(self.profile_version, "profile_version"))
        object.__setattr__(self, "compiler_version", _nonblank(self.compiler_version, "compiler_version"))
        if not isinstance(self.base_system, SystemProfile) or self.base_system is SystemProfile.UNKNOWN:
            raise ValueError("base_system must be a known SystemProfile")
        if not isinstance(self.directives, tuple):
            raise TypeError("directives must be a tuple")
        seen: set[str] = set()
        for directive in self.directives:
            if not isinstance(directive, CompiledAgreementDirective):
                raise TypeError("directives must contain CompiledAgreementDirective")
            if directive.family in seen:
                raise ValueError(f"duplicate directive family: {directive.family}")
            seen.add(directive.family)
        object.__setattr__(self, "directives", tuple(sorted(self.directives, key=lambda item: item.family)))
        object.__setattr__(self, "capabilities", _metadata(self.capabilities, "capabilities"))
        object.__setattr__(self, "sources", _metadata(self.sources, "sources"))
        if self.production_adopted is not False:
            raise ValueError("Phase 30A plans cannot be adopted by production")

    def directive(self, family: str) -> CompiledAgreementDirective | None:
        key = _nonblank(family, "family").casefold()
        return next((item for item in self.directives if item.family == key), None)

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "directives": [directive.to_dict() for directive in self.directives],
            "capabilities": list(self.capabilities),
            "sources": list(self.sources),
            "production_adopted": self.production_adopted,
            "compiler_version": self.compiler_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compile_profile_plan(
    resolved_profile: ResolvedBiddingProfile,
    *,
    base_agreements: tuple[ResolvedAgreement, ...] = (),
) -> CompiledProfilePlan:
    """Compare canonical agreement values, without binding any route or engine."""
    if not isinstance(resolved_profile, ResolvedBiddingProfile):
        raise TypeError("resolved_profile must be ResolvedBiddingProfile")
    if not isinstance(base_agreements, tuple):
        raise TypeError("base_agreements must be a tuple")
    base: dict[str, ResolvedAgreement] = {}
    for agreement in base_agreements:
        if not isinstance(agreement, ResolvedAgreement):
            raise TypeError("base_agreements must contain ResolvedAgreement")
        if agreement.family in base:
            raise ValueError(f"duplicate base agreement family: {agreement.family}")
        if agreement.treatment_id is None:
            raise ValueError(f"base agreement lacks treatment: {agreement.family}")
        base[agreement.family] = agreement

    effective = {agreement.family: agreement for agreement in resolved_profile.agreements}
    for agreement in effective.values():
        if agreement.treatment_id is None:
            raise ValueError(f"effective agreement lacks treatment: {agreement.family}")

    directives = []
    for family in sorted(base.keys() | effective.keys()):
        before = base.get(family)
        after = effective.get(family)
        if before is None:
            action = CompilationAction.ADD
        elif after is None:
            action = CompilationAction.REMOVE
        elif (before.treatment_id, before.parameters) == (after.treatment_id, after.parameters):
            action = CompilationAction.KEEP
        else:
            action = CompilationAction.REPLACE
        directives.append(CompiledAgreementDirective(
            family=family,
            action=action,
            base_treatment_id=None if before is None else before.treatment_id,
            effective_treatment_id=None if after is None else after.treatment_id,
            base_parameters=() if before is None else before.parameters,
            effective_parameters=() if after is None else after.parameters,
            effective_source_scope=None if after is None else after.source_scope,
            effective_resolution=None if after is None else after.resolution,
        ))

    return CompiledProfilePlan(
        profile_id=resolved_profile.profile_id,
        profile_version=resolved_profile.version,
        base_system=resolved_profile.base_system,
        directives=tuple(directives),
        capabilities=resolved_profile.capabilities,
        sources=resolved_profile.sources,
    )
