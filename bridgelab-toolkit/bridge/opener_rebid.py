"""B2.2 opener's second call, composed solely from existing rebid routes."""
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
from .policy_registry import PolicyRegistry, STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION
from .profile_rule_support import response_system, top_priority_conflicts
from .sayc_route_configuration import create_standard_sayc_router


class OpenerRebidDisposition(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    ABSTAIN = "ABSTAIN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class OpenerRebidAssessment:
    profile: ResolvedBiddingProfile
    context: BiddingContext
    opening: str
    response: str
    route_id: str | None
    disposition: OpenerRebidDisposition
    selected: RuleDecision | None
    engine_result: BiddingEngineResult | None
    blockers: tuple[str, ...]
    reason: str
    production_adopted: bool = False

    def __post_init__(self) -> None:
        if self.production_adopted:
            raise ValueError("opener rebid consolidation is not production adopted")
        if (self.disposition is OpenerRebidDisposition.RECOMMENDED) != (self.selected is not None):
            raise ValueError("only a recommended assessment may select a rebid")
        if self.selected is not None and (not self.selected.applicable or self.blockers):
            raise ValueError("selected rebid requires applicable, unblocked evidence")

    @property
    def recommended_call(self) -> Call | None:
        return None if self.selected is None else self.selected.candidate


def _opener_second_call(auction: Auction) -> tuple[str, str]:
    if not isinstance(auction, Auction):
        raise TypeError("auction must be Auction")
    if auction.is_complete:
        raise ValueError("opener rebid requires a live auction")
    entries = auction.entries
    index = next((i for i, e in enumerate(entries) if e.call.kind is not CallType.PASS), None)
    if index is None or len(entries) != index + 4:
        raise ValueError("requires opener's second call only")
    opener, rho, responder, lho = entries[index:]
    if (opener.call.kind is not CallType.BID or responder.call.kind is not CallType.BID
            or opener.seat is not auction.next_seat
            or responder.seat is not auction.next_seat.partner()):
        raise ValueError("requires opening followed by partner's first bid")
    if rho.call.kind is not CallType.PASS or lho.call.kind is not CallType.PASS:
        raise ValueError("competitive auctions are outside opener-rebid scope")
    return opener.call.serialize(), responder.call.serialize()


def assess_opener_rebid(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
    registry: PolicyRegistry | None = None,
    stayman_dual_major_response_policy_id: str | None = None,
) -> OpenerRebidAssessment:
    """Assess an uncontested opener rebid without inventing missing meanings.

    Opening and response agreement bindings are shared with B2.1; unbound
    rebid/opener.rebid families also block fallback. The optional Stayman policy
    ID selects an existing caller-supplied policy, never a new default. The
    actual opening/response is accepted as auction evidence; we do not rerun
    opening rules or infer the hidden responder's hand to validate past calls.
    """
    opening, response = _opener_second_call(auction)
    resolved = resolve_partnership_profile(profile, base_agreements=base_agreements)
    system, blockers = response_system(profile, resolved, opening, None,
                                       extra_families=("rebid", "opener.rebid"))
    if stayman_dual_major_response_policy_id is not None:
        policy_id = stayman_dual_major_response_policy_id
        if not isinstance(policy_id, str) or not policy_id.strip():
            raise ValueError("stayman_dual_major_response_policy_id must be a nonblank string")
        system = SystemContext(system.system, system.options + (
            (STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION, policy_id.strip()),))
    context = BiddingContext.create(hand=hand, auction=auction, vulnerability=vulnerability, system=system)
    route = create_standard_sayc_router(registry).match(context)

    def result(disposition, reason, *, selected=None, evidence=None, issues=()):
        return OpenerRebidAssessment(resolved, context, opening, response,
            None if route is None else route.route_id, disposition, selected,
            evidence, tuple(issues), reason)

    if blockers:
        return result(OpenerRebidDisposition.ABSTAIN,
                      "Relevant profile meaning is unbound; base fallback is prohibited.", issues=blockers)
    if route is None:
        return result(OpenerRebidDisposition.ABSTAIN,
                      "No existing opener-rebid route for this auction; no call or Pass inferred.",
                      issues=("No implemented opener-rebid route",))
    if not route.route_id.startswith(("sayc.opener.", "sayc.2over1.opener.")):
        return result(OpenerRebidDisposition.ABSTAIN,
                      "Matched route is outside opener-rebid scope.", issues=("Route outside opener-rebid scope",))
    evidence = route.engine.evaluate(context)
    if evidence.recommended is None:
        return result(OpenerRebidDisposition.ABSTAIN,
                      "Existing opener-rebid rules abstain; consult their complete decision trace.",
                      evidence=evidence, issues=("No applicable existing opener-rebid rule",))
    tied = top_priority_conflicts(evidence)
    if tied:
        return result(OpenerRebidDisposition.CONFLICT,
                      "Equal-priority opener-rebid rules disagree; no single call is justified.",
                      evidence=evidence, issues=tuple(item.rule_id for item in tied))
    return result(OpenerRebidDisposition.RECOMMENDED, evidence.recommended.explanation,
                  selected=evidence.recommended, evidence=evidence)