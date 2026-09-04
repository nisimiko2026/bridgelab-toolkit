"""Conservative SAYC opener rebids after exact 1♦-P-1♥-P.

Frozen BridgeLab sources support this ordered decision structure after a minor
opening and a one-major response:

1. support responder's major;
2. show a natural second suit, normally four cards;
3. after a major response, notrump precedes rebidding the minor in the
   dedicated opener-after-minor article;
4. rebidding the opening minor generally shows six cards or no better
   descriptive rebid.

This module deliberately implements only deterministic slices.  In particular,
2♣ is suppressed when four spades exist so the economical major second suit is
shown first, and the diamond rebid uses the stricter six-card branch rather
than the source's qualitative "or no better descriptive rebid" alternative.
"""

from __future__ import annotations
from dataclasses import dataclass
from .auction import Call,CallType,Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext,KnowledgeSource,RuleDecision
from .models import Suit

SAYC_ARTICLE="bidding/systems/sayc"
MINOR_ARTICLE="bidding/natural-bids/rebids/opener-after-minor"
PRIORITY=KnowledgeSource(MINOR_ARTICLE,"Rebids After Different Responses / After 1♥ or 1♠")
SECOND_SUIT=KnowledgeSource(MINOR_ARTICLE,"Showing a Second Suit")
MINOR_REBID=KnowledgeSource(MINOR_ARTICLE,"Rebidding the Minor")
NOTRUMP=KnowledgeSource(MINOR_ARTICLE,"Notrump Rebids")
SUPPORT=KnowledgeSource(MINOR_ARTICLE,"Supporting Responder / Four-Card Support")
_SAYC={"sayc","standard american yellow card"}

def _exact(context:BiddingContext)->bool:
    e=context.auction.entries
    if len(e)!=4:return False
    o,rho,r,lho=e
    return (
        o.seat is context.seat and o.call.kind is CallType.BID and o.call.bid is not None
        and o.call.bid.level==1 and o.call.bid.strain is Strain.DIAMONDS
        and rho.call.kind is CallType.PASS
        and r.seat is context.seat.partner() and r.call.kind is CallType.BID and r.call.bid is not None
        and r.call.bid.level==1 and r.call.bid.strain is Strain.HEARTS
        and lho.call.kind is CallType.PASS
    )

