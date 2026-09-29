"""Phase 29U integration of the Nisim–Nily exact-six-minor policy.

B1.3 consolidation of Phase 29S evidence, Phase 29T and Phase 30N decisions.
Historical assessment semantics are retained; no production route is registered.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .auction import Auction
from .models import Hand, Suit, Vulnerability
from .evaluation import evaluate_hand
from .partnership_profiles import PartnershipProfile
from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .nisim_nily_opening_decision_contract import (
    NisimNilyOpeningDecisionContract, build_nisim_nily_opening_decision_contract,
)
from .nisim_nily_six_minor_preempt_policy import (
    SixMinorDecision,
    SixMinorPreemptAssessment,
    assess_six_minor_three_level_preempt,
)
from .opening_policy_consolidation_audit import (
    Assessment,
    FAMILIES,
    State,
    Classification,
    assess_opening_policy,
)


class _Serializable:
    __slots__ = ()

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True, slots=True)
class IntegratedOpeningAssessment(_Serializable):
    base: Assessment
    six_minor: SixMinorPreemptAssessment
    classification: Classification
    supported_call: str | None
    resolved_blockers: tuple[str, ...]
    unresolved_blockers: tuple[str, ...]
    integration_applied: bool
    reason: str
    production_adopted: bool = False
    policy_version: str = "nisim-nily.opening-policy-six-minor@B1.3"
    selected_family: str | None = None
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.production_adopted:
            raise ValueError("opening consolidation is not production adopted")
        if self.classification is Classification.UNRESOLVED and self.supported_call is not None:
            raise ValueError("unresolved policy cannot select a call")
        if self.classification is Classification.PASS_SUPPORTED and self.supported_call != "P":
            raise ValueError("Pass classification requires P")
        if self.supported_call == "P" and self.classification is not Classification.PASS_SUPPORTED:
            raise ValueError("P requires affirmative Pass classification")


_SIX_MINOR_RESOLVED_BLOCKERS = frozenset(
    ("preempt", "later_seat", "individual_review")
)


def assess_opening_policy_with_six_minor(
    hand: Hand,
    *,
    auction: Auction,
    vulnerability: Vulnerability,
    profile: PartnershipProfile = NISIM_NILY_PROFILE,
    decisions: NisimNilyOpeningDecisionContract | None = None,
) -> IntegratedOpeningAssessment:
    """Select one partnership opening, or explicitly retain unresolved evidence.

    Historical 29S family evidence remains available in ``base``. The canonical
    30N contract supplies later approved precedence/shape/denomination choices.
    Ordinary one-level eligibility excludes the approved 1NT and strong Multi
    meanings; Rule20 never demotes those meanings to an ordinary minor opening.
    """
    if not isinstance(hand, Hand):
        raise TypeError("canonical Hand required")
    if not isinstance(profile, PartnershipProfile):
        raise TypeError("canonical PartnershipProfile required")
    if profile != NISIM_NILY_PROFILE:
        raise ValueError("only the canonical Nisim–Nily partnership is supported")
    contract = build_nisim_nily_opening_decision_contract()
    if decisions is not None:
        if not isinstance(decisions, NisimNilyOpeningDecisionContract):
            raise TypeError("typed opening decision contract required")
        if decisions != contract:
            raise ValueError("contradictory or unsupported opening decision contract")
    if not isinstance(auction, Auction):
        raise TypeError("canonical Auction required")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("canonical Vulnerability required")

    base = assess_opening_policy(
        hand,
        auction=auction,
        vulnerability=vulnerability,
    )
    six_minor = assess_six_minor_three_level_preempt(
        hand,
        seat=auction.next_seat,
        vulnerability=vulnerability,
        opening_position=len(auction.calls) + 1,
    )

    facts = evaluate_hand(hand)
    checks = {check.family: check for check in base.checks}
    if len(checks) != len(base.checks) or set(checks) != set(FAMILIES):
        raise ValueError("complete unique opening family evidence required")
    fixed_calls = {"strong_2c": "2C", "one_nt": "1NT",
                   "multi_minor": "2D", "multi_nt": "2D", "multi_weak": "2D"}
    for check in base.checks:
        if check.call is not None and check.state is not State.POSITIVE:
            raise ValueError("contradictory opening family state and call")
        if check.family in fixed_calls and check.state is State.POSITIVE:
            if check.call != fixed_calls[check.family]:
                raise ValueError("contradictory opening family and call")
    expected = {SixMinorDecision.ONE_LEVEL: ("1C", "1D"),
                SixMinorDecision.THREE_LEVEL: ("3C", "3D")}
    if six_minor.decision in expected:
        if (six_minor.preferred_call not in expected[six_minor.decision]
                or six_minor.minor not in ("C", "D")
                or not six_minor.preferred_call.endswith(six_minor.minor)) :
            raise ValueError("contradictory six-minor decision and call")
    elif six_minor.preferred_call is not None:
        raise ValueError("nonqualifying six-minor policy cannot select a call")

    def result(classification, call, family, reason, provenance, blockers=(), applied=True):
        return IntegratedOpeningAssessment(
            base, six_minor, classification, call,
            tuple(x for x in base.unresolved_blockers if x not in blockers) if applied and call is not None else (),
            tuple(blockers), applied, reason,
            selected_family=family, provenance=tuple(provenance),
        )

    def unknown(blockers, reason):
        return result(Classification.UNRESOLVED, None, None, reason,
                      (contract.approval_provenance,), blockers)

    strong = checks["strong_2c"]
    if strong.state is State.POSITIVE:
        return result(Classification.OPENING_SUPPORTED, "2C", "strong_2c",
                      strong.reason + " Strong 2C precedes every lower opening family.",
                      (strong.provenance, contract.approval_provenance))
    if strong.state is State.UNKNOWN:
        return unknown(("strong_2c",), "Strong 2C qualification is unresolved; no lower call selected.")

    # Preserve already approved strong Multi meanings, not weak-opening rules.
    for family in ("multi_minor", "multi_nt"):
        check = checks[family]
        if check.state is State.POSITIVE:
            return result(Classification.PARTNERSHIP_TREATMENT_SUPPORTED, "2D", family,
                          check.reason, (check.provenance,))
    ambiguous_strong = tuple(f for f in ("multi_minor", "multi_nt")
                             if checks[f].state is State.UNKNOWN)
    if ambiguous_strong:
        return unknown(ambiguous_strong, "Strong Multi qualification remains unresolved.")

    s, h, d, c = facts.suit_lengths
    nt_range = 15 <= facts.hcp <= 17 or (facts.hcp == 14 and base.opening_position >= 3)
    nt_shape = facts.distribution in contract.one_notrump_allowed_shapes
    if facts.distribution == (5, 4, 2, 2) and min(s, h) >= 4:
        nt_shape = False
    if facts.distribution == (6, 3, 2, 2) and max(d, c) != 6:
        nt_shape = False
    if nt_range and nt_shape and s + h != 9:
        return result(Classification.OPENING_SUPPORTED, "1NT", "one_nt",
                      "Approved positional range and Phase 30N shape; 1NT precedes ordinary one-level.",
                      (checks["one_nt"].provenance, contract.approval_provenance))

    normal = checks["natural_strength"].state is State.POSITIVE
    if normal:
        if max(s, h) >= 5:
            call = "1S" if s >= h else "1H"
        elif d >= contract.minor_diamond_minimum or c >= contract.minor_club_minimum:
            call = ("1D" if d > c else "1C" if c > d else
                    getattr(contract, f"equal_minor_{d}_{c}_call", None))
        else:
            call = None
        if call is None:
            return unknown(("natural_choice",), "Opening strength established; no approved denomination.")
        return result(Classification.OPENING_SUPPORTED, call, "one_level",
                      f"HCP={facts.hcp}; core Rule20={facts.rule_of_20.score}; approved ordinary suit choice before weak/preempt treatments.",
                      (checks["natural_strength"].provenance, contract.approval_provenance))

    # These partnership exceptions are subordinate to the approved openings
    # above. Use exact core shape/HCP/honor facts; do not extrapolate conditions.
    shape_provenance = ("User B1.3 completion: previously approved Nisim–Nily shape exceptions",)
    if facts.distribution == (4, 4, 4, 1) and facts.hcp == 11:
        singleton = next(item for item in facts.suit_honor_evidence if item.length == 1)
        # Zero HCP in an exact singleton means its rank is below Jack (T allowed).
        if singleton.hcp == 0:
            return result(Classification.OPENING_SUPPORTED, "1D" if d == 4 else "1C",
                          "4441_low_singleton",
                          "Exact 4441, 11 HCP and singleton below Jack: four diamonds select 1D, otherwise 1C.",
                          shape_provenance)

    if facts.distribution == (4, 3, 3, 3):
        spades = facts.honor_evidence(Suit.SPADES)
        spade_quality = (spades.has_ace or spades.has_king
                         or (spades.has_queen and spades.has_jack and spades.has_ten))
        if s == 4 and base.opening_position in (3, 4) and spade_quality:
            return result(Classification.OPENING_SUPPORTED, "1C", "4333_spade_exception",
                          "Exact 4333 with four spades in third/fourth seat and at least K or QJT in spades: 1C.",
                          shape_provenance)
        return result(Classification.PASS_SUPPORTED, "P", "4333_pass",
                      "Exact 4333 below higher-priority openings: four-spade, seat or spade-quality exception not met; approved Pass.",
                      shape_provenance)

    if s == h == 5 and facts.hcp <= 9:
        return result(Classification.PASS_SUPPORTED, "P", "five_five_major_pass",
                      "Explicit B1.3 invariant: exact five-five majors with at most nine HCP pass.",
                      ("User B1.3: 5-5 majors <=9 HCP remains Pass",))

    if six_minor.decision is SixMinorDecision.THREE_LEVEL:
        remaining = tuple(x for x in base.unresolved_blockers
                          if x not in _SIX_MINOR_RESOLVED_BLOCKERS)
        if remaining:
            return unknown(remaining, "Six-minor preempt qualifies but independent blockers remain.")
        return result(Classification.PARTNERSHIP_TREATMENT_SUPPORTED,
                      six_minor.preferred_call, "six_minor_preempt", six_minor.reason,
                      (six_minor.policy_version,))

    # Missing agreements never become Pass. Historical evidence stays inspectable.
    family = "pass" if base.classification is Classification.PASS_SUPPORTED else None
    return result(base.classification, base.supported_call, family, base.reason,
                  tuple(check.provenance for check in base.checks), base.unresolved_blockers,
                  six_minor.decision is not SixMinorDecision.NOT_APPLICABLE)
