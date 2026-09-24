"""Phase 30J source and ownership audit for 2/1 base opening execution.

The matrix records what a future opening executor may consider. It evaluates
neither hands nor auctions and creates no bidding recommendation or route.
"""

from __future__ import annotations

from collections import Counter
import json
from dataclasses import dataclass, field
from enum import Enum

from .partnership_profiles import AgreementResolution
from .profile_compiler import CompilationAction, CompiledProfilePlan
from .system_profiles import SystemProfile


class OpeningExecutionBoundaryState(str, Enum):
    BASE_EXECUTABLE = "BASE_EXECUTABLE"
    BASE_SOURCE_PARTIAL = "BASE_SOURCE_PARTIAL"
    PROFILE_OVERRIDE = "PROFILE_OVERRIDE"
    UNSUPPORTED = "UNSUPPORTED"


_SOURCE = "knowledge/bidding/systems/2-over-1.md"
_SAYC_ONLY = "bridge/sayc.py: opening rule gate accepts SAYC only"
_FAMILIES = (
    "opening.1c", "opening.1d", "opening.1h", "opening.1s", "opening.1nt",
    "opening.2c", "opening.2d", "opening.2h", "opening.2s", "opening.2nt",
    "opening.three_level", "opening.three_level.six_minor",
)

# Curated findings from the canonical 2/1 article. No listed family has a
# complete native opening selector/precedence contract or a native 2/1 engine.
_SOURCE_FINDINGS = {
    "opening.1c": (
        OpeningExecutionBoundaryState.BASE_SOURCE_PARTIAL,
        "Natural clubs are usually 3+, but the source varies the minor choice and does not fix exact strength or cross-family precedence.",
        (f"{_SOURCE}#Opening Requirements: 1C natural, usually 3+; partnership variant for 4-4 minors",
         "No exact equal-minor, major, notrump, or strong-hand selector for native 2/1 openings"),
    ),
    "opening.1d": (
        OpeningExecutionBoundaryState.BASE_SOURCE_PARTIAL,
        "Natural diamonds are usually 4+, without an exact minor-choice or cross-family opening selector.",
        (f"{_SOURCE}#Opening Requirements: 1D natural, usually 4+",
         "No exact equal-minor, major, notrump, or strong-hand selector for native 2/1 openings"),
    ),
    "opening.1h": (
        OpeningExecutionBoundaryState.BASE_SOURCE_PARTIAL,
        "Five hearts and approximately 12–21 HCP do not settle 5-5 majors, balanced hands, or strong-hand precedence.",
        (f"{_SOURCE}#Opening Requirements: 1H five cards, approximately 12–21 HCP",
         "No exact 5-5-major, notrump, or strong-hand precedence for native 2/1 openings"),
    ),
    "opening.1s": (
        OpeningExecutionBoundaryState.BASE_SOURCE_PARTIAL,
        "Five spades and approximately 12–21 HCP do not settle 5-5 majors, balanced hands, or strong-hand precedence.",
        (f"{_SOURCE}#Opening Requirements: 1S five cards, same approximate requirements as 1H",
         "No exact 5-5-major, notrump, or strong-hand precedence for native 2/1 openings"),
    ),
    "opening.1nt": (
        OpeningExecutionBoundaryState.BASE_SOURCE_PARTIAL,
        "The 2/1 source says usually 15–17 balanced and explicitly allows 14–16 or 16–18; system identity supplies no exact range.",
        (f"{_SOURCE}#Opening Requirements: 1NT usually 15–17 balanced; alternatives 14–16 and 16–18",
         f"{_SOURCE}#Partnership Agreements: notrump range requires explicit partnership choice"),
    ),
    "opening.2c": (
        OpeningExecutionBoundaryState.UNSUPPORTED,
        "The 2/1 article does not establish a strong 2C opening meaning or its precedence; SAYC's rule is not a native 2/1 contract.",
        (f"{_SOURCE}#Opening Requirements: no 2C opening contract",
         _SAYC_ONLY),
    ),
    "opening.2d": (
        OpeningExecutionBoundaryState.UNSUPPORTED,
        "The 2/1 article does not establish a weak or natural 2D base opening contract.",
        (f"{_SOURCE}#Opening Requirements: no 2D opening contract",
         _SAYC_ONLY),
    ),
    "opening.2h": (
        OpeningExecutionBoundaryState.UNSUPPORTED,
        "The 2/1 article does not establish a weak or natural 2H base opening contract.",
        (f"{_SOURCE}#Opening Requirements: no 2H opening contract",
         _SAYC_ONLY),
    ),
    "opening.2s": (
        OpeningExecutionBoundaryState.UNSUPPORTED,
        "The 2/1 article does not establish a weak or natural 2S base opening contract.",
        (f"{_SOURCE}#Opening Requirements: no 2S opening contract",
         _SAYC_ONLY),
    ),
    "opening.2nt": (
        OpeningExecutionBoundaryState.UNSUPPORTED,
        "The 2/1 article discusses Jacoby 2NT responses and 2NT rebids, not a native 2NT opening range.",
        (f"{_SOURCE}#Opening Requirements: no 2NT opening contract",
         f"{_SOURCE}#Core Principles: 2NT is described as a Jacoby response"),
    ),
    "opening.three_level": (
        OpeningExecutionBoundaryState.UNSUPPORTED,
        "The 2/1 article supplies no executable three-level base opening contract.",
        (f"{_SOURCE}#Opening Requirements: no three-level opening contract",
         _SAYC_ONLY),
    ),
    "opening.three_level.six_minor": (
        OpeningExecutionBoundaryState.UNSUPPORTED,
        "The six-minor treatment is a profile overlay; the 2/1 article supplies no matching base opening contract.",
        (f"{_SOURCE}#Opening Requirements: no six-minor three-level base contract",
         "bridge/nisim_nily_partnership_profile.py: explicit pilot family is partnership-selected"),
    ),
}


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


