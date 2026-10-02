"""Evaluate and compare multiple contract alternatives.

A6.9 — Contract Alternative Evaluation Pipeline.

This module composes existing simulation outcome scoring and descriptive
comparison. It preserves caller order and never selects, ranks, or promotes
an alternative into bidding policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping

from .alternative_outcome_comparison import (
    AlternativeOutcomeComparison, OutcomeAlternative, compare_simulation_outcomes,
)
from .auction import Contract
from .corpus import Vulnerability
from .deals import Deal
from .simulation_outcome import SimulationOutcomeSummary, summarize_simulation_outcomes


@dataclass(frozen=True, slots=True)
class ContractAlternative:
    alternative_id: str
    contract: Contract

    def __post_init__(self) -> None:
        if not isinstance(self.alternative_id, str) or not self.alternative_id.strip():
            raise ValueError("alternative_id must be a non-blank string")
        object.__setattr__(self, "alternative_id", self.alternative_id.strip())
        if not isinstance(self.contract, Contract):
            raise TypeError("contract must be Contract")


@dataclass(frozen=True, slots=True)
class ContractAlternativeEvaluation:
    alternative_id: str
    summary: SimulationOutcomeSummary

    def __post_init__(self) -> None:
        if not isinstance(self.alternative_id, str) or not self.alternative_id.strip():
            raise ValueError("alternative_id must be a non-blank string")
        object.__setattr__(self, "alternative_id", self.alternative_id.strip())
        if not isinstance(self.summary, SimulationOutcomeSummary):
            raise TypeError("summary must be SimulationOutcomeSummary")


@dataclass(frozen=True, slots=True)
class ContractAlternativeEvaluationPipelineResult:
    evaluations: tuple[ContractAlternativeEvaluation, ...]
    comparison: AlternativeOutcomeComparison

    def __post_init__(self) -> None:
        if len(self.evaluations) < 2:
            raise ValueError("pipeline result requires at least two alternatives")
        ids = tuple(item.alternative_id for item in self.evaluations)
        if len(set(ids)) != len(ids):
            raise ValueError("alternative_id values must be unique")
        if tuple(row.alternative_id for row in self.comparison.rows) != ids:
            raise ValueError("comparison rows must match evaluation order")

    def evaluation(self, alternative_id: str) -> ContractAlternativeEvaluation:
        for item in self.evaluations:
            if item.alternative_id == alternative_id:
                return item
        raise KeyError(alternative_id)


def evaluate_contract_alternatives(
    *,
    deal: Deal,
    vulnerability: Vulnerability,
    alternatives: Iterable[ContractAlternative],
    declarer_tricks: Mapping[str, Iterable[int]],
) -> ContractAlternativeEvaluationPipelineResult:
    """Score every supplied trick sample, aggregate, then compare alternatives."""
    if not isinstance(deal, Deal):
        raise TypeError("deal must be Deal")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("vulnerability must be Vulnerability")

    try:
        items = tuple(alternatives)
    except TypeError as exc:
        raise TypeError("alternatives must be an iterable") from exc

    if len(items) < 2:
        raise ValueError("pipeline requires at least two alternatives")
    if not all(isinstance(item, ContractAlternative) for item in items):
        raise TypeError("all alternatives must be ContractAlternative")

    ids = tuple(item.alternative_id for item in items)
    if len(set(ids)) != len(ids):
        raise ValueError("alternative_id values must be unique")

    if not isinstance(declarer_tricks, Mapping):
        raise TypeError("declarer_tricks must be a mapping")

    expected, supplied = set(ids), set(declarer_tricks)
    missing, extra = expected - supplied, supplied - expected
    if missing:
        raise ValueError("missing declarer-trick samples for: " + ", ".join(sorted(missing)))
    if extra:
        raise ValueError("unexpected declarer-trick samples for: " + ", ".join(sorted(extra)))

    evaluations = tuple(
        ContractAlternativeEvaluation(
            alternative_id=item.alternative_id,
            summary=summarize_simulation_outcomes(
                contract=item.contract,
                vulnerability=vulnerability,
                declarer_tricks=declarer_tricks[item.alternative_id],
            ),
        )
        for item in items
    )

    comparison = compare_simulation_outcomes(
        OutcomeAlternative(item.alternative_id, item.summary)
        for item in evaluations
    )
    return ContractAlternativeEvaluationPipelineResult(evaluations, comparison)
