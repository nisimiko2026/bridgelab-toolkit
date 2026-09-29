"""B2.1 first-response composition of existing routes, never new bidding rules.

The partnership resolver owns agreement precedence. The existing router and
rule registries own all hand predicates, sources and call meanings. This
opt-in assessment is not wired into production or any rebid path.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .auction import Auction, Call, CallType
from .bidding_engine import BiddingEngineResult
from .bidding_rules import BiddingContext, RuleDecision
from .models import Hand, Vulnerability
from .partnership_profiles import (
    PartnershipProfile, ResolvedAgreement,
    ResolvedBiddingProfile, resolve_partnership_profile,
)
from .policy_registry import PolicyRegistry
from .profile_rule_support import response_system as _response_system, top_priority_conflicts
from .sayc_route_configuration import create_standard_sayc_router


class FirstResponseDisposition(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    ABSTAIN = "ABSTAIN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class FirstResponseAssessment:
    profile: ResolvedBiddingProfile
    context: BiddingContext
    opening: str
    route_id: str | None
    disposition: FirstResponseDisposition
    selected: RuleDecision | None
    engine_result: BiddingEngineResult | None
    blockers: tuple[str, ...]
    reason: str
    production_adopted: bool = False

    def __post_init__(self) -> None:
        if self.production_adopted:
            raise ValueError("first-response consolidation is not production adopted")
        if (self.disposition is FirstResponseDisposition.RECOMMENDED) != (self.selected is not None):
            raise ValueError("only a recommended assessment may select a response")
        if self.selected is not None and (not self.selected.applicable or self.blockers):
            raise ValueError("selected response requires applicable, unblocked evidence")

    @property
    def recommended_call(self) -> Call | None:
        """The single selected response; engine alternatives are evidence only."""
        return None if self.selected is None else self.selected.candidate


def _first_opening(auction: Auction) -> str:
    if not isinstance(auction, Auction):
        raise TypeError("auction must be Auction")
    if auction.is_complete:
        raise ValueError("first response requires a live auction")
    entries = auction.entries
    index = next((i for i, entry in enumerate(entries)
                  if entry.call.kind is not CallType.PASS), None)
    if (index is None or entries[index].call.kind is not CallType.BID
            or len(entries) != index + 2
            or entries[index].seat is not auction.next_seat.partner()):
        raise ValueError("requires responder's first call after partner's opening; no rebids")
    return entries[index].call.serialize()


def assess_first_response(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
    registry: PolicyRegistry | None = None, suit_quality_policy_id: str | None = None,
) -> FirstResponseAssessment:
    """Resolve a profile and assess only an existing first-response route.

    Base defaults must be supplied explicitly as SYSTEM-scope agreements, as in
    the existing resolver. No system-name substitution, passed-hand normalization
    or missing-convention fallback is permitted. An explicit quality-policy ID
    selects a caller-supplied existing policy; there is no default quality test.
    Unbound relevant treatments/parameters block fallback, retaining their full
    metadata in ``profile``. Other families are unaffected.
    """
    opening = _first_opening(auction)
    resolved = resolve_partnership_profile(profile, base_agreements=base_agreements)
    system, blockers = _response_system(profile, resolved, opening, suit_quality_policy_id)
    context = BiddingContext.create(hand=hand, auction=auction, vulnerability=vulnerability, system=system)
    router = create_standard_sayc_router(registry)
    route = router.match(context)

    def result(disposition, reason, *, selected=None, evidence=None, issues=()):
        return FirstResponseAssessment(resolved, context, opening,
            None if route is None else route.route_id, disposition, selected,
            evidence, tuple(issues), reason)

    if blockers:
        return result(FirstResponseDisposition.ABSTAIN,
                      "Relevant profile meaning is unbound; base fallback is prohibited.", issues=blockers)
    if route is None:
        return result(FirstResponseDisposition.ABSTAIN,
                      "No existing response route for this auction; no call or Pass inferred.",
                      issues=("No implemented first-response route",))
    if not route.route_id.startswith("sayc.response."):
        return result(FirstResponseDisposition.ABSTAIN,
                      "Matched route is not a first-response route.", issues=("Route outside first-response scope",))
    evidence = route.engine.evaluate(context)
    if evidence.recommended is None:
        return result(FirstResponseDisposition.ABSTAIN,
                      "Existing response rules abstain; consult their complete decision trace.",
                      evidence=evidence, issues=("No applicable existing response rule",))

    # Engine priority is authoritative, but registration order alone must not
    # conceal equally ranked contradictory calls. Preserve all trace evidence.
    tied = top_priority_conflicts(evidence)
    if tied:
        return result(FirstResponseDisposition.CONFLICT,
                      "Equal-priority response rules disagree; no single call is justified.",
                      evidence=evidence, issues=tuple(item.rule_id for item in tied))
    return result(FirstResponseDisposition.RECOMMENDED, evidence.recommended.explanation,
                  selected=evidence.recommended, evidence=evidence)