"""Shared profile bindings and conflict checks for opt-in bidding assessments.

No rule families, hand predicates or production activation live here. The
partnership resolver must supply effective agreements before binding options.
"""
from __future__ import annotations

from .bidding_engine import BiddingEngineResult
from .bidding_rules import RuleDecision, SystemContext
from .major_response_options import (
    FORCING_ONE_NOTRUMP_OPTION, MAJOR_RAISE_STYLE_OPTION, TWO_OVER_ONE_OPTION,
)
from .partnership_profiles import AgreementResolution, PartnershipProfile, ResolvedBiddingProfile
from .policy_registry import SUIT_QUALITY_POLICY_OPTION


# These are bindings to existing option parsers, not new convention meanings.
_MAJOR_OPTIONS = {
    "response.major.1nt": (FORCING_ONE_NOTRUMP_OPTION, {"forcing", "nonforcing"}),
    "response.major.two_over_one": (TWO_OVER_ONE_OPTION, {"game_force", "natural"}),
    "response.major.raises": (MAJOR_RAISE_STYLE_OPTION, {"traditional", "bergen"}),
}


def response_system(
    profile: PartnershipProfile, resolved: ResolvedBiddingProfile, opening: str,
    suit_quality_policy_id: str | None,
    *, extra_families: tuple[str, ...] = (),
) -> tuple[SystemContext, tuple[str, ...]]:
    options: dict[str, str] = {}
    blockers: list[str] = []
    major = opening in ("1H", "1S")
    families = ("opening", f"opening.{opening.lower()}", "response",
                f"response.{opening.lower()}")
    if major:
        families += ("response.major",)
    elif opening in ("1C", "1D"):
        families += ("response.minor",)

    families += extra_families

    def relevant(family: str) -> bool:
        # Generic opening/response declarations apply globally within this
        # profile, but unrelated opening families do not contaminate the call.
        return family in families or any(
            family.startswith(prefix + ".") for prefix in families
            if prefix not in ("opening", "response")
        )

    for agreement in resolved.agreements:
        if not relevant(agreement.family):
            continue
        binding = _MAJOR_OPTIONS.get(agreement.family) if major else None
        if (binding is None or agreement.parameters
                or agreement.treatment_id not in binding[1]):
            blockers.append(f"Unsupported effective treatment or parameters: {agreement.family}")
            continue
        options[binding[0]] = agreement.treatment_id

    # The resolver removes disabled families. Preserve that explicit removal:
    # notably, absence must not resurrect the rules' traditional-raise default.
    for selection in profile.agreements:
        if selection.resolution is not AgreementResolution.DISABLE or not relevant(selection.family):
            continue
        binding = _MAJOR_OPTIONS.get(selection.family) if major else None
        if binding is None:
            blockers.append(f"Disabled opening/response family: {selection.family}")
        else:
            options[binding[0]] = "other" if selection.family == "response.major.raises" else "unspecified"

    if suit_quality_policy_id is not None:
        if not isinstance(suit_quality_policy_id, str) or not suit_quality_policy_id.strip():
            raise ValueError("suit_quality_policy_id must be a nonblank string")
        options[SUIT_QUALITY_POLICY_OPTION] = suit_quality_policy_id.strip()
    return SystemContext.from_mapping(resolved.base_system.value, options), tuple(sorted(blockers))


def top_priority_conflicts(evidence: BiddingEngineResult) -> tuple[RuleDecision, ...]:
    """Flag different calls tied at the top, keeping existing priority semantics."""
    if evidence.recommended is None:
        return ()
    tied = tuple(item for item in evidence.candidates
                 if item.priority == evidence.recommended.priority)
    return tied if len(tied) > 1 else ()
