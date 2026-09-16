"""Approved Phase 29M partnership knowledge, not a production bidding rule.

Approval provenance is the user's Phase 29M specification, sections D-L.
No router, system profile, source-authority registry or bidding decision is changed.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum

from .evaluation import evaluate_hand
from .models import Hand


class OpeningPolicyAuthority(str, Enum):
    AUTHORITATIVE_REPOSITORY_SOURCE = "AUTHORITATIVE_REPOSITORY_SOURCE"
    NISIM_NILY_PARTNERSHIP_POLICY = "NISIM_NILY_PARTNERSHIP_POLICY"
    SUPPORTED_REFERENCE = "SUPPORTED_REFERENCE"
    SOURCE_INSUFFICIENT = "SOURCE_INSUFFICIENT"
    UNRESOLVED = "UNRESOLVED"


class OpeningPolicyStatus(str, Enum):
    APPROVED = "APPROVED"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNRESOLVED = "UNRESOLVED"
    PROHIBITED = "PROHIBITED"
    INCOMPLETE = "INCOMPLETE"


class _Serializable:
    __slots__ = ()

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class RuleOf20Assessment(_Serializable):
    hcp: int
    longest_suit_length: int
    second_longest_suit_length: int
    score: int
    qualifies: bool
    intended_11_hcp_use: bool
    authority: OpeningPolicyAuthority = OpeningPolicyAuthority.NISIM_NILY_PARTNERSHIP_POLICY
    selects_opening_call: bool = False
    failure_implies_pass: bool = False


def assess_rule_of_20(hand: Hand) -> RuleOf20Assessment:
    """Calculate the approved strength screen only, using canonical hand facts.

