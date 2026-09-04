"""Conservative SAYC opener rebids after exact 1♦-P-1♠-P.

Canonical source: ``bidding/systems/sayc``.

Executable source-supported slices:
* support responder immediately: simple raise with four-card support;
* show a second suit: the source explicitly gives 1♦-1♠-2♣ as natural,
  showing four clubs;
* generic SAYC 1NT rebid: 12-14 balanced.

The source also explicitly identifies 1♦-1♠-2♥ as a reverse showing extra
values, longer diamonds, hearts, approximately 16+ HCP. That branch is kept
separate from the ordinary second-suit rule.

The dedicated frozen minor-opener source additionally supports 2NT as
approximately 18-19 balanced and rebidding the opening minor generally as a
six-card suit (or a qualitative no-better-description case).  Only the
objective six-card diamond slice is encoded here.
"""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .models import Suit

ARTICLE="bidding/systems/sayc"
MINOR_ARTICLE="bidding/natural-bids/rebids/opener-after-minor"
DIAMOND_REBID=KnowledgeSource(ARTICLE,"Opening 1♦ / Opener's Rebids")
PRIORITY=KnowledgeSource(ARTICLE,"Common Rebidding Priorities")
NOTRUMP=KnowledgeSource(ARTICLE,"Notrump Rebids")
REVERSE=KnowledgeSource(ARTICLE,"Reverse Bids")
SUPPORT=KnowledgeSource(ARTICLE,"Opener's Rebids After 1♣")
MINOR_NT=KnowledgeSource(MINOR_ARTICLE,"Notrump Rebids")
MINOR_REBID=KnowledgeSource(MINOR_ARTICLE,"Rebidding the Minor")
_SAYC={"sayc","standard american yellow card"}

def _exact(c:BiddingContext)->bool:
    e=c.auction.entries
    if len(e)!=4:return False
    o,rho,r,lho=e
    return (o.seat is c.seat and o.call.kind is CallType.BID and o.call.bid is not None
      and o.call.bid.level==1 and o.call.bid.strain is Strain.DIAMONDS
      and rho.call.kind is CallType.PASS
      and r.seat is c.seat.partner() and r.call.kind is CallType.BID and r.call.bid is not None
      and r.call.bid.level==1 and r.call.bid.strain is Strain.SPADES
      and lho.call.kind is CallType.PASS)

