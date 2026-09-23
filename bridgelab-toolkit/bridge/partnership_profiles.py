"""Immutable partnership configuration; no production bidding integration.

Callers supply base agreements explicitly. Sources are opaque evidence IDs,
never files to load. Capabilities are base metadata passed through unchanged
in meaning; selecting a treatment does not infer capabilities or bidding rules.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .system_profiles import SystemProfile


class AgreementResolution(Enum):
    INHERIT = "INHERIT"
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"
    REPLACE = "REPLACE"


class AgreementSourceScope(Enum):
    SYSTEM = "SYSTEM"
    PARTNERSHIP = "PARTNERSHIP"


def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


def _tuple(value: tuple, name: str) -> tuple:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be a tuple")
    return value


def _parameters(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    result = {}
    for pair in _tuple(values, "parameters"):
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError("parameters must contain (key, value) tuples")
        key, value = pair
        key = _text(key, "parameter key").casefold()
        if key in result:
            raise ValueError(f"duplicate parameter key: {key}")
        if not isinstance(value, str):
            raise TypeError("parameter value must be a string")
        result[key] = value.strip()
    return tuple(sorted(result.items()))


def _strings(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    # IDs retain case; duplicates have no additional meaning in metadata sets.
    return tuple(sorted({_text(value, name) for value in _tuple(values, name)},
                        key=lambda value: (value.casefold(), value)))


def _agreements(values: tuple, expected: type) -> tuple:
    seen = set()
    for value in _tuple(values, "agreements"):
        if not isinstance(value, expected):
            raise TypeError(f"agreements must contain {expected.__name__}")
        if value.family in seen:
            raise ValueError(f"duplicate agreement family: {value.family}")
        seen.add(value.family)
    return tuple(sorted(values, key=lambda value: value.family))


def _profile_identity(profile) -> None:
    object.__setattr__(profile, "profile_id", _text(profile.profile_id, "profile_id"))
    object.__setattr__(profile, "version", _text(profile.version, "version"))
    if not isinstance(profile.base_system, SystemProfile):
        raise TypeError("base_system must be SystemProfile")
    if profile.base_system is SystemProfile.UNKNOWN:
        raise ValueError("UNKNOWN base system cannot be resolved")
    object.__setattr__(profile, "sources", _strings(profile.sources, "sources"))


def _resolution(value: AgreementResolution) -> None:
    if not isinstance(value, AgreementResolution):
        raise TypeError("resolution must be AgreementResolution")


@dataclass(frozen=True, slots=True)
class AgreementSelection:
    """Explicit choice for one family, with case-insensitive family/key IDs.

    Parameters configure ENABLE/REPLACE. INHERIT keeps the complete base
    agreement, including its parameters; DISABLE removes it entirely.
    """

    family: str
    resolution: AgreementResolution
    treatment_id: str | None = None
    parameters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", _text(self.family, "family").casefold())
        _resolution(self.resolution)
        if self.resolution in (AgreementResolution.INHERIT, AgreementResolution.DISABLE):
            if self.treatment_id is not None:
                raise ValueError("INHERIT/DISABLE treatment_id must be None")
        else:
            object.__setattr__(self, "treatment_id", _text(self.treatment_id, "treatment_id"))
        object.__setattr__(self, "parameters", _parameters(self.parameters))

    def option(self, key: str, default: str | None = None) -> str | None:
        return dict(self.parameters).get(_text(key, "option key").casefold(), default)

    def to_dict(self) -> dict:
        return {"family": self.family, "resolution": self.resolution.value,
                "treatment_id": self.treatment_id,
                "parameters": [list(pair) for pair in self.parameters]}


@dataclass(frozen=True, slots=True)
class PartnershipProfile:
    profile_id: str
    version: str
    base_system: SystemProfile
    agreements: tuple[AgreementSelection, ...]
    sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _profile_identity(self)
        object.__setattr__(self, "agreements", _agreements(self.agreements, AgreementSelection))

    def to_dict(self) -> dict:
        return {"profile_id": self.profile_id, "version": self.version,
                "base_system": self.base_system.value,
                "agreements": [agreement.to_dict() for agreement in self.agreements],
                "sources": list(self.sources)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ResolvedAgreement:
    """Effective treatment plus provenance and its opaque string parameters."""

    family: str
    treatment_id: str | None
    resolution: AgreementResolution
    source_scope: AgreementSourceScope
    parameters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", _text(self.family, "family").casefold())
        _resolution(self.resolution)
        if not isinstance(self.source_scope, AgreementSourceScope):
            raise TypeError("source_scope must be AgreementSourceScope")
        if self.resolution is AgreementResolution.DISABLE:
            if self.treatment_id is not None:
                raise ValueError("DISABLE treatment_id must be None")
        elif self.treatment_id is not None or self.resolution is not AgreementResolution.INHERIT:
            object.__setattr__(self, "treatment_id", _text(self.treatment_id, "treatment_id"))
        object.__setattr__(self, "parameters", _parameters(self.parameters))

    def option(self, key: str, default: str | None = None) -> str | None:
        return dict(self.parameters).get(_text(key, "option key").casefold(), default)

    def to_dict(self) -> dict:
        return {"family": self.family, "treatment_id": self.treatment_id,
                "resolution": self.resolution.value, "source_scope": self.source_scope.value,
                "parameters": [list(pair) for pair in self.parameters]}


@dataclass(frozen=True, slots=True)
class ResolvedBiddingProfile:
    profile_id: str
    version: str
    base_system: SystemProfile
    agreements: tuple[ResolvedAgreement, ...]
    capabilities: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _profile_identity(self)
        object.__setattr__(self, "agreements", _agreements(self.agreements, ResolvedAgreement))
        object.__setattr__(self, "capabilities", _strings(self.capabilities, "capabilities"))

    def agreement(self, family: str) -> ResolvedAgreement | None:
        key = _text(family, "family").casefold()
        return next((value for value in self.agreements if value.family == key), None)

    def to_dict(self) -> dict:
        return {"profile_id": self.profile_id, "version": self.version,
                "base_system": self.base_system.value,
                "agreements": [agreement.to_dict() for agreement in self.agreements],
                "capabilities": list(self.capabilities), "sources": list(self.sources)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def resolve_partnership_profile(
    profile: PartnershipProfile,
    *,
    base_agreements: tuple[ResolvedAgreement, ...] = (),
    base_capabilities: tuple[str, ...] = (),
) -> ResolvedBiddingProfile:
    """Resolve only the supplied data, without registry, I/O, or rule activation.

    Unmentioned base families are retained. INHERIT with no base stays absent.
    REPLACE and ENABLE set the complete partnership treatment and parameters.
    Capabilities are independent metadata, not derived from effective families.
    """
    if not isinstance(profile, PartnershipProfile):
        raise TypeError("profile must be PartnershipProfile")
    base = _agreements(base_agreements, ResolvedAgreement)
    effective = {agreement.family: agreement for agreement in base}
    for selection in profile.agreements:
        if selection.resolution is AgreementResolution.INHERIT:
            continue
        if selection.resolution is AgreementResolution.DISABLE:
            effective.pop(selection.family, None)
        else:
            effective[selection.family] = ResolvedAgreement(
                family=selection.family, treatment_id=selection.treatment_id,
                resolution=selection.resolution, source_scope=AgreementSourceScope.PARTNERSHIP,
                parameters=selection.parameters,
            )
    return ResolvedBiddingProfile(
        profile.profile_id, profile.version, profile.base_system,
        tuple(effective.values()), base_capabilities, profile.sources,
    )
