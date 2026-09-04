"""Conservative SAYC opener rebids after exact 1♣-P-1♠-P.

Frozen sources used here:
* SAYC: support responder -> show four-card major -> rebid clubs -> notrump.
* opener-after-minor: support -> second suit -> notrump -> rebid minor after a
  major response; natural second suits normally have four cards.
* opener-after-minor gives exact 1♣-1♠-2♦ as natural, 4+ diamonds,
  minimum/medium.
* opener-after-minor gives exact 1♣-1♠-2♥ as a reverse, normally 16+ HCP,
  longer clubs than hearts, forcing one round (exact strength system-dependent).
* 1NT is about 12-14 balanced; 2NT about 18-19 balanced.

Only deterministic slices are executable.
"""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .models import Suit

SAYC="bidding/systems/sayc"
MINOR_ARTICLE="bidding/natural-bids/rebids/opener-after-minor"
CLUB_PRIORITY=KnowledgeSource(SAYC,"Opener's Rebids After 1♣")
SECOND=KnowledgeSource(MINOR_ARTICLE,"Showing a Second Suit")
REVERSE=KnowledgeSource(MINOR_ARTICLE,"Reverse Bids")
NT=KnowledgeSource(MINOR_ARTICLE,"Notrump Rebids")
MINOR=KnowledgeSource(MINOR_ARTICLE,"Rebidding the Minor")
_SAYC={"sayc","standard american yellow card"}

def _exact(c):
 e=c.auction.entries
 if len(e)!=4:return False
 o,rho,r,lho=e
 return (o.seat is c.seat and o.call.kind is CallType.BID and o.call.bid is not None and o.call.bid.level==1 and o.call.bid.strain is Strain.CLUBS
 and rho.call.kind is CallType.PASS and r.seat is c.seat.partner() and r.call.kind is CallType.BID and r.call.bid is not None
 and r.call.bid.level==1 and r.call.bid.strain is Strain.SPADES and lho.call.kind is CallType.PASS)

def _scope(rule,c):
 if c.system.system.casefold() not in _SAYC:return RuleDecision.not_applicable(rule,"Rule is scoped to SAYC.")
 if not _exact(c):return RuleDecision.not_applicable(rule,"Requires exact 1♣ — Pass — 1♠ — Pass — ?.")

@dataclass(frozen=True,slots=True)
class SaycOneClubOneSpadeTwoSpadeRule:
 rule_id:str="sayc.opener.1c.1s.2s"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.SPADES)<4:return RuleDecision.not_applicable(self.rule_id,"Requires four-card responder-major support.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2S"),priority=100,
   explanation="Support responder is first priority; the frozen minor-opener source's simple major raise uses four-card support.",
   sources=(CLUB_PRIORITY,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneSpadeTwoHeartReverseRule:
 rule_id:str="sayc.opener.1c.1s.2h.reverse"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.hcp<16:return RuleDecision.not_applicable(self.rule_id,"Frozen reverse example says normally at least 16+ HCP.")
  if c.evaluation.length(Suit.HEARTS)<4:return RuleDecision.not_applicable(self.rule_id,"Reverse requires at least four hearts.")
  if c.evaluation.length(Suit.CLUBS)<=c.evaluation.length(Suit.HEARTS):return RuleDecision.not_applicable(self.rule_id,"Frozen example requires clubs longer than hearts.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2H"),priority=95,
   explanation="Frozen minor-opener source explicitly gives 1♣-1♠-2♥ as a reverse: normally 16+ HCP, longer clubs than hearts.",
   sources=(REVERSE,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneSpadeTwoDiamondRule:
 rule_id:str="sayc.opener.1c.1s.2d"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.length(Suit.HEARTS)>=4:return RuleDecision.not_applicable(self.rule_id,"A heart branch exists; do not bypass it with diamonds.")
  if c.evaluation.length(Suit.DIAMONDS)<4:return RuleDecision.not_applicable(self.rule_id,"Exact source example requires at least four diamonds.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2D"),priority=90,
   explanation="Frozen minor-opener source explicitly gives 1♣-1♠-2♦ as natural, 4+ diamonds, minimum or medium.",
   sources=(SECOND,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneSpadeOneNotrumpRule:
 rule_id:str="sayc.opener.1c.1s.1nt"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if not 12<=c.evaluation.hcp<=14 or not c.evaluation.is_balanced:return RuleDecision.not_applicable(self.rule_id,"1NT rebid is approximately 12-14 balanced.")
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.length(Suit.HEARTS)>=4 or c.evaluation.length(Suit.DIAMONDS)>=4:return RuleDecision.not_applicable(self.rule_id,"A natural second suit has higher priority.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("1NT"),priority=75,
   explanation="After support and second-suit branches are excluded, the frozen source gives 1NT as approximately 12-14 balanced.",
   sources=(NT,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneSpadeTwoNotrumpRule:
 rule_id:str="sayc.opener.1c.1s.2nt"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if not 18<=c.evaluation.hcp<=19 or not c.evaluation.is_balanced:return RuleDecision.not_applicable(self.rule_id,"2NT rebid is approximately 18-19 balanced.")
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.length(Suit.HEARTS)>=4 or c.evaluation.length(Suit.DIAMONDS)>=4:return RuleDecision.not_applicable(self.rule_id,"A natural second suit has higher priority.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2NT"),priority=74,
   explanation="After support and second-suit branches are excluded, the frozen source gives 2NT as approximately 18-19 balanced.",
   sources=(NT,))

@dataclass(frozen=True,slots=True)
class SaycOneClubOneSpadeTwoClubRule:
 rule_id:str="sayc.opener.1c.1s.2c"
 def evaluate(self,c):
  x=_scope(self.rule_id,c)
  if x:return x
  if c.evaluation.length(Suit.SPADES)>=4:return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
  if c.evaluation.length(Suit.HEARTS)>=4 or c.evaluation.length(Suit.DIAMONDS)>=4:return RuleDecision.not_applicable(self.rule_id,"A natural second suit has higher priority.")
  if (12<=c.evaluation.hcp<=14 and c.evaluation.is_balanced) or (18<=c.evaluation.hcp<=19 and c.evaluation.is_balanced):
   return RuleDecision.not_applicable(self.rule_id,"An executable notrump branch has higher dedicated-source priority after a major response.")
  if c.evaluation.length(Suit.CLUBS)<6:return RuleDecision.not_applicable(self.rule_id,"Conservative minor rebid requires six clubs.")
  return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2C"),priority=60,
   explanation="After higher-priority branches are excluded, the source says rebidding the opening minor generally shows six cards.",
   sources=(MINOR,))

def create_sayc_one_club_one_spade_opener_rebid_engine():
 return BiddingEngine((SaycOneClubOneSpadeTwoSpadeRule(),SaycOneClubOneSpadeTwoHeartReverseRule(),
  SaycOneClubOneSpadeTwoDiamondRule(),SaycOneClubOneSpadeOneNotrumpRule(),
  SaycOneClubOneSpadeTwoNotrumpRule(),SaycOneClubOneSpadeTwoClubRule()))