def _scope(rule_id,c):
    if c.system.system.casefold() not in _SAYC:
        return RuleDecision.not_applicable(rule_id,"Rule is scoped to SAYC.")
    if not _exact(c):
        return RuleDecision.not_applicable(rule_id,"Requires exact 1♦ — Pass — 1♠ — Pass — ?.")
    return None

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneSpadeTwoSpadeRule:
    rule_id:str="sayc.opener.1d.1s.2s"
    def evaluate(self,c):
        x=_scope(self.rule_id,c)
        if x:return x
        if c.evaluation.length(Suit.SPADES)<4:
            return RuleDecision.not_applicable(self.rule_id,"Support rebid requires four-card responder-major support.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2S"),priority=100,
          explanation="SAYC opener-rebid priority is to support responder immediately; the source describes a simple major raise as four-card support.",
          sources=(PRIORITY,SUPPORT))

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneSpadeTwoHeartReverseRule:
    rule_id:str="sayc.opener.1d.1s.2h.reverse"
    def evaluate(self,c):
        x=_scope(self.rule_id,c)
        if x:return x
        if c.evaluation.length(Suit.SPADES)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Support responder has higher source priority.")
        if c.evaluation.hcp<16 or c.evaluation.length(Suit.HEARTS)<4:
            return RuleDecision.not_applicable(self.rule_id,"Canonical reverse example requires approximately 16+ HCP and hearts.")
        if c.evaluation.length(Suit.DIAMONDS)<=c.evaluation.length(Suit.HEARTS):
            return RuleDecision.not_applicable(self.rule_id,"Canonical reverse example says diamonds are longer than hearts.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2H"),priority=90,
          explanation="The canonical SAYC source explicitly identifies 1♦ — 1♠ — 2♥ as a reverse: extra values, longer diamonds, hearts, approximately 16+ HCP.",
          sources=(REVERSE,))

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneSpadeTwoClubRule:
    rule_id:str="sayc.opener.1d.1s.2c"
    def evaluate(self,c):
        x=_scope(self.rule_id,c)
        if x:return x
        if c.evaluation.length(Suit.SPADES)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Support responder has higher source priority.")
        if c.evaluation.length(Suit.CLUBS)<4:
            return RuleDecision.not_applicable(self.rule_id,"Canonical 2♣ example shows four clubs.")
        if c.evaluation.length(Suit.HEARTS)>=4 and c.evaluation.hcp>=16 and c.evaluation.length(Suit.DIAMONDS)>c.evaluation.length(Suit.HEARTS):
            return RuleDecision.not_applicable(self.rule_id,"The source-explicit 2♥ reverse has precedence in this controlled branch.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2C"),priority=80,
          explanation="The canonical SAYC 1♦ — 1♠ — 2♣ example is natural and shows four clubs.",
          sources=(DIAMOND_REBID,PRIORITY))

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneSpadeOneNotrumpRule:
    rule_id:str="sayc.opener.1d.1s.1nt"
    def evaluate(self,c):
        x=_scope(self.rule_id,c)
        if x:return x
        if not 12<=c.evaluation.hcp<=14 or not c.evaluation.is_balanced:
            return RuleDecision.not_applicable(self.rule_id,"Canonical SAYC 1NT rebid is 12-14 balanced.")
        if c.evaluation.length(Suit.SPADES)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Support responder has higher source priority.")
        if c.evaluation.length(Suit.CLUBS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"A four-card club second suit has higher source priority.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("1NT"),priority=70,
          explanation="SAYC describes the 1NT rebid as 12-14 balanced; this slice excludes higher-priority support and the source-explicit club second suit.",
          sources=(PRIORITY,NOTRUMP))

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneSpadeTwoNotrumpRule:
    rule_id:str="sayc.opener.1d.1s.2nt"
    def evaluate(self,c):
        x=_scope(self.rule_id,c)
        if x:return x
        if not 18<=c.evaluation.hcp<=19 or not c.evaluation.is_balanced:
            return RuleDecision.not_applicable(self.rule_id,"Frozen minor-opener source gives 2NT as approximately 18-19 balanced.")
        if c.evaluation.length(Suit.SPADES)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
        if c.evaluation.length(Suit.CLUBS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"The source-explicit club second suit has higher priority.")
        if c.evaluation.length(Suit.HEARTS)>=4 and c.evaluation.length(Suit.DIAMONDS)>c.evaluation.length(Suit.HEARTS):
            return RuleDecision.not_applicable(self.rule_id,"A heart reverse shape is present; do not bypass the source-explicit reverse family.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2NT"),priority=69,
          explanation="After higher-priority support and second-suit branches are excluded, the frozen minor-opener source gives 2NT as approximately 18-19 balanced.",
          sources=(MINOR_NT,))

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneSpadeTwoDiamondRule:
    rule_id:str="sayc.opener.1d.1s.2d"
    def evaluate(self,c):
        x=_scope(self.rule_id,c)
        if x:return x
        if c.evaluation.length(Suit.SPADES)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Support responder has higher priority.")
        if c.evaluation.length(Suit.CLUBS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"A source-explicit club second suit has higher priority.")
        if c.evaluation.length(Suit.HEARTS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"A heart second-suit/reverse shape exists and must not be bypassed.")
        if c.evaluation.is_balanced and (12<=c.evaluation.hcp<=14 or 18<=c.evaluation.hcp<=19):
            return RuleDecision.not_applicable(self.rule_id,"An executable notrump range has higher dedicated-source priority after a major response.")
        if c.evaluation.length(Suit.DIAMONDS)<6:
            return RuleDecision.not_applicable(self.rule_id,"Conservative minor rebid encodes only the objective six-card diamond slice.")
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse("2D"),priority=60,
          explanation="After higher-priority branches are excluded, the frozen source says rebidding the opening minor generally shows six cards.",
          sources=(MINOR_REBID,))

def create_sayc_one_diamond_one_spade_opener_rebid_engine():
    return BiddingEngine((SaycOneDiamondOneSpadeTwoSpadeRule(),SaycOneDiamondOneSpadeTwoHeartReverseRule(),
                          SaycOneDiamondOneSpadeTwoClubRule(),SaycOneDiamondOneSpadeOneNotrumpRule(),
                          SaycOneDiamondOneSpadeTwoNotrumpRule(),SaycOneDiamondOneSpadeTwoDiamondRule()))
