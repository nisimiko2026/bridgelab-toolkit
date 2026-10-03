"""Descriptive aggregation for normalized A8 benchmark records.

A8.6 summarizes existing records only.  It does not rerun cases, reclassify
disagreements, infer correctness, rank providers, or modify policy.
"""
from __future__ import annotations
from dataclasses import dataclass

from .benchmark_result_record import BenchmarkResultRecord
from .benchmark_runner import BenchmarkExecutionStatus
from .capability_providers import ProviderStatus
from .decision_evidence import DisagreementKind


@dataclass(frozen=True, slots=True)
class ProviderStatusCount:
    provider_id: str
    status: ProviderStatus
    count: int

    def __post_init__(self):
        if not isinstance(self.provider_id,str) or not self.provider_id.strip():
            raise ValueError("provider_id must be non-blank")
        if not isinstance(self.status,ProviderStatus):
            raise TypeError("status must be ProviderStatus")
        if not isinstance(self.count,int) or isinstance(self.count,bool) or self.count < 1:
            raise ValueError("count must be a positive integer")


@dataclass(frozen=True, slots=True)
class BenchmarkStatistics:
    total: int
    completed: int
    failed: int
    bridgelab_observed: int
    bridgelab_recommended: int
    bridgelab_abstained: int
    bridgelab_other_status: int
    provider_status_counts: tuple[ProviderStatusCount,...]
    disagreement_counts: tuple[tuple[DisagreementKind,int],...]

    def __post_init__(self):
        for name in ("total","completed","failed","bridgelab_observed","bridgelab_recommended","bridgelab_abstained","bridgelab_other_status"):
            v=getattr(self,name)
            if not isinstance(v,int) or isinstance(v,bool) or v < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.completed + self.failed != self.total:
            raise ValueError("completed plus failed must equal total")
        if self.bridgelab_recommended + self.bridgelab_abstained + self.bridgelab_other_status != self.bridgelab_observed:
            raise ValueError("BridgeLab status counts must equal bridgelab_observed")
        if not isinstance(self.provider_status_counts,tuple) or not all(isinstance(x,ProviderStatusCount) for x in self.provider_status_counts):
            raise TypeError("provider_status_counts must contain ProviderStatusCount")
        if not isinstance(self.disagreement_counts,tuple):
            raise TypeError("disagreement_counts must be a tuple")
        seen=set()
        for kind,count in self.disagreement_counts:
            if not isinstance(kind,DisagreementKind):
                raise TypeError("disagreement key must be DisagreementKind")
            if kind in seen:
                raise ValueError("duplicate disagreement kind")
            seen.add(kind)
            if not isinstance(count,int) or isinstance(count,bool) or count < 0:
                raise ValueError("disagreement count must be non-negative")

    def disagreement_count(self,kind: DisagreementKind) -> int:
        if not isinstance(kind,DisagreementKind):
            raise TypeError("kind must be DisagreementKind")
        return next((n for k,n in self.disagreement_counts if k is kind),0)

    def provider_count(self,provider_id: str,status: ProviderStatus) -> int:
        if not isinstance(provider_id,str) or not provider_id.strip():
            raise ValueError("provider_id must be non-blank")
        if not isinstance(status,ProviderStatus):
            raise TypeError("status must be ProviderStatus")
        key=provider_id.casefold()
        return sum(x.count for x in self.provider_status_counts if x.provider_id.casefold()==key and x.status is status)

    @property
    def execution_success_rate(self) -> float:
        return 0.0 if self.total==0 else self.completed/self.total

    @property
    def bridgelab_coverage_rate(self) -> float:
        return 0.0 if self.bridgelab_observed==0 else self.bridgelab_recommended/self.bridgelab_observed

    @property
    def bridgelab_abstention_rate(self) -> float:
        return 0.0 if self.bridgelab_observed==0 else self.bridgelab_abstained/self.bridgelab_observed


def summarize_benchmark_records(records: tuple[BenchmarkResultRecord,...]) -> BenchmarkStatistics:
    """Aggregate records exactly as stored, without semantic reinterpretation."""
    if not isinstance(records,tuple):
        raise TypeError("records must be a tuple")
    if not all(isinstance(x,BenchmarkResultRecord) for x in records):
        raise TypeError("records must contain BenchmarkResultRecord")

    completed=sum(x.execution_status is BenchmarkExecutionStatus.COMPLETED for x in records)
    failed=len(records)-completed
    observed=recommended=abstained=other=0
    provider_counts={}
    disagreement_counts={kind:0 for kind in DisagreementKind}

    for record in records:
        if record.execution_status is BenchmarkExecutionStatus.FAILED:
            continue
        if record.bridgelab is not None:
            observed += 1
            if record.bridgelab.has_recommendation:
                recommended += 1
            elif record.bridgelab.status is ProviderStatus.ABSTAIN:
                abstained += 1
            else:
                other += 1

        for provider in record.external:
            key=(provider.provider_id,provider.status)
            provider_counts[key]=provider_counts.get(key,0)+1

        for kind in record.disagreements:
            disagreement_counts[kind] += 1

    status_rows=tuple(
        ProviderStatusCount(provider_id,status,count)
        for (provider_id,status),count in sorted(
            provider_counts.items(),key=lambda x:(x[0][0].casefold(),x[0][1].value)
        )
    )
    disagreement_rows=tuple((kind,disagreement_counts[kind]) for kind in DisagreementKind)

    return BenchmarkStatistics(
        total=len(records),completed=completed,failed=failed,
        bridgelab_observed=observed,bridgelab_recommended=recommended,
        bridgelab_abstained=abstained,bridgelab_other_status=other,
        provider_status_counts=status_rows,disagreement_counts=disagreement_rows,
    )
