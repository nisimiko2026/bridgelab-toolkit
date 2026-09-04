"""Controlled SAYC Weak Jump Overcalls.

Frozen SAYC source: modern jump overcalls are preemptive and show a six-card
suit, approximately 6–10 HCP, and an offensive hand. The qualitative
``offensive hand`` requirement is delegated to an explicit OffensiveHandPolicy.
"""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Bid, Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit
from .offensive_hand_policy import OffensiveHandStatus
from .policy_registry import PolicyRegistry, assess_configured_offensive_hand

_SOURCE=KnowledgeSource("bidding/systems/sayc","Weak Jump Overcalls")

def legal_direct_jump_overcall_suits(context:BiddingContext)->tuple[tuple[Suit,int],...]:
    """Return mechanically legal suit jumps after one opponent one-level suit opening."""
    if len(context.auction.calls)!=1: return ()
    opening=context.auction.calls[0]
    if opening.kind is not CallType.BID or opening.bid is None or opening.bid.level!=1:
        return ()
    if opening.bid.strain is Strain.NOTRUMP: return ()
    out=[]
    for suit in Suit:
        # cheapest legal bid in suit
        cheapest=None
        for level in range(1,5):
            c=Call.from_bid(Bid(level,Strain(int(suit))))
            if context.auction.is_legal(c):
                cheapest=level; break
        if cheapest is None: continue
        jump=cheapest+1
        if jump<=7 and context.auction.is_legal(Call.from_bid(Bid(jump,Strain(int(suit))))):
            out.append((suit,jump))
    return tuple(out)

@dataclass(frozen=True,slots=True)
class SaycWeakJumpOvercallRule:
    registry:PolicyRegistry
    rule_id:str="sayc.overcall.weak_jump"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        if context.system.system.strip().casefold()!="sayc":
            return RuleDecision.not_applicable(self.rule_id,"Rule is SAYC-only.")
        candidates=legal_direct_jump_overcall_suits(context)
        if not candidates:
            return RuleDecision.not_applicable(self.rule_id,"Not a supported direct jump-overcall position.")
        hcp=context.evaluation.hcp
        if not 6<=hcp<=10:
            return RuleDecision.not_applicable(self.rule_id,"Weak Jump Overcall source range is approximately 6–10 HCP.")
        six=[(s,l) for s,l in candidates if context.hand.length(s)==6]
        if not six:
            return RuleDecision.not_applicable(self.rule_id,"No legal jump suit has the source-required six-card length.")
        if len(six)!=1:
            return RuleDecision.not_applicable(self.rule_id,"Multiple six-card jump suits qualify; frozen source supplies no selector.")
        offense=assess_configured_offensive_hand(context,self.registry)
        if offense is None or offense.status is OffensiveHandStatus.UNKNOWN:
            return RuleDecision.not_applicable(self.rule_id,"No known configured offensive-hand verdict is available.")
        if offense.status is not OffensiveHandStatus.QUALIFIES:
            return RuleDecision.not_applicable(self.rule_id,"Configured offensive-hand policy does not qualify this hand.")
        suit,level=six[0]
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.from_bid(Bid(level,Strain(int(suit)))),
            explanation="SAYC Weak Jump Overcall: direct preemptive jump, six-card suit, approximately 6–10 HCP, and explicit offensive-hand policy qualification.",
            sources=tuple(dict.fromkeys((_SOURCE,)+offense.sources)),
            priority=100,
        )

def create_sayc_weak_jump_overcall_engine(registry:PolicyRegistry)->BiddingEngine:
    return BiddingEngine((SaycWeakJumpOvercallRule(registry),))
