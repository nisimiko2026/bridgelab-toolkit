"""Serializable descriptive report for contract alternative outcomes.

A6.10 — Outcome Comparison Report.

This module presents an A6.9 contract-alternative pipeline result in a stable,
JSON-friendly form. It does not rank alternatives, choose a winner, recommend
a contract, or modify bidding policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contract_alternative_evaluation import (
    ContractAlternativeEvaluationPipelineResult,
)


@dataclass(frozen=True, slots=True)
class OutcomeComparisonReportRow:
    alternative_id: str
    contract: str
    declarer: str
    vulnerability: str
    sample_count: int
    mean_declarer_score: float
    median_declarer_score: float
    mean_ns_score: float
    median_ns_score: float
    make_probability: float
    down_probability: float
    min_declarer_score: int
    max_declarer_score: int
    min_ns_score: int
    max_ns_score: int

    def as_dict(self) -> dict[str, object]:
        return {
            "alternative_id": self.alternative_id,
            "contract": self.contract,
            "declarer": self.declarer,
            "vulnerability": self.vulnerability,
            "sample_count": self.sample_count,
            "mean_declarer_score": self.mean_declarer_score,
            "median_declarer_score": self.median_declarer_score,
            "mean_ns_score": self.mean_ns_score,
            "median_ns_score": self.median_ns_score,
            "make_probability": self.make_probability,
            "down_probability": self.down_probability,
            "min_declarer_score": self.min_declarer_score,
            "max_declarer_score": self.max_declarer_score,
            "min_ns_score": self.min_ns_score,
            "max_ns_score": self.max_ns_score,
        }


@dataclass(frozen=True, slots=True)
class OutcomeComparisonReport:
    rows: tuple[OutcomeComparisonReportRow, ...]
    min_sample_count: int
    max_sample_count: int
    equal_sample_counts: bool

    @property
    def total(self) -> int:
        return len(self.rows)

    def row(self, alternative_id: str) -> OutcomeComparisonReportRow:
        for item in self.rows:
            if item.alternative_id == alternative_id:
                return item
        raise KeyError(alternative_id)

    def as_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "min_sample_count": self.min_sample_count,
            "max_sample_count": self.max_sample_count,
            "equal_sample_counts": self.equal_sample_counts,
            "rows": [row.as_dict() for row in self.rows],
        }


def _contract_text(contract) -> str:
    return contract.bid.serialize() + contract.doubling.value


def build_outcome_comparison_report(
    result: ContractAlternativeEvaluationPipelineResult,
) -> OutcomeComparisonReport:
    """Build a passive serializable report from an A6.9 pipeline result."""
    if not isinstance(result, ContractAlternativeEvaluationPipelineResult):
        raise TypeError(
            "result must be ContractAlternativeEvaluationPipelineResult"
        )

    comparison_rows = {
        row.alternative_id: row
        for row in result.comparison.rows
    }

    rows = []
    for evaluation in result.evaluations:
        summary = evaluation.summary
        comparison = comparison_rows[evaluation.alternative_id]
        rows.append(
            OutcomeComparisonReportRow(
                alternative_id=evaluation.alternative_id,
                contract=_contract_text(summary.contract),
                declarer=summary.contract.declarer.value,
                vulnerability=summary.vulnerability.value,
                sample_count=summary.sample_count,
                mean_declarer_score=summary.mean_declarer_score,
                median_declarer_score=summary.median_declarer_score,
                mean_ns_score=summary.mean_ns_score,
                median_ns_score=summary.median_ns_score,
                make_probability=summary.make_probability,
                down_probability=summary.down_probability,
                min_declarer_score=summary.min_declarer_score,
                max_declarer_score=summary.max_declarer_score,
                min_ns_score=comparison.min_ns_score,
                max_ns_score=comparison.max_ns_score,
            )
        )

    return OutcomeComparisonReport(
        rows=tuple(rows),
        min_sample_count=result.comparison.min_sample_count,
        max_sample_count=result.comparison.max_sample_count,
        equal_sample_counts=result.comparison.equal_sample_counts,
    )
