"""Source-grounded SAYC direct 1NT overcall.

Frozen SAYC gives 15–18 HCP, balanced, with a stopper in the opponent's
one-level suit. Stopper interpretation remains behind an explicitly configured
StopperPolicy; BridgeLab supplies no default formula.
"""
from dataclasses import dataclass
from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .policy_registry import PolicyRegistry, assess_configured_stopper
from .stopper_policy import StopperStatus

_SOURCE=KnowledgeSource("bidding/systems/sayc","Notrump Overcalls — Direct 1NT")
_SAYC={"sayc","standard american yellow card"}

def _direct_suit_opening(context):
    entries=context.auction.entries
    if len(entries)!=1:return None
    call=entries[0].call
    if call.kind is not CallType.BID or call.bid is None:return None
    if call.bid.level!=1 or call.bid.strain is Strain.NOTRUMP:return None
    return call.bid.strain

@dataclass(frozen=True,slots=True)
class SaycDirectOneNotrumpOvercallRule:
    registry: PolicyRegistry
    rule_id: str="sayc.overcall.direct.1nt"
    def evaluate(self,context):
        if context.system.system.casefold() not in _SAYC:
            return RuleDecision.not_applicable(self.rule_id,"Rule is SAYC-only.")
        opening=_direct_suit_opening(context)
        if opening is None:
            return RuleDecision.not_applicable(self.rule_id,"Requires direct seat after one natural one-level suit opening.")
        if not 15<=context.evaluation.hcp<=18:
            return RuleDecision.not_applicable(self.rule_id,"Frozen SAYC source gives 15–18 HCP for a direct 1NT overcall.")
        if not context.evaluation.is_balanced:
            return RuleDecision.not_applicable(self.rule_id,"Frozen SAYC source requires a balanced hand.")
        assessment=assess_configured_stopper(context,self.registry,opening.suit)
        if assessment is None or assessment.status is StopperStatus.UNKNOWN:
            return RuleDecision.not_applicable(self.rule_id,"No known configured stopper verdict is available for opener's suit.")
        if assessment.status is not StopperStatus.STOPPED:
            return RuleDecision.not_applicable(self.rule_id,"Configured stopper policy does not show opener's suit stopped.")
        candidate=Call.parse("1NT")
        if not context.auction.is_legal(candidate):
            return RuleDecision.not_applicable(self.rule_id,"1NT is not legal in the current auction.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=candidate,
            explanation="Frozen SAYC direct 1NT: 15–18 HCP, balanced, and the explicitly configured stopper policy confirms a stopper in opener's suit.",
            sources=tuple(dict.fromkeys((_SOURCE,)+assessment.sources)),priority=100)

def create_sayc_direct_one_notrump_overcall_engine(registry):
    return BiddingEngine((SaycDirectOneNotrumpOvercallRule(registry),))
