"""Theory-neutral abstention diagnostics for routed bidding evaluation."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .bidding_engine import BiddingEngineResult
from .bidding_rules import BiddingContext
from .engine_router import BiddingEngineRouter

class AbstentionReason(str, Enum):
    NO_ROUTE="no-route"
    ROUTED_NO_APPLICABLE_RULE="routed-no-applicable-rule"

@dataclass(frozen=True,slots=True)
class RuleRejection:
    rule_id:str
    reason:str

@dataclass(frozen=True,slots=True)
class AbstentionDiagnostic:
    reason:AbstentionReason
    route_id:str|None
    auction:str
    rejected_rules:tuple[RuleRejection,...]

@dataclass(frozen=True,slots=True)
class DiagnosedEngineResult:
    result:BiddingEngineResult
    abstention:AbstentionDiagnostic|None

def evaluate_with_abstention_diagnostic(router:BiddingEngineRouter,context:BiddingContext)->DiagnosedEngineResult:
    """Evaluate unchanged production behavior and describe only abstentions."""
    if not isinstance(router,BiddingEngineRouter): raise TypeError("router must be BiddingEngineRouter")
    if not isinstance(context,BiddingContext): raise TypeError("context must be BiddingContext")
    match=router.match(context); result=router.evaluate(context)
    if result.has_recommendation: return DiagnosedEngineResult(result,None)
    if match is None:
        d=AbstentionDiagnostic(AbstentionReason.NO_ROUTE,None,context.auction.serialize(),())
    else:
        d=AbstentionDiagnostic(AbstentionReason.ROUTED_NO_APPLICABLE_RULE,match.route_id,context.auction.serialize(),tuple(RuleRejection(x.rule_id,x.explanation) for x in result.decisions if not x.applicable))
    return DiagnosedEngineResult(result,d)
