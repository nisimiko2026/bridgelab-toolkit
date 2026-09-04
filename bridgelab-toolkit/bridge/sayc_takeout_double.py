"""Controlled direct SAYC Takeout Double.

Frozen SAYC: opening values, shortness in opener's suit, support for the unbid
suits. The dedicated frozen article operationalizes opening values as
approximately 12+ HCP and typical support as at least three cards in every
unbid suit. The qualitative shortness term is delegated to the explicitly
configured OpponentSuitShortnessPolicy. No vulnerability/style exceptions are
invented here.
"""
from dataclasses import dataclass
from .auction import Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .models import Suit
from .opponent_suit_shortness_policy import OpponentSuitShortnessStatus
from .policy_registry import PolicyRegistry,assess_configured_opponent_suit_shortness

_SOURCE=KnowledgeSource("bidding/systems/sayc","Takeout Double")
_DETAIL=KnowledgeSource("bidding/conventions/doubles/take-out-double","Requirements")

def _direct_opening_suit(context):
    if len(context.auction.calls)!=1:return None
    c=context.auction.calls[0]
    if c.kind is not CallType.BID or c.bid is None or c.bid.level!=1 or c.bid.strain is Strain.NOTRUMP:return None
    return Suit(int(c.bid.strain))

@dataclass(frozen=True,slots=True)
class SaycTakeoutDoubleRule:
    registry:PolicyRegistry
    rule_id:str="sayc.double.takeout.direct"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        if context.system.system.strip().casefold() not in {"sayc","standard american yellow card"}:
            return RuleDecision.not_applicable(self.rule_id,"Rule is SAYC-only.")
        opener=_direct_opening_suit(context)
        if opener is None:return RuleDecision.not_applicable(self.rule_id,"Requires direct seat after an opponent one-level suit opening.")
        if context.evaluation.hcp<12:
            return RuleDecision.not_applicable(self.rule_id,"Dedicated frozen source operationalizes opening values as approximately 12+ HCP.")
        unbid=tuple(s for s in Suit if s is not opener)
        if any(context.hand.length(s)<3 for s in unbid):
            return RuleDecision.not_applicable(self.rule_id,"Dedicated frozen source gives at least three cards in each unbid suit as typical support.")
        a=assess_configured_opponent_suit_shortness(context,self.registry,opener,context.hand.length(opener))
        if a is None or a.status is OpponentSuitShortnessStatus.UNKNOWN:
            return RuleDecision.not_applicable(self.rule_id,"No known configured opponent-suit-shortness verdict is available.")
        if a.status is not OpponentSuitShortnessStatus.QUALIFIES:
            return RuleDecision.not_applicable(self.rule_id,"Configured shortness policy does not qualify the opener-suit holding.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.double(),
            explanation="Direct SAYC Takeout Double: 12+ HCP operationalization of opening values, at least three cards in every unbid suit, and explicit policy qualification of shortness in opener's suit.",
            sources=tuple(dict.fromkeys((_SOURCE,_DETAIL)+a.sources)),priority=100)

def create_sayc_takeout_double_engine(registry):
    return BiddingEngine((SaycTakeoutDoubleRule(registry),))