@dataclass(frozen=True, slots=True)
class OpeningExecutionBoundary:
    family: str
    base_system: SystemProfile
    state: OpeningExecutionBoundaryState
    compiled_action: CompilationAction | None
    base_treatment_id: str | None
    effective_treatment_id: str | None
    effective_resolution: AgreementResolution | None
    source_complete: bool
    implementation_available: bool
    reason: str
    evidence: tuple[str, ...]
    production_adopted: bool = False
    boundary_version: str = "30J.1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", _nonblank(self.family, "family").casefold())
        object.__setattr__(self, "reason", _nonblank(self.reason, "reason"))
        object.__setattr__(self, "boundary_version", _nonblank(self.boundary_version, "boundary_version"))
        if self.base_system is not SystemProfile.TWO_OVER_ONE_GF:
            raise ValueError("boundary requires TWO_OVER_ONE_GF")
        if not isinstance(self.state, OpeningExecutionBoundaryState):
            raise TypeError("state must be OpeningExecutionBoundaryState")
        if self.compiled_action is not None and not isinstance(self.compiled_action, CompilationAction):
            raise TypeError("compiled_action must be CompilationAction or None")
        if self.effective_resolution is not None and not isinstance(self.effective_resolution, AgreementResolution):
            raise TypeError("effective_resolution must be AgreementResolution or None")
        if not isinstance(self.source_complete, bool) or not isinstance(self.implementation_available, bool):
            raise TypeError("source and implementation flags must be bool")
        if not isinstance(self.evidence, tuple) or not self.evidence:
            raise ValueError("evidence must be a nonempty tuple")
        evidence = tuple(sorted({_nonblank(item, "evidence item") for item in self.evidence}))
        object.__setattr__(self, "evidence", evidence)
        override = self.compiled_action in (CompilationAction.REMOVE, CompilationAction.REPLACE) or (
            self.compiled_action is CompilationAction.ADD
            and self.effective_resolution is AgreementResolution.REPLACE)
        if (self.state is OpeningExecutionBoundaryState.PROFILE_OVERRIDE) is not override:
            raise ValueError("override state must match compiled ownership")
        if self.state is OpeningExecutionBoundaryState.BASE_EXECUTABLE and not (
            self.source_complete and self.implementation_available):
            raise ValueError("BASE_EXECUTABLE requires complete source and implementation")
        if self.production_adopted is not False:
            raise ValueError("Phase 30J is audit-only")

    def to_dict(self) -> dict:
        return {
            "family": self.family, "base_system": self.base_system.value,
            "state": self.state.value,
            "compiled_action": None if self.compiled_action is None else self.compiled_action.value,
            "base_treatment_id": self.base_treatment_id,
            "effective_treatment_id": self.effective_treatment_id,
            "effective_resolution": (None if self.effective_resolution is None
                                     else self.effective_resolution.value),
            "source_complete": self.source_complete,
            "implementation_available": self.implementation_available,
            "reason": self.reason, "evidence": list(self.evidence),
            "production_adopted": self.production_adopted,
            "boundary_version": self.boundary_version,
        }


