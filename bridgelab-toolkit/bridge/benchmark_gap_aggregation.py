"""Descriptive aggregation of A8 gap-discovery evidence.

A8.8 groups already-discovered items by category and preserves every case/replay
reference. Frequency is evidence of recurrence only; groups are not ranked,
scored, or treated as proof of correctness or repair priority.
"""
from __future__ import annotations
from dataclasses import dataclass

from .benchmark_gap_discovery import GapCategory, GapDiscoveryItem, GapDiscoveryReport


@dataclass(frozen=True, slots=True)
class GapAggregateGroup:
    category: GapCategory
    count: int
    case_ids: tuple[str, ...]
    replay_keys: tuple[str, ...]
    error_types: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.category,GapCategory):
            raise TypeError("category must be GapCategory")
        if not isinstance(self.count,int) or isinstance(self.count,bool) or self.count < 1:
            raise ValueError("count must be a positive integer")
        for name in ("case_ids","replay_keys"):
            values=getattr(self,name)
            if not isinstance(values,tuple) or not all(isinstance(x,str) and x.strip() for x in values):
                raise TypeError(f"{name} must be a tuple of non-blank strings")
            if len(values) != self.count:
                raise ValueError(f"{name} length must equal count")
        if not isinstance(self.error_types,tuple) or not all(isinstance(x,str) and x.strip() for x in self.error_types):
            raise TypeError("error_types must be a tuple of non-blank strings")
        if self.category is GapCategory.EXECUTION_FAILURE:
            if len(self.error_types) != self.count:
                raise ValueError("execution failure error_types length must equal count")
        elif self.error_types:
            raise ValueError("non-failure group cannot contain error_types")


@dataclass(frozen=True, slots=True)
class GapAggregation:
    total_records: int
    total_items: int
    groups: tuple[GapAggregateGroup,...]

    def __post_init__(self):
        for name in ("total_records","total_items"):
            value=getattr(self,name)
            if not isinstance(value,int) or isinstance(value,bool) or value < 0:
                raise ValueError(f"{name} must be non-negative")
        if not isinstance(self.groups,tuple) or not all(isinstance(x,GapAggregateGroup) for x in self.groups):
            raise TypeError("groups must contain GapAggregateGroup")
        if sum(x.count for x in self.groups) != self.total_items:
            raise ValueError("group counts must equal total_items")
        categories=tuple(x.category for x in self.groups)
        if len(set(categories)) != len(categories):
            raise ValueError("group categories must be unique")

    def count(self,category: GapCategory) -> int:
        if not isinstance(category,GapCategory):
            raise TypeError("category must be GapCategory")
        return next((x.count for x in self.groups if x.category is category),0)

    @property
    def review_candidate_count(self) -> int:
        return self.count(GapCategory.POLICY_GAP)+self.count(GapCategory.ENGINE_DEFECT)


def aggregate_gap_discovery(report: GapDiscoveryReport) -> GapAggregation:
    """Group items by category in stable enum order; never frequency-sort them."""
    if not isinstance(report,GapDiscoveryReport):
        raise TypeError("report must be GapDiscoveryReport")

    buckets={category:[] for category in GapCategory}
    for item in report.items:
        buckets[item.category].append(item)

    groups=[]
    for category in GapCategory:
        items=buckets[category]
        if not items:
            continue
        groups.append(GapAggregateGroup(
            category=category,
            count=len(items),
            case_ids=tuple(x.case_id for x in items),
            replay_keys=tuple(x.replay_key for x in items),
            error_types=tuple(x.error_type for x in items) if category is GapCategory.EXECUTION_FAILURE else (),
        ))

    return GapAggregation(
        total_records=report.total_records,
        total_items=len(report.items),
        groups=tuple(groups),
    )
