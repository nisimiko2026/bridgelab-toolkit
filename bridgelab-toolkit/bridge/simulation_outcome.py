"""Aggregate duplicate-bridge outcomes across simulation samples.

A6.5 — Simulation Outcome Evaluation.

Each sample is scored independently before aggregation. This module never
scores an average trick count and does not define or modify bidding policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable

from .auction import Contract
from .corpus import Vulnerability
from .outcome_scoring import ContractOutcome, score_contract_outcome


@dataclass(frozen=True, slots=True)
class SimulationOutcomeSummary:
    contract: Contract
    vulnerability: Vulnerability
    sample_count: int
    mean_declarer_score: float
    median_declarer_score: float
    mean_ns_score: float
    median_ns_score: float
    make_count: int
    down_count: int
    make_probability: float
    down_probability: float
    min_declarer_score: int
    max_declarer_score: int
    outcomes: tuple[ContractOutcome, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.contract, Contract):
            raise TypeError("contract must be Contract")
        if not isinstance(self.vulnerability, Vulnerability):
            raise TypeError("vulnerability must be Vulnerability")
        if not isinstance(self.sample_count, int) or isinstance(self.sample_count, bool):
            raise TypeError("sample_count must be an integer")
        if self.sample_count <= 0:
            raise ValueError("sample_count must be positive")
        if len(self.outcomes) != self.sample_count:
            raise ValueError("sample_count must match outcomes")
        if self.make_count + self.down_count != self.sample_count:
            raise ValueError("make_count + down_count must equal sample_count")

    @property
    def contract_probability(self) -> float:
        """Alias for make_probability."""
        return self.make_probability


def summarize_simulation_outcomes(
    *,
    contract: Contract,
    vulnerability: Vulnerability,
    declarer_tricks: Iterable[int],
) -> SimulationOutcomeSummary:
    """Score every simulated trick result, then aggregate the scores."""
    if not isinstance(contract, Contract):
        raise TypeError("contract must be Contract")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("vulnerability must be Vulnerability")

    try:
        trick_samples = tuple(declarer_tricks)
    except TypeError as exc:
        raise TypeError("declarer_tricks must be an iterable of integers") from exc

    if not trick_samples:
        raise ValueError("simulation requires at least one sample")

    outcomes = tuple(
        score_contract_outcome(contract, tricks, vulnerability)
        for tricks in trick_samples
    )

    declarer_scores = tuple(outcome.declarer_score for outcome in outcomes)
    ns_scores = tuple(outcome.ns_score for outcome in outcomes)
    sample_count = len(outcomes)
    make_count = sum(outcome.made for outcome in outcomes)
    down_count = sample_count - make_count

    return SimulationOutcomeSummary(
        contract=contract,
        vulnerability=vulnerability,
        sample_count=sample_count,
        mean_declarer_score=sum(declarer_scores) / sample_count,
        median_declarer_score=float(median(declarer_scores)),
        mean_ns_score=sum(ns_scores) / sample_count,
        median_ns_score=float(median(ns_scores)),
        make_count=make_count,
        down_count=down_count,
        make_probability=make_count / sample_count,
        down_probability=down_count / sample_count,
        min_declarer_score=min(declarer_scores),
        max_declarer_score=max(declarer_scores),
        outcomes=outcomes,
    )
