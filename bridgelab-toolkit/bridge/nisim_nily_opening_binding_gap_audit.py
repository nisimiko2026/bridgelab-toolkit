"""Phase 30M declarative audit of the six partial Nisim–Nily bindings.

This records approved evidence and unanswered questions. It does not evaluate
hands, choose openings, or register any production bidding behavior.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from .nisim_nily_opening_contract_binding import (
    NisimNilyOpeningContractBinding, OpeningBindingState,
    bind_nisim_nily_opening_contract,
)
from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .partnership_profiles import resolve_partnership_profile
from .profile_compiler import compile_profile_plan
from .system_profiles import SystemProfile


class OpeningBindingGapDisposition(str, Enum):
    COVERED_BY_APPROVED_EVIDENCE = "COVERED_BY_APPROVED_EVIDENCE"
    PARTNERSHIP_DECISION_REQUIRED = "PARTNERSHIP_DECISION_REQUIRED"
    DEPENDENCY_REQUIRED = "DEPENDENCY_REQUIRED"
    OUTSIDE_CURRENT_SCOPE = "OUTSIDE_CURRENT_SCOPE"


_PARTIAL_IDS = (
    "equal_minor_precedence", "minor_length_policy", "minor_selection_precedence",
    "one_notrump_shape_policy", "strong_hand_precedence", "suit_vs_notrump_precedence",
)

# Fingerprint of the committed Phase 30L.1 canonical serialization. An
# unversioned change to its evidence must be re-audited, not silently accepted.
_EXPECTED_30L_SHA256 = "1b480d498dc11e11d36d7b31265aacb57944cf6bc18da2732d3de8c0bea83868"


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")
    return value.strip()


def _optional(value: str | None, name: str) -> str | None:
    return None if value is None else _nonblank(value, name)


def _strings(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    normalized = tuple(sorted(_nonblank(value, name) for value in values))
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"duplicate {name}")
    return normalized


def _json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class OpeningBindingGap:
    gap_id: str
    binding_id: str
    disposition: OpeningBindingGapDisposition
    question: str
    known_rule: str | None
    missing_decision: str | None
    dependency: str | None
    provenance: tuple[str, ...]
    limitations: str
    requires_user_decision: bool
    production_adopted: bool = False

    def __post_init__(self) -> None:
        for name in ("gap_id", "binding_id", "question", "limitations"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        for name in ("known_rule", "missing_decision", "dependency"):
            object.__setattr__(self, name, _optional(getattr(self, name), name))
        object.__setattr__(self, "provenance", _strings(self.provenance, "provenance"))
        if not self.provenance or not isinstance(self.disposition, OpeningBindingGapDisposition):
            raise ValueError("gap needs approved provenance and a disposition")
        D = OpeningBindingGapDisposition
        expected = self.disposition is D.PARTNERSHIP_DECISION_REQUIRED
        if self.requires_user_decision is not expected:
            raise ValueError("user-decision flag must follow disposition")
        if self.disposition is D.COVERED_BY_APPROVED_EVIDENCE and (
            self.known_rule is None or self.missing_decision or self.dependency
        ):
            raise ValueError("covered gap requires only a known rule")
        if self.disposition is D.PARTNERSHIP_DECISION_REQUIRED and (
            self.missing_decision is None or self.dependency
        ):
            raise ValueError("decision gap requires an explicit missing choice")
        if self.disposition is D.DEPENDENCY_REQUIRED and (
            self.dependency is None or self.missing_decision
        ):
            raise ValueError("dependency gap requires an exact dependency")
        if self.production_adopted:
            raise ValueError("Phase 30M cannot activate production")

    def to_dict(self) -> dict:
        return {
            "gap_id": self.gap_id, "binding_id": self.binding_id,
            "disposition": self.disposition.value, "question": self.question,
            "known_rule": self.known_rule, "missing_decision": self.missing_decision,
            "dependency": self.dependency, "provenance": list(self.provenance),
            "limitations": self.limitations,
            "requires_user_decision": self.requires_user_decision,
            "production_adopted": self.production_adopted,
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True, slots=True)
class OpeningPartnershipDecisionRequest:
    decision_id: str
    binding_ids: tuple[str, ...]
    gap_ids: tuple[str, ...]
    question: str
    already_known: str
    must_not_infer: str
    existing_behavior_untouched: str
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("decision_id", "question", "already_known", "must_not_infer",
                     "existing_behavior_untouched"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        for name in ("binding_ids", "gap_ids", "provenance"):
            object.__setattr__(self, name, _strings(getattr(self, name), name))
            if not getattr(self, name):
                raise ValueError(f"{name} cannot be empty")

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id, "binding_ids": list(self.binding_ids),
            "gap_ids": list(self.gap_ids), "question": self.question,
            "already_known": self.already_known, "must_not_infer": self.must_not_infer,
            "existing_behavior_untouched": self.existing_behavior_untouched,
            "provenance": list(self.provenance),
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True, slots=True)
class NisimNilyOpeningBindingGapAudit:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    binding_version: str
    base_contract_version: str
    partial_binding_ids: tuple[str, ...]
    gaps: tuple[OpeningBindingGap, ...]
    decision_requests: tuple[OpeningPartnershipDecisionRequest, ...]
    production_bidding_changed: bool = False
    production_adopted: bool = False
    audit_version: str = "30M.1"
    covered_count: int = field(init=False)
    decision_required_count: int = field(init=False)
    dependency_required_count: int = field(init=False)
    outside_scope_count: int = field(init=False)
    bindings_fully_resolved_by_existing_evidence: tuple[str, ...] = field(init=False)
    remaining_partial_bindings: tuple[str, ...] = field(init=False)
    requires_user_decisions: bool = field(init=False)
    decision_request_ids: tuple[str, ...] = field(init=False)
    ready_for_shadow_execution: bool = field(init=False)
    ready_for_production: bool = field(init=False)
    recommended_next_phase: str = field(init=False)

    def __post_init__(self) -> None:
        if (self.profile_id, self.profile_version, self.base_system) != (
            NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
            SystemProfile.TWO_OVER_ONE_GF,
        ):
            raise ValueError("audit requires canonical Nisim–Nily identity")
        for name in ("binding_version", "base_contract_version", "audit_version"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        if self.partial_binding_ids != _PARTIAL_IDS:
            raise ValueError("Phase 30L partial binding IDs changed unexpectedly")
        if not isinstance(self.gaps, tuple) or not all(isinstance(g, OpeningBindingGap) for g in self.gaps):
            raise TypeError("gaps must contain OpeningBindingGap")
        if not isinstance(self.decision_requests, tuple) or not all(
            isinstance(r, OpeningPartnershipDecisionRequest) for r in self.decision_requests
        ):
            raise TypeError("decision_requests must contain OpeningPartnershipDecisionRequest")
        ids = [g.gap_id for g in self.gaps]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate gap ID")
        if {g.binding_id for g in self.gaps} != set(_PARTIAL_IDS):
            raise ValueError("gaps must cover exactly the six partial bindings")
        gaps = tuple(sorted(self.gaps, key=lambda g: g.gap_id))
        requests = tuple(sorted(self.decision_requests, key=lambda r: r.decision_id))
        object.__setattr__(self, "gaps", gaps)
        object.__setattr__(self, "decision_requests", requests)
        decision_ids = [r.decision_id for r in requests]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("duplicate decision request ID")
        decision_gaps = {g.gap_id for g in gaps if g.requires_user_decision}
        request_gaps = [gap_id for r in requests for gap_id in r.gap_ids]
        if len(request_gaps) != len(set(request_gaps)) or set(request_gaps) != decision_gaps:
            raise ValueError("decision requests must cover decision gaps exactly once")
        by_id = {g.gap_id: g for g in gaps}
        for request in requests:
            if request.binding_ids != tuple(sorted({by_id[g].binding_id for g in request.gap_ids})):
                raise ValueError("decision request binding IDs do not match gaps")
        counts = Counter(g.disposition for g in gaps)
        D = OpeningBindingGapDisposition
        for name, state in (("covered_count", D.COVERED_BY_APPROVED_EVIDENCE),
                            ("decision_required_count", D.PARTNERSHIP_DECISION_REQUIRED),
                            ("dependency_required_count", D.DEPENDENCY_REQUIRED),
                            ("outside_scope_count", D.OUTSIDE_CURRENT_SCOPE)):
            object.__setattr__(self, name, counts[state])
        fully = tuple(binding_id for binding_id in _PARTIAL_IDS if all(
            g.disposition is D.COVERED_BY_APPROVED_EVIDENCE
            for g in gaps if g.binding_id == binding_id
        ))
        object.__setattr__(self, "bindings_fully_resolved_by_existing_evidence", fully)
        object.__setattr__(self, "remaining_partial_bindings",
                           tuple(x for x in _PARTIAL_IDS if x not in fully))
        object.__setattr__(self, "requires_user_decisions", bool(decision_gaps))
        object.__setattr__(self, "decision_request_ids", tuple(decision_ids))
        object.__setattr__(self, "ready_for_shadow_execution", False)
        object.__setattr__(self, "ready_for_production", False)
        next_phase = (
            "30N_NISIM_NILY_OPENING_DECISION_PACKET" if decision_gaps else
            "30N_NISIM_NILY_OPENING_DEPENDENCY_COMPLETION" if counts[D.DEPENDENCY_REQUIRED] else
            "30N_NISIM_NILY_OPENING_BINDING_COMPLETION"
        )
        object.__setattr__(self, "recommended_next_phase", next_phase)
        if self.production_bidding_changed or self.production_adopted:
            raise ValueError("Phase 30M cannot claim production activation")

    def gap(self, gap_id: str) -> OpeningBindingGap | None:
        key = _nonblank(gap_id, "gap_id")
        return next((g for g in self.gaps if g.gap_id == key), None)

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id, "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "binding_version": self.binding_version,
            "base_contract_version": self.base_contract_version,
            "partial_binding_ids": list(self.partial_binding_ids),
            "gaps": [g.to_dict() for g in self.gaps],
            "decision_requests": [r.to_dict() for r in self.decision_requests],
            "covered_count": self.covered_count,
            "decision_required_count": self.decision_required_count,
            "dependency_required_count": self.dependency_required_count,
            "outside_scope_count": self.outside_scope_count,
            "bindings_fully_resolved_by_existing_evidence": list(
                self.bindings_fully_resolved_by_existing_evidence),
            "remaining_partial_bindings": list(self.remaining_partial_bindings),
            "requires_user_decisions": self.requires_user_decisions,
            "decision_request_ids": list(self.decision_request_ids),
            "ready_for_shadow_execution": self.ready_for_shadow_execution,
            "ready_for_production": self.ready_for_production,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "recommended_next_phase": self.recommended_next_phase,
            "audit_version": self.audit_version,
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


def _gap(gap_id: str, binding_id: str, disposition: OpeningBindingGapDisposition,
         question: str, *, known: str | None = None, missing: str | None = None,
         dependency: str | None = None, source: str = "PHASE29S:C",
         limitations: str = "Applies only to the explicitly stated subset.") -> OpeningBindingGap:
    return OpeningBindingGap(
        gap_id, binding_id, disposition, question, known, missing, dependency,
        (f"User-approved {source}", f"bridge/nisim_nily_opening_contract_binding.py#{binding_id}"),
        limitations,
        disposition is OpeningBindingGapDisposition.PARTNERSHIP_DECISION_REQUIRED,
    )


def _current_gaps() -> tuple[OpeningBindingGap, ...]:
    D = OpeningBindingGapDisposition
    C, P, R = D.COVERED_BY_APPROVED_EVIDENCE, D.PARTNERSHIP_DECISION_REQUIRED, D.DEPENDENCY_REQUIRED
    return (
        _gap("minor_length.ordinary_club_minimum", "minor_length_policy", P,
             "What minimum club length permits an ordinary 1C opening?",
             missing="Approve a partnership-wide ordinary 1C minimum.",
             limitations="Generic 2/1 'usually 3+' and SAYC Better Minor are not Nisim–Nily authority."),
        _gap("minor_length.ordinary_diamond_minimum", "minor_length_policy", P,
             "What minimum diamond length permits an ordinary 1D opening?",
             missing="Approve a partnership-wide ordinary 1D minimum.",
             limitations="No minimum is inferred from historical SAYC reference behavior."),
        _gap("minor_length.longer_minor", "minor_length_policy", P,
             "When must the longer minor be opened in ordinary shapes?",
             known="Exact equal 5/6-minor and isolated six-minor cases have their own rules.",
             missing="Approve the ordinary unequal-minor length rule and exceptions."),
        _gap("minor_length.six_card_minor_rule20", "minor_length_policy", C,
             "Does an eligible exact-six-card minor meeting Rule20 use the one-level minor?",
             known="29T/29U: one exact six-card minor, no other 5+ suit, and Rule20 qualification returns 1C/1D rather than a three-level preempt.",
             source="PHASE29T/29U:Rule20 six-minor priority",
             limitations="Only the exact 29T/29U structural subset; no general 1C/1D minimum."),
        _gap("minor_selection.major_vs_minor_5_5", "minor_selection_precedence", C,
             "Which suit is selected with an eligible five-card major and five-card minor?",
             known="29S chooses the five-card major, subject to higher-priority openings."),
        _gap("minor_selection.major_vs_minor_5_6", "minor_selection_precedence", C,
             "Which suit is selected with an eligible five-card major and six-card minor?",
             known="29S chooses the five-card major, subject to higher-priority openings."),
        _gap("minor_selection.major6_minor5", "minor_selection_precedence", P,
             "How is an eligible six-card major with five-card minor selected?",
             missing="Approve the concentration/quality boundary and final choice.",
             limitations="29S explicitly marks this boundary unknown; do not extrapolate 5-major logic."),
        _gap("minor_selection.unequal_minors", "minor_selection_precedence", P,
             "How are ordinary unequal-length minors selected?",
             missing="Approve a complete ordinary minor selector and its exceptions.",
             limitations="Known exact cases do not establish a general Better-Minor rule."),
        _gap("minor_selection.rule20_six_minor", "minor_selection_precedence", C,
             "Does the exact six-card-minor Rule20 branch select its own minor?",
             known="29T/29U select 1C or 1D for the sole exact six-card minor when Rule20 qualifies and no other suit is 5+.",
             source="PHASE29T/29U:Rule20 six-minor priority"),
        _gap("equal_minors.3_3", "equal_minor_precedence", P,
             "Which minor is selected with ordinary equal 3-3 minors?",
             missing="Approve the Nisim–Nily 3-3 choice.", source="PHASE29S:C; PHASE29M reference-only",
             limitations="Historical SAYC 3-3 reference is not partnership approval."),
        _gap("equal_minors.4_4", "equal_minor_precedence", P,
             "Which minor is selected with ordinary equal 4-4 minors?",
             missing="Approve the Nisim–Nily 4-4 choice.", source="PHASE29S:C; PHASE29M reference-only",
             limitations="Historical SAYC 4-4 reference is not partnership approval."),
        _gap("equal_minors.5_5", "equal_minor_precedence", C,
             "Which minor is selected with eligible equal 5-5 minors?",
             known="Later 29S explicitly chooses 1D when opening-eligible.",
             source="PHASE29S:C supersedes PHASE29M unresolved 5-5"),
        _gap("equal_minors.6_6", "equal_minor_precedence", C,
             "Which minor is selected with eligible equal 6-6 minors?",
             known="Later 29S explicitly chooses 1D when opening-eligible.",
             source="PHASE29S:C"),
        *(_gap(f"one_nt_shape.canonical_{shape}", "one_notrump_shape_policy", C,
               f"Is canonical {shape} balanced shape accepted for 1NT?",
               known=f"29S accepts canonical {shape} when the positional HCP range applies and exactly nine major cards are absent.",
               source="PHASE29S:D; bridge/evaluation.py canonical balanced distributions")
          for shape in ("4333", "4432", "5332")),
        _gap("one_nt_shape.five_card_major", "one_notrump_shape_policy", C,
             "Can a five-card major occur in the approved canonical 1NT subset?",
             known="29S permits a five-card major inside the canonical balanced subset and positional range.",
             source="PHASE29S:D"),
        _gap("one_nt_shape.exact_nine_major_cards", "one_notrump_shape_policy", C,
             "Does exactly nine total major cards qualify for the 1NT branch?",
             known="29S explicitly excludes exactly nine major cards from its 1NT branch.",
             source="PHASE29S:D", limitations="Negative rule only; not a universal shape prohibition."),
        _gap("one_nt_shape.six_card_minor", "one_notrump_shape_policy", P,
             "May a six-card-minor shape open 1NT, and under what exact conditions?",
             missing="Approve the exact six-card-minor 1NT shapes and exclusions.",
             source="PHASE29S:D", limitations="Draft convention-card language supplies no typed approval."),
        _gap("one_nt_shape.other_broader_shapes", "one_notrump_shape_policy", P,
             "Which other noncanonical or semi-balanced shapes, if any, qualify for 1NT?",
             missing="Approve each additional shape class and relevant exclusions.",
             source="PHASE29S:D", limitations="Do not infer all balanced-like or 5422 shapes."),
        _gap("suit_vs_nt.canonical_nt_vs_one_level", "suit_vs_notrump_precedence", C,
             "Does approved canonical 1NT precede an ordinary natural one-level suit?",
             known="29S selects approved 1NT over the ordinary suit when the strong-opening check is negative.",
             source="PHASE29S:D/J"),
        _gap("suit_vs_nt.five_card_major_nt", "suit_vs_notrump_precedence", C,
             "Does that precedence include approved canonical five-card-major 1NT?",
             known="29S selects the approved canonical five-card-major 1NT subset over ordinary natural selection when strong is negative.",
             source="PHASE29S:D/J"),
        _gap("suit_vs_nt.broader_nt_shapes", "suit_vs_notrump_precedence", R,
             "What is precedence when a broader 1NT shape is proposed?",
             dependency="Complete one_notrump_shape_policy for noncanonical and six-card-minor shapes.",
             source="PHASE29S:D/J"),
        _gap("suit_vs_nt.strong_opening_interaction", "suit_vs_notrump_precedence", R,
             "What is precedence if the strong-opening check is not negative?",
             dependency="Complete strong_hand_precedence and its 22-HCP/playing-trick boundaries.",
             source="PHASE29S:J"),
        _gap("strong.23_plus", "strong_hand_precedence", C,
             "Does the approved 23+ HCP Strong-2C route precede one-level/1NT?",
             known="29S route 1 selects 2C at 23+ HCP before one-level/1NT.", source="PHASE29S:J"),
        _gap("strong.22_approved_strong_suit", "strong_hand_precedence", C,
             "Do approved exact-22 HCP strong-suit patterns take priority?",
             known="29S positive 5+ suit patterns AK, AQ, KQ, or KJT select 2C at exact 22 HCP.",
             source="PHASE29S:J"),
        _gap("strong.22_unlisted_strong_suit", "strong_hand_precedence", P,
             "Which unlisted exact-22 HCP strong-suit patterns, if any, qualify for 2C?",
             missing="Approve the disposition of patterns currently reported UNKNOWN.",
             source="PHASE29S:J", limitations="Do not import SAYC's general 22+ rule."),
        _gap("strong.playing_trick_route", "strong_hand_precedence", R,
             "Can the playing-trick route be completed for currently unvalued holdings?",
             dependency="A complete typed playing-trick component table beyond approved 29S J values.",
             source="PHASE29S:J", limitations="Unknown components are not zero and receive no invented values."),
        _gap("strong.route3_closed_suit", "strong_hand_precedence", C,
             "Is the exact closed-suit Route 3 subset already computable?",
             known="29S checks 17–21 HCP, a 6+ AKQ closed suit, side suits shorter than four, all playing-trick components known, and total at least 8.5; that positive subset selects 2C absent strong-minor conflict.",
             source="PHASE29S:J", limitations="Other long suits and unvalued components remain unknown."),
        _gap("strong.strong_minor_overlap", "strong_hand_precedence", P,
             "Which opening takes priority when positive Strong-2C and strong-minor Multi overlap?",
             missing="Approve the 2C versus 2D priority for the overlapping positive subset.",
             source="PHASE29S:H/J", limitations="29S explicitly leaves this conflict unresolved."),
        _gap("strong.balanced_20_22_interaction", "strong_hand_precedence", C,
             "What exact 20–22 HCP canonical balanced interaction is already known?",
             known="29S sends canonical balanced 20–21 HCP to Multi 2D; at 22 HCP a positive strong-suit check takes 2C priority, a negative check permits Multi 2D, and UNKNOWN stays unresolved.",
             source="PHASE29S:I/J", limitations="Does not approve 5422 or generic SAYC 2NT/2C."),
    )


_DECISION_GROUPS = (
    ("MINOR_STRUCTURE", ("minor_length.ordinary_club_minimum", "minor_length.ordinary_diamond_minimum",
                          "minor_length.longer_minor", "minor_selection.unequal_minors",
                          "equal_minors.3_3", "equal_minors.4_4"),
     "What ordinary 1C/1D minimum lengths and unequal/equal 3-3 or 4-4 minor-selection rules does Nisim–Nily approve?",
     "Eligible equal 5-5/6-6 minors choose 1D; the exact Rule20 six-minor subset chooses its minor.",
     "Do not infer SAYC Better Minor, generic 2/1 'usually 3+', or historical 29M reference cases.",
     "Keep approved equal 5-5/6-6 and exact-six-minor Rule20 outcomes intact."),
    ("MAJOR_MINOR_PRECEDENCE", ("minor_selection.major6_minor5",),
     "How should an eligible six-card major with a five-card minor be chosen, including concentration and quality?",
     "An eligible five-card major with a five- or six-card minor chooses the major.",
     "Do not extend that five-major rule to six-major/five-minor hands.",
     "Keep approved five-major cases and higher-priority opening branches intact."),
    ("NOTRUMP_SHAPES", ("one_nt_shape.six_card_minor", "one_nt_shape.other_broader_shapes"),
     "Which exact six-card-minor or other noncanonical shapes, if any, may open 1NT?",
     "Canonical 4333/4432/5332 within the positional range are accepted; five-card majors may occur there, while exactly nine major cards are excluded.",
     "Do not infer permission from draft convention-card language, semi-balanced labels, or SAYC.",
     "Keep the approved canonical 1NT range, shape subset, and precedence intact."),
    ("STRONG_OPENING_PRECEDENCE", ("strong.22_unlisted_strong_suit", "strong.strong_minor_overlap"),
     "Which unlisted exact-22 strong-suit patterns qualify for 2C, and which call has priority if Strong-2C and strong-minor Multi both qualify?",
     "The 23+ HCP route and named exact-22 patterns are positive; exact 20–21 canonical balanced Multi is approved.",
     "Do not import a generic SAYC 22+ threshold or assign unknown playing-trick components.",
     "Keep the approved positive 2C routes and canonical balanced Multi decisions intact."),
)


def audit_nisim_nily_opening_binding_gaps(
    binding: NisimNilyOpeningContractBinding | None = None,
) -> NisimNilyOpeningBindingGapAudit:
    """Decompose the current six partial bindings without changing their states."""
    canonical = bind_nisim_nily_opening_contract(
        compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE)))
    if (canonical.binding_version != "30L.1"
            or canonical.base_contract_version != "30K.1"
            or hashlib.sha256(canonical.to_json().encode("utf-8")).hexdigest()
            != _EXPECTED_30L_SHA256):
        raise ValueError("Phase 30L canonical binding evidence changed unexpectedly")
    if binding is None:
        binding = canonical
    if not isinstance(binding, NisimNilyOpeningContractBinding):
        raise TypeError("binding must be NisimNilyOpeningContractBinding")
    partial = tuple(sorted(item.binding_id for item in binding.bindings
                           if item.state is OpeningBindingState.PARTIAL))
    if partial != _PARTIAL_IDS:
        raise ValueError("Phase 30L partial binding IDs changed unexpectedly")
    if binding.to_json() != canonical.to_json():
        raise ValueError("Phase 30L binding evidence changed unexpectedly")
    gaps = _current_gaps()
    by_id = {gap.gap_id: gap for gap in gaps}
    requests = tuple(OpeningPartnershipDecisionRequest(
        decision_id, tuple(sorted({by_id[x].binding_id for x in gap_ids})), gap_ids,
        question, known, not_infer, untouched,
        tuple(sorted({source for x in gap_ids for source in by_id[x].provenance})),
    ) for decision_id, gap_ids, question, known, not_infer, untouched in _DECISION_GROUPS)
    return NisimNilyOpeningBindingGapAudit(
        binding.profile_id, binding.profile_version, binding.base_system,
        binding.binding_version, binding.base_contract_version, partial, gaps, requests,
    )
