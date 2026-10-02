"""System-independent outcome evaluation contracts.

A6.1 — Outcome Evaluation Contract.

Outcome evaluators measure consequences of bridge actions. They do not define
bidding policy, convention meaning, partnership agreements, or correctness.
Double-dummy and simulation results are evidence measurements only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .deals import Deal
from .models import Card, Seat, Suit


class OutcomeEvaluationStatus(str, Enum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class OutcomeEvaluationMethod(str, Enum):
    DOUBLE_DUMMY = "double_dummy"
    SIMULATION = "simulation"


@dataclass(frozen=True, slots=True)
class OutcomeEvaluationRequest:
    deal: Deal
    declarer: Seat
    strain: Suit | None  # None means no trump.
    opening_lead: Card | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.deal, Deal):
            raise TypeError("deal must be a Deal")
        if not isinstance(self.declarer, Seat):
            raise TypeError("declarer must be a Seat")
        if self.strain is not None and not isinstance(self.strain, Suit):
            raise TypeError("strain must be a Suit or None for NT")
        if self.opening_lead is not None and not isinstance(self.opening_lead, Card):
            raise TypeError("opening_lead must be a Card or None")


@dataclass(frozen=True, slots=True)
class OutcomeEvaluationResult:
    provider_id: str
    implementation: str
    version: str | None
    method: OutcomeEvaluationMethod
    status: OutcomeEvaluationStatus
    declarer: Seat
    strain: Suit | None
    opening_lead: Card | None
    declarer_tricks: float | None
    sample_count: int | None
    elapsed_seconds: float
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        if not isinstance(self.implementation, str) or not self.implementation.strip():
            raise ValueError("implementation must be a non-blank string")
        if not isinstance(self.method, OutcomeEvaluationMethod):
            raise TypeError("method must be OutcomeEvaluationMethod")
        if not isinstance(self.status, OutcomeEvaluationStatus):
            raise TypeError("status must be OutcomeEvaluationStatus")
        if not isinstance(self.declarer, Seat):
            raise TypeError("declarer must be a Seat")
        if self.strain is not None and not isinstance(self.strain, Suit):
            raise TypeError("strain must be a Suit or None for NT")
        if self.opening_lead is not None and not isinstance(self.opening_lead, Card):
            raise TypeError("opening_lead must be a Card or None")
        if not isinstance(self.elapsed_seconds, (int, float)) or isinstance(
            self.elapsed_seconds, bool
        ) or self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be non-negative")

        if self.status is OutcomeEvaluationStatus.SUCCESS:
            if not isinstance(self.declarer_tricks, (int, float)) or isinstance(
                self.declarer_tricks, bool
            ) or not 0 <= self.declarer_tricks <= 13:
                raise ValueError(
                    "successful outcome result needs 0..13 declarer tricks"
                )
        elif self.declarer_tricks is not None:
            raise ValueError(
                "failed/unavailable outcome result must not contain tricks"
            )

        if self.method is OutcomeEvaluationMethod.DOUBLE_DUMMY:
            if self.sample_count is not None:
                raise ValueError(
                    "double-dummy outcome result must not contain sample_count"
                )
            if (
                self.status is OutcomeEvaluationStatus.SUCCESS
                and not float(self.declarer_tricks).is_integer()
            ):
                raise ValueError(
                    "double-dummy declarer tricks must be an integer"
                )
        elif self.sample_count is not None:
            if (
                not isinstance(self.sample_count, int)
                or isinstance(self.sample_count, bool)
                or self.sample_count < 1
            ):
                raise ValueError("sample_count must be a positive integer")


class OutcomeEvaluator(Protocol):
    provider_id: str
    method: OutcomeEvaluationMethod

    def evaluate(
        self,
        request: OutcomeEvaluationRequest,
    ) -> OutcomeEvaluationResult:
        """Measure an outcome or return explicit unavailable/failure status."""
