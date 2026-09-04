"""Conservative SAYC opener rebids after exact 1♣-P-1♥-P.

Canonical source: ``bidding/systems/sayc``.

The 1♣ section gives exact priority:
support responder, show four-card major, rebid clubs, bid notrump.
The source explicitly shows 1♣-1♥-2♥ as four-card support and gives the
generic SAYC 1NT rebid as 12-14 balanced.  The rebidding-minor section gives
the parallel 1♣-1♠-2♣ example as usually six clubs/minimum.

For this auction, 1♠ is the economical source-directed four-card-major rebid.
No jump, reverse, or strength extension is inferred.
"""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .models import Suit

ARTICLE="bidding/systems/sayc"
PRIORITY=KnowledgeSource(ARTICLE,"Opener's Rebids After 1♣")
NOTRUMP=KnowledgeSource(ARTICLE,"Notrump Rebids")
MINOR=KnowledgeSource(ARTICLE,"Rebidding Minor")
_SAYC={"sayc","standard american yellow card"}

def _exact(c):
 e=c.auction.entries
 if len(e)!=4:return False
 o,rho,r,lho=e
 return (o.seat is c.seat and o.call.kind is CallType.BID and o.call.bid is not None
  and o.call.bid.level==1 and o.call.bid.strain is Strain.CLUBS
  and rho.call.kind is CallType.PASS and r.seat is c.seat.partner()
  and r.call.kind is CallType.BID and r.call.bid is not None
  and r.call.bid.level==1 and r.call.bid.strain is Strain.HEARTS
  and lho.call.kind is CallType.PASS)

def _scope(rule,c):
 if c.system.system.casefold() not in _SAYC:return RuleDecision.not_applicable(rule,"Rule is scoped to SAYC.")
 if not _exact(c):return RuleDecision.not_applicable(rule,"Requires exact 1♣ — Pass — 1♥ — Pass — ?.")

@dataclass(frozen=True,slots=True)
class SaycOneClubOneHeartTwoHeartRule:
 rule_id:str="sayc.opener.1c.1h.2h"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.HEARTS)<4:return RuleDecision.not_applicable(self.rule_id,"Canonical simple support requires four-card heart support.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2H"),priority=100,
   explanation="The canonical SAYC 1♣ rebid section explicitly shows 1♣ — 1♥ — 2♥ as four-card support.",
   sources=(PRIORITY,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneHeartOneSpadeRule:
 rule_id:str="sayc.opener.1c.1h.1s"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.HEARTS)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher source priority.")
  if c.evaluation.length(Suit.SPADES)<4:return RuleDecision.not_applicable(self.rule_id,"The 1♣ source priority calls for showing a four-card major.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("1S"),priority=90,
   explanation="After support, the canonical 1♣ rebid priority is to show a four-card major; 1♠ is the economical four-card-major rebid after 1♥.",
   sources=(PRIORITY,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneHeartTwoClubRule:
 rule_id:str="sayc.opener.1c.1h.2c"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.HEARTS)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher source priority.")
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Showing a four-card major has higher source priority.")
  if c.evaluation.length(Suit.CLUBS)<6:return RuleDecision.not_applicable(self.rule_id,"Canonical rebidding-minor example usually shows six clubs.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2C"),priority=80,
   explanation="With higher-priority support and four-card-major branches excluded, the canonical SAYC rebidding-minor example supports a six-club rebid.",
   sources=(PRIORITY,MINOR))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneHeartOneNotrumpRule:
 rule_id:str="sayc.opener.1c.1h.1nt"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if not 12<=c.evaluation.hcp<=14 or not c.evaluation.is_balanced:return RuleDecision.not_applicable(self.rule_id,"Canonical SAYC 1NT rebid is 12-14 balanced.")
  if c.evaluation.length(Suit.HEARTS)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher source priority.")
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Showing a four-card major has higher source priority.")
  if c.evaluation.length(Suit.CLUBS)>=6:return RuleDecision.not_applicable(self.rule_id,"Rebidding clubs has higher source priority.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("1NT"),priority=70,
   explanation="Canonical SAYC gives 1NT rebid as 12-14 balanced; all higher-priority 1♣ rebid branches are excluded.",
   sources=(PRIORITY,NOTRUMP))

def create_sayc_one_club_one_heart_opener_rebid_engine():
 return BiddingEngine((SaycOneClubOneHeartTwoHeartRule(),SaycOneClubOneHeartOneSpadeRule(),
                       SaycOneClubOneHeartTwoClubRule(),SaycOneClubOneHeartOneNotrumpRule()))
