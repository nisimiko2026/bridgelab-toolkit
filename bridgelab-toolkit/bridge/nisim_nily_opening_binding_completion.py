"""Phase 30O declarative completion above the unchanged Phase 30L binding."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace
import json

from .nisim_nily_opening_binding_gap_audit import (
    OpeningBindingGapDisposition, audit_nisim_nily_opening_binding_gaps,
)
from .nisim_nily_opening_contract_binding import (
    NisimNilyOpeningContractBinding, OpeningBindingState,
    OpeningContractBinding, bind_nisim_nily_opening_contract,
)
from .nisim_nily_opening_decision_contract import (
    NisimNilyOpeningDecisionContract, build_nisim_nily_opening_decision_contract,
)
from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .partnership_profiles import resolve_partnership_profile
from .profile_compiler import compile_profile_plan
from .system_profiles import SystemProfile
from .two_over_one_opening_contract import build_two_over_one_opening_contract


# Each of these 30M requests is answered by a typed Phase 30N field. An
# unexpected new decision gap stays open instead of receiving blanket approval.
_APPROVED_DECISION_GAPS = frozenset((
    "minor_length.ordinary_club_minimum", "minor_length.ordinary_diamond_minimum",
    "minor_length.longer_minor", "minor_selection.unequal_minors",
    "equal_minors.3_3", "equal_minors.4_4",
    "minor_selection.major6_minor5", "one_nt_shape.six_card_minor",
    "one_nt_shape.other_broader_shapes", "strong.22_unlisted_strong_suit",
    "strong.strong_minor_overlap",
))
_RESOLVED_DEPENDENCIES = frozenset((
    "suit_vs_nt.broader_nt_shapes", "suit_vs_nt.strong_opening_interaction",
))
_EXECUTION_ONLY_DEPENDENCIES = frozenset(("strong.playing_trick_route",))


@dataclass(frozen=True, slots=True)
class NisimNilyCompletedOpeningBinding:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    base_contract_version: str
    phase30l_binding_version: str
    decision_contract_version: str
    base_ready_for_execution: bool
    bindings: tuple[OpeningContractBinding, ...]
    remaining_decision_gap_ids: tuple[str, ...]
    remaining_dependency_gap_ids: tuple[str, ...]
    remaining_dependencies: tuple[str, ...]
    production_bidding_changed: bool = False
    production_adopted: bool = False
    completion_version: str = "30O.1"
    bound_count: int = field(init=False)
    partial_count: int = field(init=False)
    unresolved_count: int = field(init=False)
    all_required_bindings_resolved: bool = field(init=False)
    declarative_contract_complete: bool = field(init=False)
    ready_for_shadow_execution: bool = field(init=False)
    ready_for_production: bool = field(init=False)
    recommended_next_phase: str = field(init=False)

    def __post_init__(self) -> None:
        if (self.profile_id, self.profile_version, self.base_system) != (
            NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
            SystemProfile.TWO_OVER_ONE_GF,
        ):
            raise ValueError("completion requires canonical Nisim–Nily identity")
        if (self.base_contract_version, self.phase30l_binding_version,
            self.decision_contract_version, self.completion_version) != (
            "30K.1", "30L.1", "30N.1", "30O.1",
        ):
            raise ValueError("completion source version changed")
        if not isinstance(self.bindings, tuple) or not all(
            isinstance(x, OpeningContractBinding) for x in self.bindings
        ):
            raise TypeError("bindings must contain OpeningContractBinding")
        ids = [x.binding_id for x in self.bindings]
        required = build_two_over_one_opening_contract().required_bindings
        if len(ids) != len(required) or len(set(ids)) != len(required) or set(ids) != set(required):
            raise ValueError("completion must cover every Phase 30K binding exactly once")
        for name in ("remaining_decision_gap_ids", "remaining_dependency_gap_ids",
                     "remaining_dependencies"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or len(values) != len(set(values)):
                raise ValueError(f"{name} must be a unique tuple")
            object.__setattr__(self, name, tuple(sorted(values)))
        bindings = tuple(sorted(self.bindings, key=lambda x: x.binding_id))
        object.__setattr__(self, "bindings", bindings)
        counts = Counter(x.state for x in bindings)
        object.__setattr__(self, "bound_count", counts[OpeningBindingState.BOUND])
        object.__setattr__(self, "partial_count", counts[OpeningBindingState.PARTIAL])
        object.__setattr__(self, "unresolved_count", counts[OpeningBindingState.UNRESOLVED])
        all_bound = self.bound_count == len(bindings)
        object.__setattr__(self, "all_required_bindings_resolved", all_bound)
        complete = all_bound and not self.remaining_decision_gap_ids
        object.__setattr__(self, "declarative_contract_complete", complete)
        shadow = complete and not self.remaining_dependencies and self.base_ready_for_execution
        object.__setattr__(self, "ready_for_shadow_execution", shadow)
        object.__setattr__(self, "ready_for_production", shadow and self.production_adopted)
        next_phase = (
            "30P_NISIM_NILY_OPENING_DECISION_COMPLETION"
            if self.remaining_decision_gap_ids else
            "30P_NISIM_NILY_OPENING_EXECUTION_DEPENDENCY_COMPLETION"
            if self.remaining_dependencies or not self.base_ready_for_execution or not complete else
            "30P_NISIM_NILY_OPENING_SHADOW_ENGINE"
        )
        object.__setattr__(self, "recommended_next_phase", next_phase)
        if self.production_bidding_changed or self.production_adopted:
            raise ValueError("Phase 30O cannot activate production")

    def binding(self, binding_id: str) -> OpeningContractBinding | None:
        return next((x for x in self.bindings if x.binding_id == binding_id), None)

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id, "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "base_contract_version": self.base_contract_version,
            "phase30l_binding_version": self.phase30l_binding_version,
            "decision_contract_version": self.decision_contract_version,
            "base_ready_for_execution": self.base_ready_for_execution,
            "bindings": [x.to_dict() for x in self.bindings],
            "remaining_decision_gap_ids": list(self.remaining_decision_gap_ids),
            "remaining_dependency_gap_ids": list(self.remaining_dependency_gap_ids),
            "remaining_dependencies": list(self.remaining_dependencies),
            "bound_count": self.bound_count, "partial_count": self.partial_count,
            "unresolved_count": self.unresolved_count,
            "all_required_bindings_resolved": self.all_required_bindings_resolved,
            "declarative_contract_complete": self.declarative_contract_complete,
            "ready_for_shadow_execution": self.ready_for_shadow_execution,
            "ready_for_production": self.ready_for_production,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "recommended_next_phase": self.recommended_next_phase,
            "completion_version": self.completion_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))


def _additions(decisions: NisimNilyOpeningDecisionContract) -> dict[str, tuple]:
    """Binding parameters, newly resolved scope, and remaining limitations."""
    shape_text = ",".join("".join(str(n) for n in shape)
                          for shape in decisions.one_notrump_allowed_shapes)
    return {
        "minor_length_policy": (
            (("club_minimum", decisions.minor_club_minimum),
             ("diamond_minimum", decisions.minor_diamond_minimum),
             ("unequal_minor_rule", decisions.unequal_minor_rule),
             ("exact_six_minor_rule20_preserved", decisions.exact_six_minor_rule20_preserved)),
            "Ordinary 1C/1D require three cards; unequal minors use the longer minor.",
            "Higher-priority strong, 1NT and major openings still take precedence."),
        "minor_selection_precedence": (
            (("unequal_minors", decisions.unequal_minor_rule),
             ("six_major_five_minor", decisions.six_major_five_minor_call_family),
             ("exact_six_minor_rule20_preserved", decisions.exact_six_minor_rule20_preserved)),
            "Eligible 6-major plus 5-minor selects the major; otherwise ordinary unequal minors select the longer minor.",
            "Strong openings, approved 1NT and approved major branches precede ordinary minor choice."),
        "equal_minor_precedence": (
            (("equal_3_3", decisions.equal_minor_3_3_call),
             ("equal_4_4", decisions.equal_minor_4_4_call),
             ("equal_5_5", decisions.equal_minor_5_5_call),
             ("equal_6_6", decisions.equal_minor_6_6_call)),
            "Equal 3-3 chooses 1C; equal 4-4, 5-5 and 6-6 choose 1D when eligible.",
            "Only the listed equal lengths are decided; higher-priority openings still apply."),
        "one_notrump_shape_policy": (
            (("allowed_sorted_shapes", shape_text),
             ("excluded_sorted_shapes", "5431,6331"),
             ("five_card_major_allowed", decisions.one_notrump_five_card_major_allowed),
             ("shape_5422_excludes_two_majors", decisions.one_notrump_5422_both_majors_excluded),
             ("shape_6322_requires_six_card_minor", decisions.one_notrump_6322_six_suit_must_be_minor),
             ("exact_nine_major_cards_excluded", decisions.one_notrump_exact_nine_major_cards_excluded)),
            "Approved 5422 excludes five-plus-four in the majors; approved 6322 requires the six-card suit to be C or D.",
            "No other semi-balanced or six-card-suit shape is inferred; positional HCP ranges remain separate."),
        "suit_vs_notrump_precedence": (
            (("approved_1nt_precedes_ordinary_one_level",
              decisions.approved_one_notrump_precedes_ordinary_one_level),
             ("strong_2c_precedes_1nt", decisions.strong_two_club_precedes_one_notrump),
             ("strong_2c_over_strong_minor",
              decisions.strong_two_club_vs_strong_minor_precedence)),
            "The now-typed approved 1NT shape/range branch precedes ordinary one-level suits, after strong-opening priority.",
            "Precedence applies only when the relevant opening predicates are positively established."),
        "strong_hand_precedence": (
            (("strong_2c_hcp_route_min", decisions.strong_two_club_routes[0].hcp_min),
             ("exact_22_suit_minimum", decisions.strong_two_club_routes[1].suit_minimum),
             ("exact_22_honor_patterns", ",".join(decisions.strong_two_club_routes[1].qualifying_honor_patterns)),
             ("route3_hcp_range", "17-21"),
             ("route3_closed_suit", "AKQxxx+"),
             ("route3_max_other_suit_length", decisions.strong_two_club_routes[2].maximum_other_suit_length),
             ("route3_min_playing_tricks", "8.5"),
             ("strong_2c_over_strong_minor",
              decisions.strong_two_club_vs_strong_minor_precedence)),
            "Approved 2C routes precede lower openings; 2C wins a positive strong-minor Multi overlap.",
            "Playing-trick components not approved in 29S remain an external execution dependency; no new values are inferred."),
    }


def complete_nisim_nily_opening_binding(
    binding: NisimNilyOpeningContractBinding | None = None,
    decisions: NisimNilyOpeningDecisionContract | None = None,
) -> NisimNilyCompletedOpeningBinding:
    """Apply exact approved decisions without mutating Phase 30L or 30M."""
    if binding is None:
        plan = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
        binding = bind_nisim_nily_opening_contract(plan)
    if not isinstance(binding, NisimNilyOpeningContractBinding):
        raise TypeError("binding must be NisimNilyOpeningContractBinding")
    audit = audit_nisim_nily_opening_binding_gaps(binding)
    if decisions is None:
        decisions = build_nisim_nily_opening_decision_contract()
    if not isinstance(decisions, NisimNilyOpeningDecisionContract):
        raise TypeError("decisions must be NisimNilyOpeningDecisionContract")
    if decisions.to_json() != build_nisim_nily_opening_decision_contract().to_json():
        raise ValueError("Phase 30N approved decisions changed unexpectedly")
    D = OpeningBindingGapDisposition
    decision_gaps = {g.gap_id for g in audit.gaps
                     if g.disposition is D.PARTNERSHIP_DECISION_REQUIRED}
    if decision_gaps != _APPROVED_DECISION_GAPS:
        raise ValueError("Phase 30M partnership decision gaps changed unexpectedly")
    dependency_gaps = {g.gap_id: g for g in audit.gaps if g.disposition is D.DEPENDENCY_REQUIRED}
    if set(dependency_gaps) != _RESOLVED_DEPENDENCIES | _EXECUTION_ONLY_DEPENDENCIES:
        raise ValueError("Phase 30M dependency gaps changed unexpectedly")
    additions = _additions(decisions)
    completed = []
    for item in binding.bindings:
        if item.binding_id not in audit.partial_binding_ids:
            completed.append(item)
            continue
        new_params, new_aspect, limitations = additions[item.binding_id]
        parameters = tuple((key, value) for key, value in item.parameters if key not in {
            name for name, _ in new_params}) + tuple(new_params)
        completed.append(replace(
            item, state=OpeningBindingState.BOUND, parameters=parameters,
            resolved_aspects=item.resolved_aspects + (new_aspect,),
            unresolved_aspects=(), limitations=limitations,
            provenance=item.provenance + (
                "User-approved Phase 30N Nisim–Nily partnership decision",),
            current_authority="PHASE30N",
        ))
    execution_gap_ids = tuple(sorted(_EXECUTION_ONLY_DEPENDENCIES))
    return NisimNilyCompletedOpeningBinding(
        binding.profile_id, binding.profile_version, binding.base_system,
        binding.base_contract_version, binding.binding_version,
        decisions.decision_version, binding.base_ready_for_execution,
        tuple(completed), (), execution_gap_ids,
        tuple(dependency_gaps[gap_id].dependency for gap_id in execution_gap_ids),
    )
