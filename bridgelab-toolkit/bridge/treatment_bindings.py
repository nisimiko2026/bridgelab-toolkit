"""One explicit shadow binding from profile metadata to the Phase 29T assessor.

Availability of this implementation does not activate it for any partnership.
Only an effective compiled treatment may select this binding. No route or
production rule is created here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .models import Hand, Seat, Vulnerability
from .nisim_nily_six_minor_preempt_policy import (
    SixMinorPreemptAssessment,
    assess_six_minor_three_level_preempt,
)
from .profile_compiler import CompilationAction, CompiledAgreementDirective


class TreatmentImplementationKind(Enum):
    POLICY_ASSESSOR = "POLICY_ASSESSOR"


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be blank")
    return normalized


@dataclass(frozen=True, slots=True)
class TreatmentImplementationBinding:
    family: str
    treatment_id: str
    implementation_id: str
    implementation_kind: TreatmentImplementationKind
    implementation_version: str
    production_adopted: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", _nonblank(self.family, "family").casefold())
        object.__setattr__(self, "treatment_id", _nonblank(self.treatment_id, "treatment_id"))
        object.__setattr__(self, "implementation_id", _nonblank(self.implementation_id, "implementation_id"))
        object.__setattr__(self, "implementation_version", _nonblank(self.implementation_version, "implementation_version"))
        if not isinstance(self.implementation_kind, TreatmentImplementationKind):
            raise TypeError("implementation_kind must be TreatmentImplementationKind")
        if self.production_adopted is not False:
            raise ValueError("Phase 30B binding cannot be adopted by production")

    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "treatment_id": self.treatment_id,
            "implementation_id": self.implementation_id,
            "implementation_kind": self.implementation_kind.value,
            "implementation_version": self.implementation_version,
            "production_adopted": self.production_adopted,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


NISIM_NILY_SIX_MINOR_BINDING = TreatmentImplementationBinding(
    family="opening.three_level.six_minor",
    treatment_id="nisim_nily_six_minor_preempt",
    implementation_id="nisim-nily.six-minor-preempt",
    implementation_kind=TreatmentImplementationKind.POLICY_ASSESSOR,
    implementation_version="nisim-nily.six-minor-preempt@29T.1",
)


def get_treatment_binding(
    *, family: str, treatment_id: str
) -> TreatmentImplementationBinding | None:
    """Return the single exact pilot binding; treatment IDs have no aliases."""
    if not isinstance(family, str) or not isinstance(treatment_id, str):
        raise TypeError("family and treatment_id must be strings")
    normalized_family = family.strip().casefold()
    normalized_treatment = treatment_id.strip()
    if (
        normalized_family == NISIM_NILY_SIX_MINOR_BINDING.family
        and normalized_treatment == NISIM_NILY_SIX_MINOR_BINDING.treatment_id
    ):
        return NISIM_NILY_SIX_MINOR_BINDING
    return None


def bind_compiled_directive(
    directive: CompiledAgreementDirective,
) -> TreatmentImplementationBinding | None:
    """Bind an effective pilot treatment, including KEEP with no delta."""
    if not isinstance(directive, CompiledAgreementDirective):
        raise TypeError("directive must be CompiledAgreementDirective")
    if directive.action is CompilationAction.REMOVE or directive.effective_treatment_id is None:
        return None
    # Phase 29T exposes no treatment-parameter API. An unhandled parameter
    # must not be silently ignored by this pilot binding.
    if directive.effective_parameters:
        return None
    return get_treatment_binding(
        family=directive.family,
        treatment_id=directive.effective_treatment_id,
    )


def evaluate_bound_treatment(
    binding: TreatmentImplementationBinding,
    *,
    hand: Hand,
    seat: Seat,
    vulnerability: Vulnerability,
    opening_position: int,
) -> SixMinorPreemptAssessment:
    """Run only the exact supported shadow binding through Phase 29T."""
    if not isinstance(binding, TreatmentImplementationBinding):
        raise TypeError("binding must be TreatmentImplementationBinding")
    if binding != NISIM_NILY_SIX_MINOR_BINDING:
        raise ValueError("unsupported Phase 30B treatment binding")
    return assess_six_minor_three_level_preempt(
        hand,
        seat=seat,
        vulnerability=vulnerability,
        opening_position=opening_position,
    )
