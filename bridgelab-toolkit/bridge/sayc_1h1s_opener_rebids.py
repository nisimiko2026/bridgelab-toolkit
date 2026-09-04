"""Conservative SAYC opener rebids after exact 1♥-P-1♠-P.

Frozen sources give the priority support -> second suit -> rebid hearts ->
notrump.  The dedicated opener-after-major article explicitly gives
1♥-1♠-2♦ as natural, at least four diamonds, minimum or medium.  It describes
second suits generally as normally four cards and natural.  It does not give
an equally exact 1♥-1♠-2♣ contract, so clubs remain unresolved.

The source also gives 1♥-1♠-1NT as balanced/minimum/no support/no second suit,
2NT as approximately 18-19 balanced, and a major rebid as usually six cards
when no better description exists.
"""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .models import Suit
SAYC="bidding/systems/sayc"
MAJOR_ARTICLE="bidding/natural-bids/rebids/opener-after-major"
PRIORITY=KnowledgeSource(MAJOR_ARTICLE,"Rebids After Different Responses / After New Suit Response")
SECOND=KnowledgeSource(MAJOR_ARTICLE,"Showing a Second Suit")
MAJOR=KnowledgeSource(MAJOR_ARTICLE,"Rebidding the Major")
NOTRUMP=KnowledgeSource(MAJOR_ARTICLE,"Notrump Rebids")
_SAYC={"sayc","standard american yellow card"}

def _exact(c):
 e=c.auction.entries
 if len(e)!=4:return False
 o,rho,r,lho=e
 return (o.seat is c.seat and o.call.kind is CallType.BID and o.call.bid is not None and o.call.bid.level==1 and o.call.bid.strain is Strain.HEARTS
 and rho.call.kind is CallType.PASS and r.seat is c.seat.partner() and r.call.kind is CallType.BID and r.call.bid is not None
 and r.call.bid.level==1 and r.call.bid.strain is Strain.SPADES and lho.call.kind is CallType.PASS)

def _scope(rule,c):
 if c.system.system.casefold() not in _SAYC:return RuleDecision.not_applicable(rule,"Rule is scoped to SAYC.")
 if not _exact(c):return RuleDecision.not_applicable(rule,"Requires exact 1♥ — Pass — 1♠ — Pass — ?.")

@dataclass(frozen=True,slots=True)
class SaycOneHeartOneSpadeTwoDiamondRule:
 rule_id:str="sayc.opener.1h.1s.2d"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.length(Suit.CLUBS)>=4:return RuleDecision.not_applicable(self.rule_id,"A club second-suit branch also exists and its exact precedence is not source-defined.")
  if c.evaluation.length(Suit.DIAMONDS)<4:return RuleDecision.not_applicable(self.rule_id,"Exact source example requires at least four diamonds.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2D"),priority=90,
   explanation="The frozen opener-after-major source explicitly gives 1♥-1♠-2♦ as natural, 4+ diamonds, minimum or medium.",
   sources=(PRIORITY,SECOND))

@dataclass(frozen=True,slots=True)
class SaycOneHeartOneSpadeTwoHeartRule:
 rule_id:str="sayc.opener.1h.1s.2h"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.length(Suit.CLUBS)>=4 or c.evaluation.length(Suit.DIAMONDS)>=4:return RuleDecision.not_applicable(self.rule_id,"A second-suit branch has higher priority.")
  if c.evaluation.length(Suit.HEARTS)<6:return RuleDecision.not_applicable(self.rule_id,"Major rebid normally shows a six-card suit.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2H"),priority=70,
   explanation="With higher-priority support and second-suit branches excluded, the source describes rebidding the major as usually six cards.",
   sources=(PRIORITY,MAJOR))

@dataclass(frozen=True,slots=True)
class SaycOneHeartOneSpadeOneNotrumpRule:
 rule_id:str="sayc.opener.1h.1s.1nt"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if not 12<=c.evaluation.hcp<=14 or not c.evaluation.is_balanced:return RuleDecision.not_applicable(self.rule_id,"1NT rebid is 12-14 balanced.")
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.length(Suit.CLUBS)>=4 or c.evaluation.length(Suit.DIAMONDS)>=4:return RuleDecision.not_applicable(self.rule_id,"A second suit has higher priority.")
  if c.evaluation.length(Suit.HEARTS)>=6:return RuleDecision.not_applicable(self.rule_id,"Six-card heart rebid has higher priority.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("1NT"),priority=60,
   explanation="The frozen source explicitly describes 1♥-1♠-1NT as balanced, minimum, with no support and no second suit.",
   sources=(PRIORITY,NOTRUMP))

@dataclass(frozen=True,slots=True)
class SaycOneHeartOneSpadeTwoNotrumpRule:
 rule_id:str="sayc.opener.1h.1s.2nt"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if not 18<=c.evaluation.hcp<=19 or not c.evaluation.is_balanced:return RuleDecision.not_applicable(self.rule_id,"2NT rebid is approximately 18-19 balanced.")
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.length(Suit.CLUBS)>=4 or c.evaluation.length(Suit.DIAMONDS)>=4:return RuleDecision.not_applicable(self.rule_id,"A second suit has higher priority.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2NT"),priority=59,
   explanation="With higher-priority support and second-suit branches excluded, the frozen source gives 2NT as approximately 18-19 balanced.",
   sources=(PRIORITY,NOTRUMP))

def create_sayc_one_heart_one_spade_opener_rebid_engine():
 return BiddingEngine((SaycOneHeartOneSpadeTwoDiamondRule(),SaycOneHeartOneSpadeTwoHeartRule(),
  SaycOneHeartOneSpadeOneNotrumpRule(),SaycOneHeartOneSpadeTwoNotrumpRule()))
