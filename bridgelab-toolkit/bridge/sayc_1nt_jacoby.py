"""Conservative Jacoby Transfers after an uncontested SAYC 1NT opening."""
from dataclasses import dataclass
from .auction import Call
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit
_SOURCE=KnowledgeSource("bidding/conventions/transfers/jacoby-transfers","Jacoby Transfers")
_SAYC={"sayc","standard american yellow card"}
def _calls(c): return tuple(e.call.serialize() for e in c.auction.entries)

@dataclass(frozen=True,slots=True)
class SaycOneNotrumpJacobyResponseRule:
    rule_id:str="sayc.response.1nt.jacoby"
    def evaluate(self,c):
        if c.system.system.casefold() not in _SAYC: return RuleDecision.not_applicable(self.rule_id,"SAYC only.")
        if _calls(c)!=("1NT","P"): return RuleDecision.not_applicable(self.rule_id,"Requires uncontested 1NT-P.")
        h,s=c.evaluation.length(Suit.HEARTS),c.evaluation.length(Suit.SPADES)
        if h>=5 and s<5: bid,why="2D","5+ hearts only: Jacoby transfer."
        elif s>=5 and h<5: bid,why="2H","5+ spades only: Jacoby transfer."
        else: return RuleDecision.not_applicable(self.rule_id,"No unique source-safe transfer.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse(bid),explanation=why,sources=(_SOURCE,),priority=100)

@dataclass(frozen=True,slots=True)
class SaycOneNotrumpJacobyAcceptanceRule:
    rule_id:str="sayc.opener.1nt.jacoby.accept"
    def evaluate(self,c):
        if c.system.system.casefold() not in _SAYC: return RuleDecision.not_applicable(self.rule_id,"SAYC only.")
        a=_calls(c)
        if a==("1NT","P","2D","P"): bid="2H"
        elif a==("1NT","P","2H","P"): bid="2S"
        else: return RuleDecision.not_applicable(self.rule_id,"No established 1NT Jacoby transfer.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse(bid),explanation="Opener normally accepts the Jacoby transfer.",sources=(_SOURCE,),priority=100)

def create_sayc_one_notrump_jacoby_response_engine(): return BiddingEngine((SaycOneNotrumpJacobyResponseRule(),))
def create_sayc_one_notrump_jacoby_accept_engine(): return BiddingEngine((SaycOneNotrumpJacobyAcceptanceRule(),))

from .jacoby_continuation_strength_policy import JacobyContinuationStrengthClass
from .policy_registry import PolicyRegistry, assess_configured_jacoby_continuation_strength

@dataclass(frozen=True, slots=True)
class SaycOneNotrumpJacobyContinuationRule:
    """Translate an explicitly supplied Jacoby continuation strength class.

    The frozen source supplies the class-to-call mapping but not numeric HCP
    boundaries.  This rule therefore abstains unless a configured policy
    supplies the class; BridgeLab provides no default classifier.
    """
    registry: PolicyRegistry
    rule_id: str = "sayc.responder.1nt.jacoby.continuation"

    def evaluate(self, c):
        if c.system.system.casefold() not in _SAYC:
            return RuleDecision.not_applicable(self.rule_id, "SAYC only.")
        a = _calls(c)
        if a == ("1NT", "P", "2D", "P", "2H", "P"):
            game_bid = "4H"
        elif a == ("1NT", "P", "2H", "P", "2S", "P"):
            game_bid = "4S"
        else:
            return RuleDecision.not_applicable(self.rule_id, "Requires an accepted uncontested 1NT Jacoby transfer.")

        assessment = assess_configured_jacoby_continuation_strength(c, self.registry)
        if assessment is None:
            return RuleDecision.not_applicable(self.rule_id, "No Jacoby continuation strength policy is explicitly configured.")

        cls = assessment.strength_class
        if cls is JacobyContinuationStrengthClass.WEAK:
            bid, why = "P", "Explicit Jacoby continuation class WEAK: pass the accepted transfer."
        elif cls is JacobyContinuationStrengthClass.INVITATIONAL:
            bid, why = "2NT", "Explicit Jacoby continuation class INVITATIONAL: bid 2NT."
        elif cls is JacobyContinuationStrengthClass.GAME_GOING:
            bid, why = game_bid, f"Explicit Jacoby continuation class GAME_GOING: bid {game_bid}."
        elif cls is JacobyContinuationStrengthClass.SLAM_INTEREST:
            return RuleDecision.not_applicable(self.rule_id, "SLAM_INTEREST requires further partnership slam methods.")
        else:
            return RuleDecision.not_applicable(self.rule_id, "Jacoby continuation strength is UNKNOWN.")

        sources = (_SOURCE,) + tuple(s for s in assessment.sources if s != _SOURCE)
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse(bid),
            explanation=why + " " + assessment.explanation.strip(),
            sources=sources,
            priority=100,
        )


def create_sayc_one_notrump_jacoby_continuation_engine(registry: PolicyRegistry) -> BiddingEngine:
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    return BiddingEngine((SaycOneNotrumpJacobyContinuationRule(registry),))
