"""A8.10 production-scale SAYC benchmark adapter.

Runs the existing production SAYC coverage benchmark and exposes a compact,
replay-preserving scale report. It does not reinterpret abstention as failure
or install any missing bidding policy.
"""
from __future__ import annotations
from dataclasses import dataclass

from .sayc_coverage_benchmark import SaycCoverageBenchmarkReport, run_sayc_coverage_benchmark


@dataclass(frozen=True, slots=True)
class ProductionScaleBenchmarkReport:
    start_seed: int
    count: int
    coverage: SaycCoverageBenchmarkReport
    replay_records: tuple[object, ...]

    def __post_init__(self):
        if not isinstance(self.start_seed,int) or isinstance(self.start_seed,bool):
            raise TypeError("start_seed must be an integer")
        if not isinstance(self.count,int) or isinstance(self.count,bool) or self.count < 0:
            raise ValueError("count must be a non-negative integer")
        if not isinstance(self.coverage,SaycCoverageBenchmarkReport):
            raise TypeError("coverage must be SaycCoverageBenchmarkReport")
        if not isinstance(self.replay_records,tuple):
            raise TypeError("replay_records must be a tuple")
        if self.coverage.metrics.runs != self.count:
            raise ValueError("coverage run count must equal count")
        if len(self.replay_records) != self.count:
            raise ValueError("replay record count must equal count")

    @property
    def completed(self) -> int:
        return self.coverage.metrics.completed

    @property
    def abstained(self) -> int:
        return self.coverage.metrics.abstained

    @property
    def opening_rate(self) -> float:
        return self.coverage.metrics.opening_rate

    @property
    def responder_bid_rate(self) -> float:
        return self.coverage.metrics.responder_bid_rate

    @property
    def opener_rebid_rate(self) -> float:
        return self.coverage.metrics.opener_rebid_rate


def run_production_scale_benchmark(*,start_seed:int=1,count:int=1000) -> ProductionScaleBenchmarkReport:
    """Run the current production SAYC benchmark with exact replay records."""
    if not isinstance(start_seed,int) or isinstance(start_seed,bool):
        raise TypeError("start_seed must be an integer")
    if not isinstance(count,int) or isinstance(count,bool):
        raise TypeError("count must be an integer")
    if count < 0:
        raise ValueError("count must be non-negative")

    coverage=run_sayc_coverage_benchmark(start_seed=start_seed,count=count)
    replay_records=tuple(coverage.batch.replay_records)
    return ProductionScaleBenchmarkReport(start_seed,count,coverage,replay_records)
