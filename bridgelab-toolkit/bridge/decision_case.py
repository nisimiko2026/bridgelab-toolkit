"""Passive evidence bundle for one BridgeLab decision case.

A DecisionCase gathers heterogeneous evidence around one decision point.
It does not rank providers, vote, choose a winner, infer missing systems,
override bidding policy, or convert reference measurements into recommendations.
"""
from __future__ import annotations

from dataclasses import dataclass

from .corpus import CanonicalBoardRecord
from .decision_evidence import DecisionEvidence, Disagreement
from .double_dummy_evidence import DoubleDummyEvidence
from .simulation_outcome import SimulationOutcomeSummary
from .simulation_statistics import SimulationStatistics


@dataclass(frozen=True, slots=True)
class DecisionCase:
    """Immutable collection of evidence for one decision point."""

    case_id: str
    bridgelab: DecisionEvidence[object] | None = None
    external: tuple[DecisionEvidence[object], ...] = ()
    corpus: tuple[CanonicalBoardRecord, ...] = ()
    simulations: tuple[SimulationStatistics, ...] = ()
    outcome_simulations: tuple[SimulationOutcomeSummary, ...] = ()
    double_dummy: tuple[DoubleDummyEvidence, ...] = ()
    disagreements: tuple[Disagreement, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ValueError("case_id must be a non-blank string")
        object.__setattr__(self, "case_id", self.case_id.strip())

        if self.bridgelab is not None and not isinstance(
            self.bridgelab,
            DecisionEvidence,
        ):
            raise TypeError(
                "bridgelab must be DecisionEvidence or None"
            )

        self._validate_tuple(
            "external",
            self.external,
            DecisionEvidence,
        )
        self._validate_tuple(
            "corpus",
            self.corpus,
            CanonicalBoardRecord,
        )
        self._validate_tuple(
            "simulations",
            self.simulations,
            SimulationStatistics,
        )
        self._validate_tuple(
            "outcome_simulations",
            self.outcome_simulations,
            SimulationOutcomeSummary,
        )
        self._validate_tuple(
            "double_dummy",
            self.double_dummy,
            DoubleDummyEvidence,
        )
        self._validate_tuple(
            "disagreements",
            self.disagreements,
            Disagreement,
        )

        if not isinstance(self.notes, tuple):
            raise TypeError("notes must be a tuple")
        for note in self.notes:
            if not isinstance(note, str) or not note.strip():
                raise ValueError(
                    "notes entries must be non-blank strings"
                )

    @staticmethod
    def _validate_tuple(
        name: str,
        values: object,
        expected_type: type,
    ) -> None:
        if not isinstance(values, tuple):
            raise TypeError(f"{name} must be a tuple")
        for value in values:
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"{name} entries must be "
                    f"{expected_type.__name__}"
                )
