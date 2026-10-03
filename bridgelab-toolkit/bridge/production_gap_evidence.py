"""A8.13 evidence classification for production abstentions.

Classification is conservative. Mechanical evidence is not silently promoted
to a policy gap or engine defect.  Opening Pass candidates are intentionally
left for source/policy review because current production rules do not emit an
opening Pass recommendation.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .abstention_diagnostics import AbstentionReason
from .production_gap_extraction import ProductionAbstentionCase, extract_production_abstentions

class EvidenceClass(str, Enum):
    MISSING_ROUTE = "missing-route"
    ROUTED_RULE_REJECTION = "routed-rule-rejection"
    OPENING_PASS_REVIEW = "opening-pass-review"

@dataclass(frozen=True, slots=True)
class ClassifiedAbstention:
    case: ProductionAbstentionCase
    evidence_class: EvidenceClass
    basis: str

@dataclass(frozen=True, slots=True)
class EvidenceClassGroup:
    evidence_class: EvidenceClass
    count: int
    share_of_abstentions: float
    seeds: tuple[int, ...]

@dataclass(frozen=True, slots=True)
class ProductionGapEvidenceReport:
    runs: int
    completed: int
    abstained: int
    cases: tuple[ClassifiedAbstention, ...]
    groups: tuple[EvidenceClassGroup, ...]

    def count(self, evidence_class: EvidenceClass) -> int:
        return next((g.count for g in self.groups if g.evidence_class is evidence_class), 0)

def _classify(case: ProductionAbstentionCase) -> ClassifiedAbstention:
    d=case.diagnostic
    if d.reason is AbstentionReason.NO_ROUTE:
        return ClassifiedAbstention(case,EvidenceClass.MISSING_ROUTE,
            "No configured production route owns the exact auction.")
    if case.depth == 0 and d.route_id == "sayc.opening":
        return ClassifiedAbstention(case,EvidenceClass.OPENING_PASS_REVIEW,
            "Opening route exists but no rule recommends a call; current evidence does not prove whether Pass or another treatment is required.")
    return ClassifiedAbstention(case,EvidenceClass.ROUTED_RULE_REJECTION,
        "A production route exists, but none of its current rules recommends a call.")

def classify_production_gap_evidence(*,start_seed:int=1,count:int=1000)->ProductionGapEvidenceReport:
    source=extract_production_abstentions(start_seed=start_seed,count=count)
    cases=tuple(_classify(x) for x in source.cases)
    buckets={e:[] for e in EvidenceClass}
    for x in cases: buckets[x.evidence_class].append(x.case.seed)
    total=len(cases)
    groups=tuple(EvidenceClassGroup(e,len(buckets[e]),0.0 if total==0 else len(buckets[e])/total,tuple(buckets[e]))
                 for e in EvidenceClass if buckets[e])
    assert sum(g.count for g in groups)==source.abstained
    return ProductionGapEvidenceReport(source.runs,source.completed,source.abstained,cases,groups)
