"""Phase 30L declarative Nisim–Nily binding of the generic 2/1 contract.

Current approved Phase 29S rules supply the evidence recorded here. Earlier
Phase 29M propositions remain historical. This module never evaluates hands,
chooses calls, or registers a production route.
"""

from __future__ import annotations

from collections import Counter
import json
from dataclasses import dataclass, field
from enum import Enum

from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .profile_compiler import CompiledProfilePlan
from .system_profiles import SystemProfile
from .two_over_one_opening_contract import (
    TwoOverOneOpeningContract, build_two_over_one_opening_contract,
)


class OpeningBindingState(str, Enum):
    BOUND = "BOUND"
    PARTIAL = "PARTIAL"
    UNRESOLVED = "UNRESOLVED"


_EXPECTED_BINDINGS = (
    "equal_minor_precedence", "five_five_major_precedence", "minor_length_policy",
    "minor_selection_precedence", "one_level_strength_policy",
    "one_notrump_five_card_major_policy", "one_notrump_range",
    "one_notrump_shape_policy", "strong_hand_precedence",
    "suit_vs_notrump_precedence",
)


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


def _strings(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    return tuple(sorted({_nonblank(item, name) for item in values}))


def _parameters(values: tuple[tuple[str, str | int | bool], ...]) -> tuple[tuple[str, str | int | bool], ...]:
    if not isinstance(values, tuple):
        raise TypeError("parameters must be a tuple")
    seen = set()
    result = []
    for pair in values:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError("parameters must contain (name, value) pairs")
        key, value = pair
        key = _nonblank(key, "parameter name")
        if key.casefold() in seen:
            raise ValueError("duplicate parameter name")
        seen.add(key.casefold())
        if not isinstance(value, (str, int, bool)) or isinstance(value, float):
            raise TypeError("parameter values must be str, int, or bool")
        if isinstance(value, str):
            value = _nonblank(value, "parameter value")
        result.append((key, value))
    return tuple(sorted(result, key=lambda pair: pair[0].casefold()))


@dataclass(frozen=True, slots=True)
class OpeningContractBinding:
    binding_id: str
    state: OpeningBindingState
    parameters: tuple[tuple[str, str | int | bool], ...]
    resolved_aspects: tuple[str, ...]
    unresolved_aspects: tuple[str, ...]
    provenance: tuple[str, ...]
    limitations: str
    current_authority: str = "PHASE29S"
    historical_authority: str | None = None
    supersedes_historical_scope: bool = False
    production_adopted: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "binding_id", _nonblank(self.binding_id, "binding_id"))
        if not isinstance(self.state, OpeningBindingState):
            raise TypeError("state must be OpeningBindingState")
        object.__setattr__(self, "parameters", _parameters(self.parameters))
        for name in ("resolved_aspects", "unresolved_aspects", "provenance"):
            object.__setattr__(self, name, _strings(getattr(self, name), name))
        object.__setattr__(self, "limitations", _nonblank(self.limitations, "limitations"))
        object.__setattr__(self, "current_authority", _nonblank(self.current_authority, "current_authority"))
        if self.historical_authority is not None:
            object.__setattr__(self, "historical_authority",
                               _nonblank(self.historical_authority, "historical_authority"))
        if self.supersedes_historical_scope and self.historical_authority is None:
            raise ValueError("supersession requires historical authority")
        if not self.provenance:
            raise ValueError("binding needs provenance")
        if self.state is OpeningBindingState.BOUND and (
                not self.parameters or not self.resolved_aspects or self.unresolved_aspects):
            raise ValueError("BOUND requires complete parameters and no unresolved aspects")
        if self.state is OpeningBindingState.PARTIAL and (
                not self.resolved_aspects or not self.unresolved_aspects):
            raise ValueError("PARTIAL requires resolved and unresolved aspects")
        if self.state is OpeningBindingState.UNRESOLVED and (
                self.parameters or self.resolved_aspects or not self.unresolved_aspects):
            raise ValueError("UNRESOLVED cannot claim resolved values")
        if self.production_adopted is not False:
            raise ValueError("Phase 30L cannot activate production")

    def to_dict(self) -> dict:
        return {
            "binding_id": self.binding_id, "state": self.state.value,
            "parameters": [[key, value] for key, value in self.parameters],
            "resolved_aspects": list(self.resolved_aspects),
            "unresolved_aspects": list(self.unresolved_aspects),
            "provenance": list(self.provenance), "limitations": self.limitations,
            "current_authority": self.current_authority,
            "historical_authority": self.historical_authority,
            "supersedes_historical_scope": self.supersedes_historical_scope,
            "production_adopted": self.production_adopted,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class NisimNilyOpeningContractBinding:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    base_contract_version: str
    base_required_bindings: tuple[str, ...]
    base_ready_for_execution: bool
    bindings: tuple[OpeningContractBinding, ...]
    production_bidding_changed: bool = False
    production_adopted: bool = False
    binding_version: str = "30L.1"
    bound_count: int = field(init=False)
    partial_count: int = field(init=False)
    unresolved_count: int = field(init=False)
    all_required_bindings_resolved: bool = field(init=False)
    ready_for_shadow_execution: bool = field(init=False)
    ready_for_production: bool = field(init=False)
    recommended_next_phase: str = field(init=False)

    def __post_init__(self) -> None:
        if (self.profile_id, self.profile_version, self.base_system) != (
            NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
            SystemProfile.TWO_OVER_ONE_GF,
        ):
            raise ValueError("binding requires canonical Nisim–Nily identity")
        object.__setattr__(self, "base_contract_version",
                           _nonblank(self.base_contract_version, "base_contract_version"))
        object.__setattr__(self, "binding_version", _nonblank(self.binding_version, "binding_version"))
        if not isinstance(self.base_required_bindings, tuple):
            raise TypeError("base_required_bindings must be a tuple")
        if self.base_required_bindings != _EXPECTED_BINDINGS:
            raise ValueError("Phase 30K binding IDs changed unexpectedly")
        if not isinstance(self.bindings, tuple) or not all(
                isinstance(item, OpeningContractBinding) for item in self.bindings):
            raise TypeError("bindings must contain OpeningContractBinding")
        ids = [item.binding_id for item in self.bindings]
        if len(ids) != len(set(ids)) or set(ids) != set(self.base_required_bindings):
            raise ValueError("bindings must cover each Phase 30K requirement exactly once")
        bindings = tuple(sorted(self.bindings, key=lambda item: item.binding_id))
        object.__setattr__(self, "bindings", bindings)
        counts = Counter(item.state for item in bindings)
        object.__setattr__(self, "bound_count", counts[OpeningBindingState.BOUND])
        object.__setattr__(self, "partial_count", counts[OpeningBindingState.PARTIAL])
        object.__setattr__(self, "unresolved_count", counts[OpeningBindingState.UNRESOLVED])
        complete = all(item.state is OpeningBindingState.BOUND for item in bindings)
        object.__setattr__(self, "all_required_bindings_resolved", complete)
        shadow = complete and self.base_ready_for_execution
        object.__setattr__(self, "ready_for_shadow_execution", shadow)
        object.__setattr__(self, "ready_for_production", shadow and self.production_adopted)
        object.__setattr__(self, "recommended_next_phase",
                           "30M_NISIM_NILY_OPENING_SHADOW_ENGINE" if complete else
                           "30M_NISIM_NILY_OPENING_BINDING_GAP_AUDIT")
        if self.production_bidding_changed or self.production_adopted:
            raise ValueError("Phase 30L cannot claim production activation")

    def binding(self, binding_id: str) -> OpeningContractBinding | None:
        key = _nonblank(binding_id, "binding_id")
        return next((item for item in self.bindings if item.binding_id == key), None)

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id, "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "base_contract_version": self.base_contract_version,
            "base_required_bindings": list(self.base_required_bindings),
            "base_ready_for_execution": self.base_ready_for_execution,
            "bindings": [item.to_dict() for item in self.bindings],
            "bound_count": self.bound_count, "partial_count": self.partial_count,
            "unresolved_count": self.unresolved_count,
            "all_required_bindings_resolved": self.all_required_bindings_resolved,
            "ready_for_shadow_execution": self.ready_for_shadow_execution,
            "ready_for_production": self.ready_for_production,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "recommended_next_phase": self.recommended_next_phase,
            "binding_version": self.binding_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class NisimNilyOpeningBindingCapability:
    base_contract_loaded: bool
    partnership_identity_validated: bool
    binding_schema_ready: bool
    historical_supersession_traced: bool
    all_required_bindings_resolved: bool
    shadow_execution_ready: bool
    production_bidding_changed: bool = False
    production_adopted: bool = False
    version: str = "30L.1"

    def to_dict(self) -> dict:
        return {
            "base_contract_loaded": self.base_contract_loaded,
            "partnership_identity_validated": self.partnership_identity_validated,
            "binding_schema_ready": self.binding_schema_ready,
            "historical_supersession_traced": self.historical_supersession_traced,
            "all_required_bindings_resolved": self.all_required_bindings_resolved,
            "shadow_execution_ready": self.shadow_execution_ready,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "version": self.version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def capability_for_nisim_nily_opening_binding(
    binding: NisimNilyOpeningContractBinding,
) -> NisimNilyOpeningBindingCapability:
    if not isinstance(binding, NisimNilyOpeningContractBinding):
        raise TypeError("binding must be NisimNilyOpeningContractBinding")
    return NisimNilyOpeningBindingCapability(
        base_contract_loaded=bool(binding.base_contract_version),
        partnership_identity_validated=True,
        binding_schema_ready=tuple(item.binding_id for item in binding.bindings) == _EXPECTED_BINDINGS,
        historical_supersession_traced=all(
            binding.binding(key).supersedes_historical_scope
            and binding.binding(key).historical_authority == "PHASE29M"
            for key in ("one_level_strength_policy", "equal_minor_precedence")),
        all_required_bindings_resolved=binding.all_required_bindings_resolved,
        shadow_execution_ready=binding.ready_for_shadow_execution,
    )


def _binding(binding_id: str, state: OpeningBindingState,
             parameters: tuple[tuple[str, str | int | bool], ...],
             resolved: tuple[str, ...], unresolved: tuple[str, ...],
             section: str, limitations: str, *, historical: str | None = None,
             supersedes: bool = False) -> OpeningContractBinding:
    return OpeningContractBinding(
        binding_id, state, parameters, resolved, unresolved,
        (f"User-approved PHASE29S consolidation {section}",
         f"bridge/opening_policy_consolidation_audit.py#assess_opening_policy:{section}"),
        limitations, historical_authority=historical,
        supersedes_historical_scope=supersedes,
    )


def bind_nisim_nily_opening_contract(
    plan: CompiledProfilePlan,
    base_contract: TwoOverOneOpeningContract | None = None,
) -> NisimNilyOpeningContractBinding:
    """Record current approved values and explicit gaps for one partnership."""
    if not isinstance(plan, CompiledProfilePlan):
        raise TypeError("plan must be CompiledProfilePlan")
    if (plan.profile_id, plan.profile_version, plan.base_system) != (
        NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
        SystemProfile.TWO_OVER_ONE_GF,
    ):
        raise ValueError("requires the canonical Nisim–Nily compiled plan")
    for selection in NISIM_NILY_PROFILE.agreements:
        directive = plan.directive(selection.family)
        if directive is None or directive.effective_treatment_id != selection.treatment_id:
            raise ValueError("compiled plan lacks a canonical Nisim–Nily selection")
    if base_contract is None:
        base_contract = build_two_over_one_opening_contract()
    if not isinstance(base_contract, TwoOverOneOpeningContract):
        raise TypeError("base_contract must be TwoOverOneOpeningContract")
    if base_contract.base_system is not plan.base_system:
        raise ValueError("base contract system differs from compiled plan")
    if (len(base_contract.required_bindings) != len(_EXPECTED_BINDINGS)
            or base_contract.required_bindings != _EXPECTED_BINDINGS):
        raise ValueError("Phase 30K binding IDs changed unexpectedly")
    B, P = OpeningBindingState.BOUND, OpeningBindingState.PARTIAL
    bindings = (
        _binding("one_level_strength_policy", B,
                 (("normal_hcp_min", 12), ("rule20_min_score", 20),
                  ("rule20_can_establish_opening_strength", True),
                  ("failed_rule20_implies_pass", False)),
                 ("HCP >= 12 or Rule20 >= 20 establishes normal opening strength in every seat",),
                 (), "B", "Strength alone selects no suit, notrump, strong opening, or Pass.",
                 historical="PHASE29M", supersedes=True),
        _binding("minor_length_policy", P,
                 (("recognized_minor_candidate_lengths", "5,6"),),
                 ("Exact 5/6-card minor candidate shapes occur in approved natural-choice cases",),
                 ("No complete 3/4/5/6-card natural minor opening length contract",),
                 "C", "SAYC Better-Minor length defaults are not imported.", historical="PHASE29M"),
        _binding("minor_selection_precedence", P,
                 (("five_major_with_five_or_six_minor", "major"),
                  ("equal_five_or_six_minors", "1D")),
                 ("Eligible five-card major with five/six-card minor selects the major",
                  "Eligible equal 5/6-card minors select diamonds"),
                 ("Ordinary longer-minor and other minor-shape selection is unspecified",
                  "Six-card major plus five-card minor depends on unresolved concentration/quality"),
                 "C", "Known choices remain subject to strength and higher-priority opening branches."),
        _binding("equal_minor_precedence", P,
                 (("resolved_equal_lengths", "5,6"), ("preferred_call", "1D"),
                  ("requires_opening_eligibility", True)),
                 ("Eligible 5-5 and 6-6 minors select 1D under later Phase 29S rule",),
                 ("3-3 and 4-4 minor choices are only historical SAYC reference cases",
                  "No complete equal-minor selector across all shapes and higher-priority openings"),
                 "C", "29S supersedes 29M's unresolved 5-5/6-6 scope only; no universal Better Minor rule.",
                 historical="PHASE29M", supersedes=True),
        _binding("five_five_major_precedence", B,
                 (("spades_length", 5), ("hearts_length", 5),
                  ("preferred_call", "1S"), ("requires_opening_eligibility", True)),
                 ("Opening-eligible exact 5S-5H chooses 1S",), (), "C",
                 "Exact 5-5 only; the rule does not imply a 6-6 major choice.",
                 historical="PHASE29M"),
        _binding("one_notrump_range", B,
                 tuple((f"position_{position}_{edge}", value)
                       for position in (1, 2, 3, 4)
                       for edge, value in (("min", 15 if position <= 2 else 14),
                                           ("max", 17))),
                 ("Positions 1-2 use 15-17 HCP; positions 3-4 use 14-17 HCP",),
                 (), "D", "Range is positional; no vulnerability adjustment is approved."),
        _binding("one_notrump_five_card_major_policy", B,
                 (("five_card_major_allowed_in_canonical_balanced", True),
                  ("exactly_nine_major_cards_allowed", False)),
                 ("A five-card major can appear in the approved canonical balanced 1NT subset",
                  "Exactly nine total major cards excludes the current 1NT branch"),
                 (), "D", "No generalization to arbitrary 5-4 or six-card-major shapes."),
        _binding("one_notrump_shape_policy", P,
                 (("canonical_balanced_subset_accepted", True),),
                 ("Canonical balanced shapes within approved range are accepted",),
                 ("Broader 'all such shapes' interpretation is unresolved",
                  "Six-card-minor and other noncanonical balanced-like shapes lack typed approval"),
                 "D", "A draft convention-card note does not resolve broader shape scope."),
        _binding("suit_vs_notrump_precedence", P,
                 (("approved_canonical_1nt_precedes_ordinary_natural", True),
                  ("requires_strong_opening_negative", True)),
                 ("Approved canonical 1NT branch precedes ordinary natural one-level selection when strong branch is negative",),
                 ("Precedence for broader unresolved 1NT shapes is unknown",
                  "Unresolved strong-opening branch can block a final 1NT choice"),
                 "D/J", "No global NT-over-suit rule beyond the approved range/shape branch."),
        _binding("strong_hand_precedence", P,
                 (("strong_2c_hcp_route_min", 23),
                  ("exact_22_requires_approved_strong_suit", True)),
                 ("23+ HCP strong-2C route takes precedence",
                  "Exact 22-HCP approved strong-suit patterns take precedence",
                  "20-21 canonical balanced Multi/NT branch and 22-HCP strong priority are checked"),
                 ("Unlisted 22-HCP strong-suit patterns remain unknown",
                  "Playing-trick route has unapproved component values",
                  "Strong-2C versus strong-minor conflict remains unresolved",
                  "5422 balanced-like treatment and other strong boundaries remain unresolved"),
                 "H/I/J", "No SAYC 22+ strong-2C threshold or general playing-tricks formula is imported."),
    )
    return NisimNilyOpeningContractBinding(
        profile_id=plan.profile_id, profile_version=plan.profile_version,
        base_system=plan.base_system, base_contract_version=base_contract.contract_version,
        base_required_bindings=base_contract.required_bindings,
        base_ready_for_execution=base_contract.ready_for_execution,
        bindings=bindings,
    )
