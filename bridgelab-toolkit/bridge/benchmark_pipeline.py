"""End-to-end orchestration for the A8 benchmark evidence pipeline.

A8.9 composes already-defined A8 stages.  It adds no bidding policy and does
not rank, score, select, or reinterpret evidence.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from .benchmark_batch import BenchmarkBatch
from .benchmark_gap_aggregation import GapAggregation, aggregate_gap_discovery
from .benchmark_gap_discovery import GapDiscoveryReport, discover_benchmark_gaps
from .benchmark_result_record import BenchmarkResultRecord, benchmark_result_record
from .benchmark_runner import BenchmarkRun, run_benchmark_batch
from .benchmark_statistics import BenchmarkStatistics, summarize_benchmark_records

T=TypeVar("T")


@dataclass(frozen=True, slots=True)
class BenchmarkPipelineResult(Generic[T]):
    run: BenchmarkRun[T]
    records: tuple[BenchmarkResultRecord,...]
    statistics: BenchmarkStatistics
    gaps: GapDiscoveryReport
    aggregation: GapAggregation

    def __post_init__(self):
        if not isinstance(self.run,BenchmarkRun):
            raise TypeError("run must be BenchmarkRun")
        if not isinstance(self.records,tuple) or not all(isinstance(x,BenchmarkResultRecord) for x in self.records):
            raise TypeError("records must contain BenchmarkResultRecord")
        if len(self.records) != self.run.batch.case_count:
            raise ValueError("record count must equal batch case count")
        if tuple(x.identity for x in self.records) != self.run.batch.cases:
            raise ValueError("record identities must match batch cases in order")
        if not isinstance(self.statistics,BenchmarkStatistics):
            raise TypeError("statistics must be BenchmarkStatistics")
        if not isinstance(self.gaps,GapDiscoveryReport):
            raise TypeError("gaps must be GapDiscoveryReport")
        if not isinstance(self.aggregation,GapAggregation):
            raise TypeError("aggregation must be GapAggregation")
        if self.statistics.total != len(self.records):
            raise ValueError("statistics total must equal record count")
        if self.gaps.total_records != len(self.records):
            raise ValueError("gap report total must equal record count")
        if self.aggregation.total_records != len(self.records):
            raise ValueError("aggregation total must equal record count")
        if self.aggregation.total_items != len(self.gaps.items):
            raise ValueError("aggregation item total must equal gap item count")


def run_benchmark_pipeline(
    batch: BenchmarkBatch,
    executor: Callable,
) -> BenchmarkPipelineResult:
    """Run A8.4 through A8.8 once over one validated A8.3 batch."""
    run=run_benchmark_batch(batch,executor)
    records=tuple(benchmark_result_record(x) for x in run.executions)
    statistics=summarize_benchmark_records(records)
    gaps=discover_benchmark_gaps(records)
    aggregation=aggregate_gap_discovery(gaps)
    return BenchmarkPipelineResult(run,records,statistics,gaps,aggregation)
