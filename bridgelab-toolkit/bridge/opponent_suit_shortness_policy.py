"""Explicit policy for the source term ``shortness in the opponent's suit``.

Takeout Double source material requires shortness but does not define an exact
card-count threshold. Objective suit length is supplied to the policy; BridgeLab
ships no default interpretation.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable
from .bidding_rules import BiddingContext, KnowledgeSource
from .models import Suit

class OpponentSuitShortnessStatus(Enum):
    QUALIFIES="qualifies"
    DOES_NOT_QUALIFY="does-not-qualify"
    UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class OpponentSuitShortnessAssessment:
    policy_id: str
    status: OpponentSuitShortnessStatus
    opponent_suit: Suit
    suit_length: int
    explanation: str=""
    sources: tuple[KnowledgeSource,...]=()
    def __post_init__(self):
        if not isinstance(self.policy_id,str): raise TypeError("policy_id must be str")
        pid=self.policy_id.strip()
        if not pid: raise ValueError("policy_id must not be blank")
        object.__setattr__(self,"policy_id",pid)
        if not isinstance(self.status,OpponentSuitShortnessStatus): raise TypeError("status must be OpponentSuitShortnessStatus")
        if not isinstance(self.opponent_suit,Suit): raise TypeError("opponent_suit must be Suit")
        if not isinstance(self.suit_length,int) or not 0<=self.suit_length<=13: raise ValueError("suit_length must be 0..13")
        if not isinstance(self.explanation,str): raise TypeError("explanation must be str")
        if any(not isinstance(x,KnowledgeSource) for x in self.sources): raise TypeError("sources must contain KnowledgeSource values")
        if self.status is not OpponentSuitShortnessStatus.UNKNOWN and (not self.explanation.strip() or not self.sources):
            raise ValueError("known shortness outcomes require explanation and source")

@runtime_checkable
class OpponentSuitShortnessPolicy(Protocol):
    @property
    def policy_id(self)->str: ...
    def assess(self,context:BiddingContext,opponent_suit:Suit,suit_length:int)->OpponentSuitShortnessAssessment: ...

def assess_opponent_suit_shortness(policy,context,opponent_suit,suit_length):
    if not isinstance(context,BiddingContext): raise TypeError("context must be BiddingContext")
    if not isinstance(opponent_suit,Suit): raise TypeError("opponent_suit must be Suit")
    if not isinstance(suit_length,int) or not 0<=suit_length<=13: raise ValueError("suit_length must be 0..13")
    pid=getattr(policy,"policy_id",None)
    if not isinstance(pid,str) or not pid.strip(): raise ValueError("policy must expose nonblank string policy_id")
    result=policy.assess(context,opponent_suit,suit_length)
    if not isinstance(result,OpponentSuitShortnessAssessment): raise TypeError("policy must return OpponentSuitShortnessAssessment")
    if result.policy_id.casefold()!=pid.strip().casefold(): raise ValueError("assessment policy_id must match policy")
    if result.opponent_suit is not opponent_suit or result.suit_length!=suit_length:
        raise ValueError("assessment must preserve opponent suit and objective suit length")
    return result