def _recommended_next_phase(boundaries: tuple[OpeningExecutionBoundary, ...],
                            safe: bool) -> str:
    base = tuple(item for item in boundaries if item.state is not OpeningExecutionBoundaryState.PROFILE_OVERRIDE
                 and item.family != "opening.three_level.six_minor")
    if any(not item.source_complete for item in base):
        return "30K_EXPLICIT_TWO_OVER_ONE_OPENING_CONTRACT"
    if any(item.source_complete and not item.implementation_available for item in base):
        return "30K_TWO_OVER_ONE_OPENING_ENGINE"
    if not safe and any(item.state is OpeningExecutionBoundaryState.PROFILE_OVERRIDE
                        for item in boundaries):
        return "30K_PARTNERSHIP_OPENING_CONTRACT"
    return "30K_OPENING_EXECUTION_INTEGRATION" if safe else "30K_EXPLICIT_TWO_OVER_ONE_OPENING_CONTRACT"


@dataclass(frozen=True, slots=True)
class TwoOverOneOpeningExecutionBoundaryAudit:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    boundaries: tuple[OpeningExecutionBoundary, ...]
    production_bidding_changed: bool = False
    production_adopted: bool = False
    audit_version: str = "30J.1"
    base_executable_count: int = field(init=False)
    base_source_partial_count: int = field(init=False)
    profile_override_count: int = field(init=False)
    unsupported_count: int = field(init=False)
    safe_opening_execution_ready: bool = field(init=False)
    recommended_next_phase: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _nonblank(self.profile_id, "profile_id"))
        object.__setattr__(self, "profile_version", _nonblank(self.profile_version, "profile_version"))
        if self.base_system is not SystemProfile.TWO_OVER_ONE_GF:
            raise ValueError("audit requires TWO_OVER_ONE_GF")
        if not isinstance(self.boundaries, tuple) or not all(
                isinstance(item, OpeningExecutionBoundary) for item in self.boundaries):
            raise TypeError("boundaries must contain OpeningExecutionBoundary")
        keys = [item.family for item in self.boundaries]
        if len(keys) != len(set(keys)) or set(keys) != set(_FAMILIES):
            raise ValueError("boundaries must cover each audited opening family exactly once")
        if any(item.base_system is not self.base_system for item in self.boundaries):
            raise ValueError("boundary base system differs from audit")
        boundaries = tuple(sorted(self.boundaries, key=lambda item: item.family))
        object.__setattr__(self, "boundaries", boundaries)
        counts = Counter(item.state for item in boundaries)
        for name, state in (
            ("base_executable_count", OpeningExecutionBoundaryState.BASE_EXECUTABLE),
            ("base_source_partial_count", OpeningExecutionBoundaryState.BASE_SOURCE_PARTIAL),
            ("profile_override_count", OpeningExecutionBoundaryState.PROFILE_OVERRIDE),
            ("unsupported_count", OpeningExecutionBoundaryState.UNSUPPORTED),
        ):
            object.__setattr__(self, name, counts[state])
        base_needed = tuple(item for item in boundaries
                            if item.state is not OpeningExecutionBoundaryState.PROFILE_OVERRIDE
                            and item.family != "opening.three_level.six_minor")
        safe = bool(base_needed) and all(
            item.state is OpeningExecutionBoundaryState.BASE_EXECUTABLE for item in base_needed)
        object.__setattr__(self, "safe_opening_execution_ready", safe)
        object.__setattr__(self, "recommended_next_phase",
                           _recommended_next_phase(boundaries, safe))
        if self.production_bidding_changed or self.production_adopted:
            raise ValueError("Phase 30J cannot claim production activation")

    def boundary(self, family: str) -> OpeningExecutionBoundary | None:
        key = _nonblank(family, "family").casefold()
        return next((item for item in self.boundaries if item.family == key), None)

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id, "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "boundaries": [item.to_dict() for item in self.boundaries],
            "base_executable_count": self.base_executable_count,
            "base_source_partial_count": self.base_source_partial_count,
            "profile_override_count": self.profile_override_count,
            "unsupported_count": self.unsupported_count,
            "safe_opening_execution_ready": self.safe_opening_execution_ready,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "recommended_next_phase": self.recommended_next_phase,
            "audit_version": self.audit_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def audit_two_over_one_opening_execution_boundary(
    plan: CompiledProfilePlan,
) -> TwoOverOneOpeningExecutionBoundaryAudit:
    """Classify native 2/1 openings and preserve compiled profile ownership."""
    if not isinstance(plan, CompiledProfilePlan):
        raise TypeError("plan must be CompiledProfilePlan")
    if plan.base_system is not SystemProfile.TWO_OVER_ONE_GF:
        raise ValueError("opening boundary audit requires TWO_OVER_ONE_GF")
    boundaries = []
    for family in _FAMILIES:
        directive = plan.directive(family)
        action = None if directive is None else directive.action
        resolution = None if directive is None else directive.effective_resolution
        source_state, source_reason, source_evidence = _SOURCE_FINDINGS[family]
        # A REPLACE selection can compile as ADD when no base catalog was
        # supplied. Its explicit partnership intent still blocks base reuse.
        override = action in (CompilationAction.REMOVE, CompilationAction.REPLACE) or (
            action is CompilationAction.ADD and resolution is AgreementResolution.REPLACE)
        if override:
            state = OpeningExecutionBoundaryState.PROFILE_OVERRIDE
            reason = (
                "Compiled REPLACE/REMOVE owns this opening; native base reuse is forbidden."
                if action in (CompilationAction.REMOVE, CompilationAction.REPLACE) else
                "Partnership REPLACE resolution compiles as ADD without a base catalog; native base reuse remains forbidden."
            )
            evidence = source_evidence + (
                f"Compiled directive: action={action.value}; effective resolution="
                f"{None if resolution is None else resolution.value}; base treatment="
                f"{None if directive is None else directive.base_treatment_id}",)
        else:
            state = source_state
            reason = source_reason
            evidence = source_evidence + (
                _SAYC_ONLY,
                f"Compiled directive: action={None if action is None else action.value}; "
                "ADD/KEEP do not by themselves suppress base ownership",
            )
            if action is CompilationAction.ADD and family == "opening.three_level.six_minor":
                evidence += ("Pilot ADD is profile-owned when applicable, not a base implementation",)
        boundaries.append(OpeningExecutionBoundary(
            family=family, base_system=plan.base_system, state=state,
            compiled_action=action,
            base_treatment_id=None if directive is None else directive.base_treatment_id,
            effective_treatment_id=None if directive is None else directive.effective_treatment_id,
            effective_resolution=resolution,
            source_complete=False, implementation_available=False,
            reason=reason, evidence=evidence,
        ))
    return TwoOverOneOpeningExecutionBoundaryAudit(
        profile_id=plan.profile_id, profile_version=plan.profile_version,
        base_system=plan.base_system, boundaries=tuple(boundaries),
    )
