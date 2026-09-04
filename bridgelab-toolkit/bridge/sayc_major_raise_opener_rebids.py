"""Conservative SAYC opener continuations after a traditional simple major raise.

Canonical BridgeLab sources:
* ``bidding/systems/sayc`` — simple raise is 6-9 support points; 1♠ responses
  are parallel to 1♥; a worked 1♠-2♠ example passes with a minimum opening.
* ``bidding/natural-bids/rebids/opener-after-major`` — minimum = 12-14 HCP;
  after a raise opener evaluates partscore/invitation/game/slam.

Only the minimum/pass slice is deterministic enough to execute.  Medium and
strong hands are deliberately left unresolved because the sources do not map
them to one unique call after a simple raise.
"""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .major_response_options import MajorRaiseStyle, major_raise_style

SAYC="bidding/systems/sayc"
MAJOR="bidding/natural-bids/rebids/opener-after-major"
SIMPLE=KnowledgeSource(SAYC,"Major-Suit Raises / Simple Raise")
EXAMPLE=KnowledgeSource(SAYC,"Example 1 – Simple Major Fit")
STRENGTH=KnowledgeSource(MAJOR,"Strength Categories / Minimum")
AFTER_RAISE=KnowledgeSource(MAJOR,"Rebids After Different Responses / After Raise")
_SAYC={"sayc","standard american yellow card"}

def _exact(c, strain):
 e=c.auction.entries
 if len(e)!=4:return False
 o,rho,r,lho=e
 return (o.seat is c.seat and o.call.kind is CallType.BID and o.call.bid is not None
  and o.call.bid.level==1 and o.call.bid.strain is strain
  and rho.call.kind is CallType.PASS
  and r.seat is c.seat.partner() and r.call.kind is CallType.BID and r.call.bid is not None
  and r.call.bid.level==2 and r.call.bid.strain is strain
  and lho.call.kind is CallType.PASS)

@dataclass(frozen=True,slots=True)
class SaycSimpleMajorRaiseMinimumPassRule:
 strain:Strain
 rule_id:str
 def evaluate(self,c):
  if c.system.system.casefold() not in _SAYC:
   return RuleDecision.not_applicable(self.rule_id,"Rule is scoped to SAYC.")
  if major_raise_style(c.system) is not MajorRaiseStyle.TRADITIONAL:
   return RuleDecision.not_applicable(self.rule_id,"Requires the traditional major-raise treatment.")
  if not _exact(c,self.strain):
   return RuleDecision.not_applicable(self.rule_id,"Requires exact uncontested one-major — two-major — Pass position.")
  if not 12<=c.evaluation.hcp<=14:
   return RuleDecision.not_applicable(self.rule_id,"The executable source slice is opener's 12-14 HCP minimum.")
  return RuleDecision.recommend(
   rule_id=self.rule_id,candidate=Call.parse("P"),priority=100,
   explanation="Responder's bid is the traditional 6-9 simple major raise. Canonical opener-rebid material defines 12-14 HCP as minimum, and the SAYC worked simple-major-fit example passes with a minimum opening.",
   sources=(SIMPLE,STRENGTH,AFTER_RAISE,EXAMPLE))

def create_sayc_simple_major_raise_opener_rebid_engine(strain:Strain):
 if strain not in (Strain.HEARTS,Strain.SPADES):
  raise ValueError("simple-major-raise continuation requires hearts or spades")
 suffix="1h.2h" if strain is Strain.HEARTS else "1s.2s"
 return BiddingEngine((SaycSimpleMajorRaiseMinimumPassRule(strain,f"sayc.opener.{suffix}.pass.minimum"),))
