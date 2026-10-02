"""Descriptive comparison of simulated bridge outcome alternatives.

A6.6 — Alternative Outcome Comparison.

This module compares measured simulation summaries from a fixed NS perspective.
It does not choose a bid, declare a policy winner, infer correctness, or modify
any system, convention, treatment, or partnership agreement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .simulation_outcome import SimulationOutcomeSummary


@dataclass(frozen=True, slots=True)
class OutcomeAlternative:
    alternative_id: str
    summary: SimulationOutcomeSummary

    def __post_init__(self) -> None:
        if not isinstance(self.alternative_id, str) or not self.alternative_id.strip():
            raise ValueError("alternative_id must be a non-blank string")
        if not isinstance(self.summary, SimulationOutcomeSummary):
            raise TypeError("summary must be SimulationOutcomeSummary")


@dataclass(frozen=True, slots=True)
class AlternativeOutcomeRow:
    alternative_id: str
    sample_count: int
    mean_ns_score: float
    median_ns_score: float
    make_probability: float
    down_probability: float
    min_ns_score: int
    max_ns_score: int


@dataclass(frozen=True, slots=True)
class AlternativeOutcomeComparison:
    rows: tuple[AlternativeOutcomeRow, ...]
    min_sample_count: int
    max_sample_count: int
    equal_sample_counts: bool

    def __post_init__(self) -> None:
        if len(self.rows) < 2:
            raise ValueError("comparison requires at least two alternatives")
        ids = tuple(row.alternative_id for row in self.rows)
        if len(set(ids)) != len(ids):
            raise ValueError("alternative_id values must be unique")

    def row(self, alternative_id: str) -> AlternativeOutcomeRow:
        for row in self.rows:
            if row.alternative_id == alternative_id:
                return row
        raise KeyError(alternative_id)


def compare_simulation_outcomes(
    alternatives: Iterable[OutcomeAlternative],
) -> AlternativeOutcomeComparison:
    """Create a stable, descriptive comparison without ranking alternatives."""
    try:
        items = tuple(alternatives)
    except TypeError as exc:
        raise TypeError("alternatives must be an iterable") from exc

    if len(items) < 2:
        raise ValueError("comparison requires at least two alternatives")
    if not all(isinstance(item, OutcomeAlternative) for item in items):
        raise TypeError("all alternatives must be OutcomeAlternative")

    ids = tuple(item.alternative_id for item in items)
    if len(set(ids)) != len(ids):
        raise ValueError("alternative_id values must be unique")

    rows = []
    for item in items:
        summary = item.summary
        ns_scores = tuple(outcome.ns_score for outcome in summary.outcomes)
        rows.append(
            AlternativeOutcomeRow(
                alternative_id=item.alternative_id,
                sample_count=summary.sample_count,
                mean_ns_score=summary.mean_ns_score,
                median_ns_score=summary.median_ns_score,
                make_probability=summary.make_probability,
                down_probability=summary.down_probability,
                min_ns_score=min(ns_scores),
                max_ns_score=max(ns_scores),
            )
        )

    counts = tuple(row.sample_count for row in rows)
    return AlternativeOutcomeComparison(
        rows=tuple(rows),
        min_sample_count=min(counts),
        max_sample_count=max(counts),
        equal_sample_counts=len(set(counts)) == 1,
    )