The arithmetic can be inspected for any hand. Only 11-HCP borderline use is
approved here; a qualifying <=10 hand gains no general opening entitlement.
12+ normal strength does not depend on this score. Seat/exception integration
and opening-family applicability remain separate from this calculation.
"""
    facts = evaluate_hand(hand)
    longest, second = sorted(facts.suit_lengths, reverse=True)[:2]
    score = facts.hcp + longest + second
    return RuleOf20Assessment(facts.hcp, longest, second, score, score >= 20, facts.hcp == 11)


@dataclass(frozen=True, slots=True)
class OpeningPolicyProposition(_Serializable):
    policy_id: str
    authority: OpeningPolicyAuthority
    status: OpeningPolicyStatus
    condition: str
    policy: str
    provenance: tuple[str, ...]
    limitations: str
    normal_opening_strength: bool = False
    requires_rule20: bool = False
    preferred_call: str | None = None
    production_adopted: bool = False


@dataclass(frozen=True, slots=True)
class OpeningSafetyExclusion(_Serializable):
    exclusion_id: str
    domain: str
    provenance: tuple[str, ...]
    authority: OpeningPolicyAuthority = OpeningPolicyAuthority.NISIM_NILY_PARTNERSHIP_POLICY
    status: OpeningPolicyStatus = OpeningPolicyStatus.UNRESOLVED
    exclude_from_future_pass: bool = True
    unresolved_disposition: str = "UNKNOWN / ABSTAIN"
    implies_pass: bool = False


@dataclass(frozen=True, slots=True)
class NisimNilyOpeningPolicy(_Serializable):
    policy_id: str
    version: str
    approval_provenance: str
    propositions: tuple[OpeningPolicyProposition, ...]
    safety_exclusions: tuple[OpeningSafetyExclusion, ...]
    unresolved_domains: tuple[str, ...]
    rule20_definition: str = "HCP + longest_suit_length + second_longest_suit_length >= 20"
    rule20_primary_hcp: int = 11
    rule20_authority: OpeningPolicyAuthority = OpeningPolicyAuthority.NISIM_NILY_PARTNERSHIP_POLICY
    rule22_status: OpeningPolicyStatus = OpeningPolicyStatus.REFERENCE_ONLY
    equal_five_card_majors_choice: str = "1S"
    equal_major_choice_requires_opening_eligibility: bool = True
    invariant: str = "PASS != FALLBACK_FOR_ABSTAIN"
    failure_to_open_is_evidence_to_pass: bool = False
    abstain_to_pass_allowed: bool = False
    unknown_to_pass_allowed: bool = False
    registry_complement_is_pass: bool = False
    positive_pass_status: OpeningPolicyStatus = OpeningPolicyStatus.INCOMPLETE
    production_integration: bool = False


def build_nisim_nily_opening_policy() -> NisimNilyOpeningPolicy:
    """Return approved declarative policy; do not apply it to production decisions."""
    partnership = OpeningPolicyAuthority.NISIM_NILY_PARTNERSHIP_POLICY
    reference = OpeningPolicyAuthority.SUPPORTED_REFERENCE
    approved = OpeningPolicyStatus.APPROVED
    user = "User-approved PHASE 29M"
    prior = "bridge/opening_pass_source_policy_audit.py"
    family_guard = (
        "Strength or suit preference alone selects no actual bid. Preserve sourced family, "
        "shape, length, balanced, strong-opening, preempt and unresolved-boundary requirements."
    )
    propositions = (
        OpeningPolicyProposition("strength-13-plus", partnership, approved, "HCP >= 13",
            "Normally opening strength; use existing sourced opening families for actual recommendations.",
            (user + " D1",), family_guard, normal_opening_strength=True),
        OpeningPolicyProposition("strength-12", partnership, approved, "HCP == 12",
            "Normally opening strength; Rule20 is not a universal gate; no arbitrary opening bid.",
            (user + " D2",), family_guard, normal_opening_strength=True),
        OpeningPolicyProposition("strength-11", partnership, approved, "HCP == 11 and Rule20Score >= 20",
            "May have sufficient partnership opening strength; not an opening-call selector.",
            (user + " D3/E", "knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md"),
            family_guard + " Failing the screen does not imply Pass.", requires_rule20=True),
        OpeningPolicyProposition("strength-10-or-less", partnership, approved, "HCP <= 10",
            "No general new opening entitlement. Existing covered weak/preempt recommendations remain unchanged; "
            "ordinary unsupported hands are only conditional future Pass candidates.",
            (user + " D4",), "A future positive Pass predicate and every safety exclusion are still required; "
            "exceptional or distributional uncertainty remains UNKNOWN / ABSTAIN."),
        OpeningPolicyProposition("rule20", partnership, approved, "Borderline strength, primarily 11 HCP",
            "HCP + lengths of two longest suits >=20 qualifies the strength screen.",
            (user + " E",), "Not universal SAYC. Not a universal 12-HCP gate. No call choice or failed-screen Pass."),
        OpeningPolicyProposition("rule22", reference, OpeningPolicyStatus.REFERENCE_ONLY, "Repository Rule22 guidance",
            "Not production-adopted, not mandatory partnership opening requirement, not Pass policy.",
            (user + " F", "knowledge/bidding/principles/bidding-fundamentals/rule-of-22.md"),
            "No quick-trick requirement is added to approved Rule20."),
        OpeningPolicyProposition("equal-five-card-majors", partnership, approved, "Spades == 5 and hearts == 5",
            "5S-5H => 1S; supersedes the provisional 1H reference suggestion for this partnership.",
            (user + " G",), family_guard + " Exactly 5-5 only; no extension to 6-6; not universal SAYC.",
            preferred_call="1S"),
        OpeningPolicyProposition("five-major-five-minor", partnership, approved, "One five-card major and one five-card minor",
            "Prefer the five-card major where consistent with existing sourced opening rules.",
            (user + " H", "bridge/sayc.py"), family_guard),
        OpeningPolicyProposition("equal-minors-3-3", reference, OpeningPolicyStatus.REFERENCE_ONLY, "Clubs == 3 and diamonds == 3",
            "Existing sourced Better Minor selects 1C subject to current strength/major/NT/strong gates.",
            (user + " I", "knowledge/bidding/systems/sayc.md#Better Minor", "bridge/sayc.py"),
            "Canonical production reference is not authenticated external authority.", preferred_call="1C", production_adopted=True),
        OpeningPolicyProposition("equal-minors-4-4", reference, OpeningPolicyStatus.REFERENCE_ONLY, "Clubs == 4 and diamonds == 4",
            "Existing sourced Better Minor selects 1D subject to current strength/major/NT/strong gates.",
            (user + " I", "knowledge/bidding/systems/sayc.md#Better Minor", "bridge/sayc.py"),
            "No new universal equal-minor selector.", preferred_call="1D", production_adopted=True),
        OpeningPolicyProposition("equal-minors-5-5", OpeningPolicyAuthority.UNRESOLVED, OpeningPolicyStatus.UNRESOLVED,
            "Clubs == 5 and diamonds == 5", "UNRESOLVED; not Pass.", (user + " I", prior), "No approved selector."),
        OpeningPolicyProposition("other-equal-minors", OpeningPolicyAuthority.UNRESOLVED, OpeningPolicyStatus.UNRESOLVED,
            "Equal minors outside 3-3/4-4/5-5", "No universal selector; 6-6 remains unresolved.",
            (user + " I", prior), "Equal <=2 entails a five-card major in a 13-card hand; family gates still apply; not an independent minor-gap claim."),
        OpeningPolicyProposition("pass-fallback-prohibition", partnership, OpeningPolicyStatus.PROHIBITED,
            "ABSTAIN, UNKNOWN or no opening rule matched", "Never convert these outcomes to Pass or define Pass as registry complement.",
            (user + " L/X",), "Future Pass requires positive strength/domain conditions, exclusions, provenance and explanation."),
        OpeningPolicyProposition("positive-pass", OpeningPolicyAuthority.SOURCE_INSUFFICIENT, OpeningPolicyStatus.INCOMPLETE,
            "Future positive Opening Pass predicate", "Not yet defined by these approvals.",
            (user + " D4/L", prior), "Normal strength and protected exclusions alone do not specify a positive Pass domain."),
    )
    exclusions = (
        OpeningSafetyExclusion("equal-minors", "Equal 5-5/6-6 minors and other unsupported minor selectors", (user + " I", prior)),
        OpeningSafetyExclusion("strong-2c-playing-tricks", "Below-22-HCP strong-2C playing-trick eligibility not fully formalized", (user + " J", prior)),
        OpeningSafetyExclusion("weak-two-preempt", "Multiple/competing long suits; 6-6 weak-two qualifiers; 7-6 weak-two/preempt overlaps; strength or distributional exceptions", (user + " K", prior)),
        OpeningSafetyExclusion("long-suit-variants", "Uncovered six clubs, six-card preempt exceptions, eight-plus/four-level and generic 5-HCP preempt variants", (user + " D4/K", prior)),
        OpeningSafetyExclusion("equal-majors-6-6", "6S-6H is outside the exact 5S-5H approval", (user + " G", prior)),
        OpeningSafetyExclusion("unimplemented-approved-openings", "Exact 5-5 majors and 11-HCP Rule20 strength may now have approved policy but remain production coverage boundaries", (user + " D3/G",)),
        OpeningSafetyExclusion("context-and-evaluation", "Unspecified seat/vulnerability exceptions, optional NT adjustments and unresolved opening-family applicability", (user + " D1/D2/L", prior)),
    )
    return NisimNilyOpeningPolicy(
        "nisim-nily.opening-policy", "29M.1", user + " sections D-L; explicit partnership approval, not universal SAYC",
        propositions, exclusions, tuple(e.exclusion_id for e in exclusions) + ("positive-pass-domain",),
    )