def _scope(rule_id:str,context:BiddingContext):
    if context.system.system.casefold() not in _SAYC:
        return RuleDecision.not_applicable(rule_id,"Rule is scoped to SAYC.")
    if not _exact(context):
        return RuleDecision.not_applicable(rule_id,"Requires exact 1♦ — Pass — 1♥ — Pass — ?.")

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneHeartTwoHeartRule:
    rule_id:str="sayc.opener.1d.1h.2h"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        x=_scope(self.rule_id,context)
        if x:return x
        if context.evaluation.length(Suit.HEARTS)<4:
            return RuleDecision.not_applicable(self.rule_id,"Requires four-card responder-major support.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.parse("2H"),priority=100,
            explanation="The dedicated opener-after-minor source gives responder-major support first priority and its four-card-support example uses a simple raise.",
            sources=(PRIORITY,SUPPORT),
        )

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneHeartOneSpadeRule:
    rule_id:str="sayc.opener.1d.1h.1s"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        x=_scope(self.rule_id,context)
        if x:return x
        if context.evaluation.length(Suit.HEARTS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Supporting responder has higher source priority.")
        if context.evaluation.length(Suit.SPADES)<4:
            return RuleDecision.not_applicable(self.rule_id,"Natural second-suit evidence normally requires four cards.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.parse("1S"),priority=90,
            explanation="Without heart support, the source next prioritizes showing a natural four-card second suit; 1♠ is the economical major second suit.",
            sources=(PRIORITY,SECOND_SUIT),
        )

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneHeartTwoClubRule:
    rule_id:str="sayc.opener.1d.1h.2c"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        x=_scope(self.rule_id,context)
        if x:return x
        if context.evaluation.length(Suit.HEARTS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Supporting responder has higher source priority.")
        if context.evaluation.length(Suit.SPADES)>=4:
            return RuleDecision.not_applicable(self.rule_id,"A four-card spade second suit is shown first in this conservative slice.")
        if context.evaluation.length(Suit.CLUBS)<4:
            return RuleDecision.not_applicable(self.rule_id,"Natural second-suit evidence normally requires four clubs.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.parse("2C"),priority=85,
            explanation="Without heart support or a four-card spade major, the source supports showing a natural four-card club second suit.",
            sources=(PRIORITY,SECOND_SUIT),
        )

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneHeartOneNotrumpRule:
    rule_id:str="sayc.opener.1d.1h.1nt"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        x=_scope(self.rule_id,context)
        if x:return x
        if not 12<=context.evaluation.hcp<=14 or not context.evaluation.is_balanced:
            return RuleDecision.not_applicable(self.rule_id,"Canonical minor-opener 1NT rebid is approximately 12-14 balanced.")
        if context.evaluation.length(Suit.HEARTS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Supporting responder has higher source priority.")
        if context.evaluation.length(Suit.SPADES)>=4 or context.evaluation.length(Suit.CLUBS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"A natural four-card second suit has higher source priority.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.parse("1NT"),priority=70,
            explanation="After support and second-suit branches are excluded, the dedicated minor-opener source gives 1NT as approximately 12-14 balanced.",
            sources=(PRIORITY,NOTRUMP),
        )

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneHeartTwoNotrumpRule:
    rule_id:str="sayc.opener.1d.1h.2nt"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        x=_scope(self.rule_id,context)
        if x:return x
        if not 18<=context.evaluation.hcp<=19 or not context.evaluation.is_balanced:
            return RuleDecision.not_applicable(self.rule_id,"Canonical minor-opener 2NT rebid is approximately 18-19 balanced.")
        if context.evaluation.length(Suit.HEARTS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Supporting responder has higher source priority.")
        if context.evaluation.length(Suit.SPADES)>=4 or context.evaluation.length(Suit.CLUBS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"A natural four-card second suit has higher source priority.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.parse("2NT"),priority=69,
            explanation="After support and second-suit branches are excluded, the dedicated minor-opener source gives 2NT as approximately 18-19 balanced.",
            sources=(PRIORITY,NOTRUMP),
        )

@dataclass(frozen=True,slots=True)
class SaycOneDiamondOneHeartTwoDiamondRule:
    rule_id:str="sayc.opener.1d.1h.2d"
    def evaluate(self,context:BiddingContext)->RuleDecision:
        x=_scope(self.rule_id,context)
        if x:return x
        if context.evaluation.length(Suit.HEARTS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"Supporting responder has higher source priority.")
        if context.evaluation.length(Suit.SPADES)>=4 or context.evaluation.length(Suit.CLUBS)>=4:
            return RuleDecision.not_applicable(self.rule_id,"A natural four-card second suit has higher source priority.")
        if (12<=context.evaluation.hcp<=14 and context.evaluation.is_balanced) or (18<=context.evaluation.hcp<=19 and context.evaluation.is_balanced):
            return RuleDecision.not_applicable(self.rule_id,"An executable notrump rebid has higher source priority after a major response.")
        if context.evaluation.length(Suit.DIAMONDS)<6:
            return RuleDecision.not_applicable(self.rule_id,"This conservative minor-rebid slice requires six diamonds.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.parse("2D"),priority=60,
            explanation="After support, second-suit and executable notrump branches are excluded, the source says rebidding the opening minor generally shows a six-card suit.",
            sources=(PRIORITY,MINOR_REBID),
        )

def create_sayc_one_diamond_one_heart_opener_rebid_engine()->BiddingEngine:
    return BiddingEngine((
        SaycOneDiamondOneHeartTwoHeartRule(),
        SaycOneDiamondOneHeartOneSpadeRule(),
        SaycOneDiamondOneHeartTwoClubRule(),
        SaycOneDiamondOneHeartOneNotrumpRule(),
        SaycOneDiamondOneHeartTwoNotrumpRule(),
        SaycOneDiamondOneHeartTwoDiamondRule(),
    ))
