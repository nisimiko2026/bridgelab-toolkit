"""B2.3 responder's second call, using only existing continuation routes."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .auction import Auction, Call, CallType
from .bidding_engine import BiddingEngineResult
from .bidding_rules import BiddingContext, RuleDecision, SystemContext
from .models import Hand, Vulnerability
from .partnership_profiles import (
    PartnershipProfile, ResolvedAgreement, ResolvedBiddingProfile,
    resolve_partnership_profile,
)
from .policy_registry import (
    JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION,
    STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION,
    PolicyRegistry,
)
from .profile_rule_support import response_system, top_priority_conflicts
from .sayc_route_configuration import create_standard_sayc_router


class ResponderRebidDisposition(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    ABSTAIN = "ABSTAIN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class ResponderRebidAssessment:
    profile: ResolvedBiddingProfile
    context: BiddingContext
    opening: str
    response: str
    opener_rebid: str
    route_id: str | None
    disposition: ResponderRebidDisposition
    selected: RuleDecision | None
    engine_result: BiddingEngineResult | None
    blockers: tuple[str, ...]
    reason: str
    production_adopted: bool = False

    def __post_init__(self) -> None:
        if self.production_adopted:
            raise ValueError("responder rebid consolidation is not production adopted")
        if (self.disposition is ResponderRebidDisposition.RECOMMENDED) != (self.selected is not None):
            raise ValueError("only a recommended assessment may select a rebid")
        if self.selected is not None and (not self.selected.applicable or self.blockers):
            raise ValueError("selected rebid requires applicable, unblocked evidence")

    @property
    def recommended_call(self) -> Call | None:
        return None if self.selected is None else self.selected.candidate


def _responder_second_call(auction: Auction) -> tuple[str, str, str]:
    if not isinstance(auction, Auction):
        raise TypeError("auction must be Auction")
    if auction.is_complete:
        raise ValueError("responder rebid requires a live auction")
    entries = auction.entries
    index = next((i for i, e in enumerate(entries) if e.call.kind is not CallType.PASS), None)
    if index is None or len(entries) != index + 6:
        raise ValueError("requires responder's second call only")
    opener, rho, responder, lho, rebid, rho_again = entries[index:]
    if (any(e.call.kind is not CallType.BID for e in (opener, responder, rebid))
            or responder.seat is not auction.next_seat
            or opener.seat is not auction.next_seat.partner()
            or rebid.seat is not opener.seat):
        raise ValueError("requires opening, partner's first bid, and opener's rebid")
    if any(e.call.kind is not CallType.PASS for e in (rho, lho, rho_again)):
        raise ValueError("competitive auctions are outside responder-rebid scope")
    return tuple(e.call.serialize() for e in (opener, responder, rebid))


def assess_responder_rebid(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
    registry: PolicyRegistry | None = None,
    jacoby_continuation_strength_policy_id: str | None = None,
    stayman_continuation_strength_policy_id: str | None = None,
) -> ResponderRebidAssessment:
    """Compose an uncontested responder rebid without filling missing meanings.

    Optional policy IDs select existing caller-supplied strength classifiers;
    no default classifier or numeric strength thresholds are supplied here.
    Unbound relevant opening/response/rebid agreements prohibit fallback, even
    when a policy ID is supplied. Prior calls remain visible auction evidence,
    not decisions reconstructed using hidden opener cards.
    """
    opening, response, opener_rebid = _responder_second_call(auction)
    resolved = resolve_partnership_profile(profile, base_agreements=base_agreements)
    system, blockers = response_system(
        profile, resolved, opening, None,
        extra_families=("rebid", "opener.rebid", "responder.rebid"),
    )
    options = dict(system.options)
    for name, option, policy_id in (
        ("jacoby_continuation_strength_policy_id", JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION,
         jacoby_continuation_strength_policy_id),
        ("stayman_continuation_strength_policy_id", STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION,
         stayman_continuation_strength_policy_id),
    ):
        if policy_id is not None:
            if not isinstance(policy_id, str) or not policy_id.strip():
                raise ValueError(f"{name} must be a nonblank string")
            options[option] = policy_id.strip()
    system = SystemContext.from_mapping(system.system, options)
    context = BiddingContext.create(hand=hand, auction=auction, vulnerability=vulnerability, system=system)
    route = create_standard_sayc_router(registry).match(context)

    def result(disposition, reason, *, selected=None, evidence=None, issues=()):
        return ResponderRebidAssessment(
            resolved, context, opening, response, opener_rebid,
            None if route is None else route.route_id, disposition, selected,
            evidence, tuple(issues), reason,
        )

    if blockers:
        return result(ResponderRebidDisposition.ABSTAIN,
                      "Relevant profile meaning is unbound; base fallback is prohibited.", issues=blockers)
    if route is None:
        return result(ResponderRebidDisposition.ABSTAIN,
                      "No existing responder-rebid route for this auction; no call or Pass inferred.",
                      issues=("No implemented responder-rebid route",))
    if not route.route_id.startswith("sayc.responder."):
        return result(ResponderRebidDisposition.ABSTAIN,
                      "Matched route is outside responder-rebid scope.",
                      issues=("Route outside responder-rebid scope",))
    evidence = route.engine.evaluate(context)
    if evidence.recommended is None:
        return result(ResponderRebidDisposition.ABSTAIN,
                      "Existing responder-rebid rules abstain; consult their complete decision trace.",
                      evidence=evidence, issues=("No applicable existing responder-rebid rule",))
    tied = top_priority_conflicts(evidence)
    if tied:
        return result(ResponderRebidDisposition.CONFLICT,
                      "Equal-priority responder-rebid rules disagree; no single call is justified.",
                      evidence=evidence, issues=tuple(item.rule_id for item in tied))
    return result(ResponderRebidDisposition.RECOMMENDED, evidence.recommended.explanation,
                  selected=evidence.recommended, evidence=evidence)
