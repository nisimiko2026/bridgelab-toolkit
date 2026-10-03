"""Conservative gap-discovery view over A8 benchmark result records.

A8.7 maps already-classified disagreement evidence into engineering review
categories.  It does not reclassify bridge semantics, infer correctness, or
promote every disagreement into a BridgeLab defect.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from .benchmark_result_record import BenchmarkResultRecord
from .benchmark_runner import BenchmarkExecutionStatus
from .decision_evidence import DisagreementKind


class GapCategory(str, Enum):
    POLICY_GAP = "policy-gap"
    ENGINE_DEFECT = "engine-defect"
    SYSTEM_DIFFERENCE = "system-difference"
    CONVENTION_DIFFERENCE = "convention-difference"
    TREATMENT_DIFFERENCE = "treatment-difference"
    PARTNERSHIP_AGREEMENT = "partnership-agreement"
    JUDGMENT_DIFFERENCE = "judgment-difference"
    BRIDGELAB_ABSTENTION = "bridgelab-abstention"
    EXTERNAL_ABSTENTION = "external-abstention"
    UNKNOWN_EXTERNAL_SYSTEM = "unknown-external-system"
    EXECUTION_FAILURE = "execution-failure"


_KIND_TO_CATEGORY = {
    DisagreementKind.POSSIBLE_POLICY_GAP: GapCategory.POLICY_GAP,
    DisagreementKind.POSSIBLE_ENGINE_DEFECT: GapCategory.ENGINE_DEFECT,
    DisagreementKind.SYSTEM_DIFFERENCE: GapCategory.SYSTEM_DIFFERENCE,
    DisagreementKind.CONVENTION_DIFFERENCE: GapCategory.CONVENTION_DIFFERENCE,
    DisagreementKind.TREATMENT_DIFFERENCE: GapCategory.TREATMENT_DIFFERENCE,
    DisagreementKind.PARTNERSHIP_AGREEMENT: GapCategory.PARTNERSHIP_AGREEMENT,
    DisagreementKind.JUDGMENT_DIFFERENCE: GapCategory.JUDGMENT_DIFFERENCE,
    DisagreementKind.BRIDGELAB_ABSTAIN: GapCategory.BRIDGELAB_ABSTENTION,
    DisagreementKind.EXTERNAL_MODEL_ABSTAIN: GapCategory.EXTERNAL_ABSTENTION,
    DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM: GapCategory.UNKNOWN_EXTERNAL_SYSTEM,
}


@dataclass(frozen=True, slots=True)
class GapDiscoveryItem:
    case_id: str
    replay_key: str
    category: GapCategory
    source_kind: DisagreementKind | None = None
    error_type: str | None = None

    def __post_init__(self):
        for name in ("case_id","replay_key"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip():
                raise ValueError(f"{name} must be non-blank")
        if not isinstance(self.category,GapCategory):
            raise TypeError("category must be GapCategory")
        if self.source_kind is not None and not isinstance(self.source_kind,DisagreementKind):
            raise TypeError("source_kind must be DisagreementKind or None")
        if self.category is GapCategory.EXECUTION_FAILURE:
            if self.source_kind is not None:
                raise ValueError("execution failure cannot have source_kind")
            if not isinstance(self.error_type,str) or not self.error_type.strip():
                raise ValueError("execution failure requires error_type")
        elif self.error_type is not None:
            raise ValueError("non-failure gap item cannot have error_type")


@dataclass(frozen=True, slots=True)
class GapDiscoveryReport:
    total_records: int
    items: tuple[GapDiscoveryItem,...]

    def __post_init__(self):
        if not isinstance(self.total_records,int) or isinstance(self.total_records,bool) or self.total_records < 0:
            raise ValueError("total_records must be non-negative")
        if not isinstance(self.items,tuple) or not all(isinstance(x,GapDiscoveryItem) for x in self.items):
            raise TypeError("items must contain GapDiscoveryItem")

    def count(self,category: GapCategory) -> int:
        if not isinstance(category,GapCategory):
            raise TypeError("category must be GapCategory")
        return sum(x.category is category for x in self.items)

    @property
    def review_candidate_count(self) -> int:
        return self.count(GapCategory.POLICY_GAP)+self.count(GapCategory.ENGINE_DEFECT)


def discover_benchmark_gaps(records: tuple[BenchmarkResultRecord,...]) -> GapDiscoveryReport:
    """Expose existing classifications as review categories; AGREEMENT is omitted."""
    if not isinstance(records,tuple):
        raise TypeError("records must be a tuple")
    if not all(isinstance(x,BenchmarkResultRecord) for x in records):
        raise TypeError("records must contain BenchmarkResultRecord")

    items=[]
    for record in records:
        if record.execution_status is BenchmarkExecutionStatus.FAILED:
            items.append(GapDiscoveryItem(
                case_id=record.identity.case_id,
                replay_key=record.identity.replay_key,
                category=GapCategory.EXECUTION_FAILURE,
                error_type=record.error_type,
            ))
            continue

        for kind in record.disagreements:
            if kind is DisagreementKind.AGREEMENT:
                continue
            category=_KIND_TO_CATEGORY.get(kind)
            if category is None:
                raise ValueError(f"unsupported disagreement kind: {kind}")
            items.append(GapDiscoveryItem(
                case_id=record.identity.case_id,
                replay_key=record.identity.replay_key,
                category=category,
                source_kind=kind,
            ))

    return GapDiscoveryReport(total_records=len(records),items=tuple(items))
