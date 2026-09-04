"""Explicit source-role policy for Advancer strength after a Takeout Double.

Frozen source distinguishes minimum, invitational and strong hands but gives no
numeric boundaries. BridgeLab therefore ships no default classifier.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol,runtime_checkable
from .bidding_rules import BiddingContext,KnowledgeSource

class TakeoutAdvancerStrengthClass(Enum):
    MINIMUM="minimum"
    INVITATIONAL="invitational"
    STRONG="strong"
    UNKNOWN="unknown"

@dataclass(frozen=True,slots=True)
class TakeoutAdvancerStrengthAssessment:
    policy_id:str
    strength_class:TakeoutAdvancerStrengthClass
    explanation:str=""
    sources:tuple[KnowledgeSource,...]=()
    def __post_init__(self):
        if not isinstance(self.policy_id,str): raise TypeError("policy_id must be str")
        pid=self.policy_id.strip()
        if not pid: raise ValueError("policy_id must not be blank")
        object.__setattr__(self,"policy_id",pid)
        if not isinstance(self.strength_class,TakeoutAdvancerStrengthClass):
            raise TypeError("strength_class must be TakeoutAdvancerStrengthClass")
        if not isinstance(self.explanation,str): raise TypeError("explanation must be str")
        if any(not isinstance(x,KnowledgeSource) for x in self.sources):
            raise TypeError("sources must contain KnowledgeSource values")
        if self.strength_class is not TakeoutAdvancerStrengthClass.UNKNOWN and (not self.explanation.strip() or not self.sources):
            raise ValueError("known strength classifications require explanation and source")

@runtime_checkable
class TakeoutAdvancerStrengthPolicy(Protocol):
    @property
    def policy_id(self)->str: ...
    def assess(self,context:BiddingContext)->TakeoutAdvancerStrengthAssessment: ...

def assess_takeout_advancer_strength(policy,context):
    if not isinstance(context,BiddingContext): raise TypeError("context must be BiddingContext")
    pid=getattr(policy,"policy_id",None)
    if not isinstance(pid,str) or not pid.strip(): raise ValueError("policy must expose nonblank string policy_id")
    result=policy.assess(context)
    if not isinstance(result,TakeoutAdvancerStrengthAssessment):
        raise TypeError("policy must return TakeoutAdvancerStrengthAssessment")
    if result.policy_id.casefold()!=pid.strip().casefold():
        raise ValueError("assessment policy_id must match policy")
    return result
