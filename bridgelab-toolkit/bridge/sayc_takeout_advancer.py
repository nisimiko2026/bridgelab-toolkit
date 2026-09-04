"""Controlled minimum Advancer response to a direct SAYC Takeout Double.

Frozen SAYC: responder normally bids the cheapest four-card suit. Strength
branches (jump/NT/cue) are not numerically defined, so this rule activates only
when an explicitly configured TakeoutAdvancerStrengthPolicy says MINIMUM.
"""
from dataclasses import dataclass
from .auction import Bid,Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .models import Suit
from .policy_registry import PolicyRegistry,assess_configured_takeout_advancer_strength
from .takeout_advancer_strength_policy import TakeoutAdvancerStrengthClass

_SOURCE=KnowledgeSource("bidding/systems/sayc","Responses to Takeout Double")
_DETAIL=KnowledgeSource("bidding/conventions/doubles/take-out-double","Responses")

def _direct_takeout_sequence(context):
    calls=context.auction.calls
    if len(calls)!=3:return None
    opening,double,pas=calls
    if opening.kind is not CallType.BID or opening.bid is None or opening.bid.level!=1 or opening.bid.strain is Strain.NOTRUMP:return None
    if double.kind is not CallType.DOUBLE or pas.kind is not CallType.PASS:return None
    return Suit(int(opening.bid.strain))

@dataclass(frozen=True,slots=True)
class SaycTakeoutAdvancerMinimumRule:
    registry:PolicyRegistry
    rule_id:str="sayc.advancer.takeout.minimum.natural"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        if context.system.system.strip().casefold() not in {"sayc","standard american yellow card"}:
            return RuleDecision.not_applicable(self.rule_id,"Rule is SAYC-only.")
        opener=_direct_takeout_sequence(context)
        if opener is None:
            return RuleDecision.not_applicable(self.rule_id,"Requires opponent one-level suit opening, Double, Pass.")
        assessment=assess_configured_takeout_advancer_strength(context,self.registry)
        if assessment is None or assessment.strength_class is TakeoutAdvancerStrengthClass.UNKNOWN:
            return RuleDecision.not_applicable(self.rule_id,"No known configured Takeout Advancer strength classification.")
        if assessment.strength_class is not TakeoutAdvancerStrengthClass.MINIMUM:
            return RuleDecision.not_applicable(self.rule_id,"Configured Advancer strength is not MINIMUM.")
        # Frozen scoped SAYC says cheapest four-card suit. The opener's suit is
        # not an unbid suit, so it is excluded. Search calls in auction order.
        candidates=[]
        for level in range(1,8):
            for suit in Suit:
                if suit is opener or context.hand.length(suit)<4:continue
                call=Call.from_bid(Bid(level,Strain(int(suit))))
                if context.auction.is_legal(call):
                    candidates.append(call)
            if candidates:break
        if not candidates:
            return RuleDecision.not_applicable(self.rule_id,"MINIMUM hand has no legal four-card unbid-suit response.")
        # Bid order is level then C,D,H,S; therefore first is mechanically cheapest.
        candidate=candidates[0]
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=candidate,
            explanation="Minimum SAYC Advancer response after partner's Takeout Double: explicit MINIMUM strength classification and the frozen-source cheapest legal four-card unbid suit.",
            sources=tuple(dict.fromkeys((_SOURCE,_DETAIL)+assessment.sources)),priority=100)

def create_sayc_takeout_advancer_minimum_engine(registry):
    return BiddingEngine((SaycTakeoutAdvancerMinimumRule(registry),))
