"""Immutable enrichment of BridgeLab decision cases.

This module adds already-produced corpus, simulation, and double-dummy
evidence to an existing DecisionCase.

It does not reinterpret evidence, rerun bidding decisions, classify new
disagreements, rank sources, vote, select a winner, or convert measurements
into recommendations.
"""

from __future__ import annotations

from dataclasses import replace

from .corpus import CanonicalBoardRecord
from .decision_case import DecisionCase
from .double_dummy_evidence import DoubleDummyEvidence
from .simulation_statistics import SimulationStatistics


def enrich_decision_case(
    case: DecisionCase,
    *,
    corpus: tuple[CanonicalBoardRecord, ...] = (),
    simulations: tuple[SimulationStatistics, ...] = (),
    double_dummy: tuple[DoubleDummyEvidence, ...] = (),
    notes: tuple[str, ...] = (),
) -> DecisionCase:
    """Return a new DecisionCase with additional reference evidence.

    Existing evidence is preserved first. New evidence is appended in caller
    order within each evidence category.

    The original DecisionCase is never mutated.
    """

    if not isinstance(case, DecisionCase):
        raise TypeError("case must be DecisionCase")

    _validate_tuple(
        "corpus",
        corpus,
        CanonicalBoardRecord,
    )
    _validate_tuple(
        "simulations",
        simulations,
        SimulationStatistics,
    )
    _validate_tuple(
        "double_dummy",
        double_dummy,
        DoubleDummyEvidence,
    )

    if not isinstance(notes, tuple):
        raise TypeError("notes must be a tuple")

    for note in notes:
        if not isinstance(note, str) or not note.strip():
            raise ValueError(
                "notes entries must be non-blank strings"
            )

    return replace(
        case,
        corpus=case.corpus + corpus,
        simulations=case.simulations + simulations,
        double_dummy=case.double_dummy + double_dummy,
        notes=case.notes + notes,
    )


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
