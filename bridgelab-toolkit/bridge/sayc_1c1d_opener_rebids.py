"""Conservative SAYC opener rebids after exact 1♣-P-1♦-P.

Frozen SAYC priority after 1♣:
support responder, show four-card major, rebid clubs, bid notrump.

This phase executes:
* 1♥ with 4+ hearts (when both majors exist, hearts is the economical first
  four-card-major rebid; no claim is made beyond the source priority/order);
* 1♠ with 4+ spades and fewer than four hearts;
* 2♣ with 6+ clubs after excluding four-card majors;
* 1NT with 12-14 balanced after excluding four-card majors and six clubs.

A diamond raise is not implemented because the source gives no deterministic
support length/strength contract for 1♣-1♦ in this section.
"""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .models import Suit
ARTICLE="bidding/systems/sayc"
PRIORITY=KnowledgeSource(ARTICLE,"Opener's Rebids After 1♣")
MINOR=KnowledgeSource(ARTICLE,"Rebidding Minor")
NOTRUMP=KnowledgeSource(ARTICLE,"Notrump Rebids")
_SAYC={"sayc","standard american yellow card"}

def _exact(c):
 e=c.auction.entries
 if len(e)!=4:return False
 o,rho,r,lho=e
 return (o.seat is c.seat and o.call.kind is CallType.BID and o.call.bid is not None and o.call.bid.level==1 and o.call.bid.strain is Strain.CLUBS
 and rho.call.kind is CallType.PASS and r.seat is c.seat.partner() and r.call.kind is CallType.BID and r.call.bid is not None
 and r.call.bid.level==1 and r.call.bid.strain is Strain.DIAMONDS and lho.call.kind is CallType.PASS)

def _scope(rule,c):
 if c.system.system.casefold() not in _SAYC:return RuleDecision.not_applicable(rule,"Rule is scoped to SAYC.")
 if not _exact(c):return RuleDecision.not_applicable(rule,"Requires exact 1♣ — Pass — 1♦ — Pass — ?.")

@dataclass(frozen=True,slots=True)
class SaycOneClubOneDiamondOneHeartRule:
 rule_id:str="sayc.opener.1c.1d.1h"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.HEARTS)<4:return RuleDecision.not_applicable(self.rule_id,"Requires a four-card heart major.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("1H"),priority=95,
   explanation="After 1♣ the canonical priority is to show a four-card major; 1♥ is the economical first major rebid.",
   sources=(PRIORITY,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneDiamondOneSpadeRule:
 rule_id:str="sayc.opener.1c.1d.1s"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.HEARTS)>=4:return RuleDecision.not_applicable(self.rule_id,"The executable heart-major branch has precedence.")
  if c.evaluation.length(Suit.SPADES)<4:return RuleDecision.not_applicable(self.rule_id,"Requires a four-card spade major.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("1S"),priority=90,
   explanation="After 1♣ the canonical priority is to show a four-card major; no four-card hearts are present.",
   sources=(PRIORITY,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneDiamondTwoClubRule:
 rule_id:str="sayc.opener.1c.1d.2c"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.HEARTS)>=4 or c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Showing a four-card major has higher source priority.")
  if c.evaluation.length(Suit.CLUBS)<6:return RuleDecision.not_applicable(self.rule_id,"Canonical minor rebid evidence normally requires six clubs.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2C"),priority=80,
   explanation="With four-card-major branches excluded, the canonical minor-rebid evidence supports a six-club rebid.",
   sources=(PRIORITY,MINOR))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneDiamondOneNotrumpRule:
 rule_id:str="sayc.opener.1c.1d.1nt"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if not 12<=c.evaluation.hcp<=14 or not c.evaluation.is_balanced:return RuleDecision.not_applicable(self.rule_id,"Canonical SAYC 1NT rebid is 12-14 balanced.")
  if c.evaluation.length(Suit.HEARTS)>=4 or c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Showing a four-card major has higher source priority.")
  if c.evaluation.length(Suit.CLUBS)>=6:return RuleDecision.not_applicable(self.rule_id,"Rebidding six clubs has higher source priority.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("1NT"),priority=70,
   explanation="Canonical SAYC gives 1NT rebid as 12-14 balanced after higher-priority 1♣ branches are excluded.",
   sources=(PRIORITY,NOTRUMP))

def create_sayc_one_club_one_diamond_opener_rebid_engine():
 return BiddingEngine((SaycOneClubOneDiamondOneHeartRule(),SaycOneClubOneDiamondOneSpadeRule(),
                       SaycOneClubOneDiamondTwoClubRule(),SaycOneClubOneDiamondOneNotrumpRule()))
