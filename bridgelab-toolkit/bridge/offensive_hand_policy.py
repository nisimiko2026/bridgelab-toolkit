"""Explicit policy for the source term ``offensive hand``.

Weak Jump Overcall material uses this qualitative term without an executable
formula. BridgeLab therefore requires an application/partnership policy and
ships no default definition.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable
from .bidding_rules import BiddingContext, KnowledgeSource

class OffensiveHandStatus(Enum):
    QUALIFIES="qualifies"
    DOES_NOT_QUALIFY="does-not-qualify"
    UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class OffensiveHandAssessment:
    policy_id: str
    status: OffensiveHandStatus
    explanation: str=""
    sources: tuple[KnowledgeSource,...]=()
    def __post_init__(self):
        if not isinstance(self.policy_id,str): raise TypeError("policy_id must be str")
        pid=self.policy_id.strip()
        if not pid: raise ValueError("policy_id must not be blank")
        object.__setattr__(self,"policy_id",pid)
        if not isinstance(self.status,OffensiveHandStatus): raise TypeError("status must be OffensiveHandStatus")
        if not isinstance(self.explanation,str): raise TypeError("explanation must be str")
        if any(not isinstance(x,KnowledgeSource) for x in self.sources): raise TypeError("sources must contain KnowledgeSource values")
        if self.status is not OffensiveHandStatus.UNKNOWN and (not self.explanation.strip() or not self.sources):
            raise ValueError("known offensive-hand outcomes require explanation and source")
    @classmethod
    def unknown(cls,policy_id,explanation="",sources=()): return cls(policy_id,OffensiveHandStatus.UNKNOWN,explanation,sources)
    @classmethod
    def qualifies(cls,policy_id,explanation,sources): return cls(policy_id,OffensiveHandStatus.QUALIFIES,explanation,sources)
    @classmethod
    def does_not_qualify(cls,policy_id,explanation,sources): return cls(policy_id,OffensiveHandStatus.DOES_NOT_QUALIFY,explanation,sources)
    @property
    def is_known(self): return self.status is not OffensiveHandStatus.UNKNOWN
    @property
    def qualifies_offense(self):
        return None if self.status is OffensiveHandStatus.UNKNOWN else self.status is OffensiveHandStatus.QUALIFIES

@runtime_checkable
class OffensiveHandPolicy(Protocol):
    @property
    def policy_id(self)->str: ...
    def assess(self,context:BiddingContext)->OffensiveHandAssessment: ...

def assess_offensive_hand(policy:OffensiveHandPolicy,context:BiddingContext)->OffensiveHandAssessment:
    if not isinstance(context,BiddingContext): raise TypeError("context must be BiddingContext")
    pid=getattr(policy,"policy_id",None)
    if not isinstance(pid,str): raise TypeError("policy must expose string policy_id")
    pid=pid.strip()
    if not pid: raise ValueError("policy_id must not be blank")
    result=policy.assess(context)
    if not isinstance(result,OffensiveHandAssessment): raise TypeError("policy must return OffensiveHandAssessment")
    if result.policy_id.casefold()!=pid.casefold(): raise ValueError("assessment policy_id must match policy")
    return result
