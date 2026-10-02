"""Evaluate a canonical contract through an OutcomeEvaluator and score it.

A6.4 — Contract Outcome Evaluator.

This service composes measurement and duplicate scoring. It does not define
bidding policy, choose contracts, rank bids, or substitute heuristic outcomes
when the underlying evaluator is unavailable or fails.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Contract
from .corpus import Vulnerability
from .deals import Deal
from .outcome_evaluation import (
    OutcomeEvaluator,
    OutcomeEvaluationRequest,
    OutcomeEvaluationResult,
    OutcomeEvaluationStatus,
)
from .outcome_scoring import ContractOutcome, score_contract_outcome


@dataclass(frozen=True, slots=True)
class ContractOutcomeEvaluation:
    contract: Contract
    vulnerability: Vulnerability
    measurement: OutcomeEvaluationResult
    outcome: ContractOutcome | None

    def __post_init__(self) -> None:
        if not isinstance(self.contract, Contract):
            raise TypeError("contract must be Contract")
        if not isinstance(self.vulnerability, Vulnerability):
            raise TypeError("vulnerability must be Vulnerability")
        if not isinstance(self.measurement, OutcomeEvaluationResult):
            raise TypeError("measurement must be OutcomeEvaluationResult")
        if self.measurement.status is OutcomeEvaluationStatus.SUCCESS:
            if self.outcome is None:
                raise ValueError("successful measurement requires scored outcome")
        elif self.outcome is not None:
            raise ValueError("non-successful measurement cannot have scored outcome")

    @property
    def status(self) -> OutcomeEvaluationStatus:
        return self.measurement.status

    @property
    def declarer_score(self) -> int | None:
        return None if self.outcome is None else self.outcome.declarer_score

    @property
    def ns_score(self) -> int | None:
        return None if self.outcome is None else self.outcome.ns_score


def evaluate_contract_outcome(
    *,
    evaluator: OutcomeEvaluator,
    deal: Deal,
    contract: Contract,
    vulnerability: Vulnerability,
) -> ContractOutcomeEvaluation:
    """Measure declarer tricks for ``contract`` and score only on success."""
    if not callable(getattr(evaluator, "evaluate", None)):
        raise TypeError("evaluator must provide a callable evaluate method")
    if not isinstance(deal, Deal):
        raise TypeError("deal must be Deal")
    if not isinstance(contract, Contract):
        raise TypeError("contract must be Contract")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("vulnerability must be Vulnerability")

    measurement = evaluator.evaluate(
        OutcomeEvaluationRequest(
            deal=deal,
            declarer=contract.declarer,
            strain=contract.bid.strain.suit,
        )
    )
    if not isinstance(measurement, OutcomeEvaluationResult):
        raise TypeError("evaluator must return OutcomeEvaluationResult")

    if measurement.declarer is not contract.declarer:
        raise ValueError("measurement declarer does not match contract")
    if measurement.strain is not contract.bid.strain.suit:
        raise ValueError("measurement strain does not match contract")
    if measurement.opening_lead is not None:
        raise ValueError("unexpected opening_lead in unrestricted contract evaluation")

    outcome = None
    if measurement.status is OutcomeEvaluationStatus.SUCCESS:
        tricks = measurement.declarer_tricks
        if tricks is None:
            raise ValueError("successful measurement requires declarer tricks")
        if not float(tricks).is_integer():
            raise ValueError(
                "contract scoring requires an integer declarer-trick measurement"
            )
        outcome = score_contract_outcome(
            contract,
            int(tricks),
            vulnerability,
        )

    return ContractOutcomeEvaluation(
        contract=contract,
        vulnerability=vulnerability,
        measurement=measurement,
        outcome=outcome,
    )
