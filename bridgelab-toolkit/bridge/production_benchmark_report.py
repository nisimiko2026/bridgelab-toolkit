"""A8.15 consolidated production benchmark report.

Composes already-validated A8 production measurements. It does not change
bidding policy and does not turn frequency into correctness or priority.
"""
from __future__ import annotations

from dataclasses import dataclass

from .production_gap_concentration import (
    ProductionGapConcentrationReport,
    analyze_production_gap_concentration,
)
from .production_gap_evidence import (
    ProductionGapEvidenceReport,
    classify_production_gap_evidence,
)
from .production_replay_cases import (
    RepresentativeReplayReport,
    build_representative_replay_report,
)


@dataclass(frozen=True, slots=True)
class ProductionBenchmarkSummary:
    start_seed: int
    runs: int
    completed: int
    abstained: int
    completion_rate: float
    abstention_rate: float
    production_calls: int
    fixture_calls: int


@dataclass(frozen=True, slots=True)
class ConsolidatedProductionBenchmarkReport:
    summary: ProductionBenchmarkSummary
    concentration: ProductionGapConcentrationReport
    evidence: ProductionGapEvidenceReport
    representatives: RepresentativeReplayReport

    def __post_init__(self):
        counts = {
            self.summary.runs,
            self.concentration.source.runs,
            self.evidence.runs,
            self.representatives.runs,
        }
        if len(counts) != 1:
            raise ValueError("component run counts disagree")
        abstentions = {
            self.summary.abstained,
            self.concentration.abstained,
            self.evidence.abstained,
            self.representatives.abstained,
        }
        if len(abstentions) != 1:
            raise ValueError("component abstention counts disagree")


def build_consolidated_production_benchmark_report(
    *, start_seed: int = 1, count: int = 1000, per_class_limit: int = 5
) -> ConsolidatedProductionBenchmarkReport:
    concentration = analyze_production_gap_concentration(
        start_seed=start_seed, count=count
    )
    evidence = classify_production_gap_evidence(
        start_seed=start_seed, count=count
    )
    representatives = build_representative_replay_report(
        start_seed=start_seed, count=count, per_class_limit=per_class_limit
    )

    # Reuse the validated A8.10 production measurement for headline metrics.
    from .production_scale_benchmark import run_production_scale_benchmark
    scale = run_production_scale_benchmark(start_seed=start_seed, count=count)
    m = scale.coverage.metrics

    completed = scale.completed
    abstained = scale.abstained
    summary = ProductionBenchmarkSummary(
        start_seed=start_seed,
        runs=m.runs,
        completed=completed,
        abstained=abstained,
        completion_rate=0.0 if m.runs == 0 else completed / m.runs,
        abstention_rate=0.0 if m.runs == 0 else abstained / m.runs,
        production_calls=m.production_calls,
        fixture_calls=m.fixture_calls,
    )
    return ConsolidatedProductionBenchmarkReport(
        summary=summary,
        concentration=concentration,
        evidence=evidence,
        representatives=representatives,
    )
