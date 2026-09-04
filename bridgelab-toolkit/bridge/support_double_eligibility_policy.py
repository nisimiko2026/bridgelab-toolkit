"""Explicit source-role policy for unresolved Support Double eligibility.

Frozen source supplies objective three-card support, but leaves opening-values,
"no more descriptive natural rebid", and convention range partly qualitative or
partnership-dependent. BridgeLab therefore ships no default eligibility policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable
from .bidding_rules import BiddingContext, KnowledgeSource

class SupportDoubleEligibilityStatus(Enum):
    QUALIFIES="qualifies"
    DOES_NOT_QUALIFY="does-not-qualify"
    UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class SupportDoubleEligibilityAssessment:
    policy_id:str
    status:SupportDoubleEligibilityStatus
    explanation:str=""
    sources:tuple[KnowledgeSource,...]=()
    def __post_init__(self):
        if not isinstance(self.policy_id,str): raise TypeError("policy_id must be str")
        pid=self.policy_id.strip()
        if not pid: raise ValueError("policy_id must not be blank")
        object.__setattr__(self,"policy_id",pid)
        if not isinstance(self.status,SupportDoubleEligibilityStatus): raise TypeError("status must be SupportDoubleEligibilityStatus")
        if not isinstance(self.explanation,str): raise TypeError("explanation must be str")
        if any(not isinstance(x,KnowledgeSource) for x in self.sources): raise TypeError("sources must contain KnowledgeSource values")
        if self.status is not SupportDoubleEligibilityStatus.UNKNOWN and (not self.explanation.strip() or not self.sources):
            raise ValueError("known eligibility outcomes require explanation and source")

@runtime_checkable
class SupportDoubleEligibilityPolicy(Protocol):
    @property
    def policy_id(self)->str: ...
    def assess(self,context:BiddingContext)->SupportDoubleEligibilityAssessment: ...

def assess_support_double_eligibility(policy,context):
    if not isinstance(context,BiddingContext): raise TypeError("context must be BiddingContext")
    pid=getattr(policy,"policy_id",None)
    if not isinstance(pid,str) or not pid.strip(): raise ValueError("policy must expose nonblank string policy_id")
    result=policy.assess(context)
    if not isinstance(result,SupportDoubleEligibilityAssessment): raise TypeError("policy must return SupportDoubleEligibilityAssessment")
    if result.policy_id.casefold()!=pid.strip().casefold(): raise ValueError("assessment policy_id must match policy")
    return result
