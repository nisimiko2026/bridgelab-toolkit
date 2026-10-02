"""Attach measured outcome evidence to an existing DecisionCase.

A6.7.1 — Outcome Simulation Evidence Correction.

Auction-simulation statistics and scored outcome simulations are different
evidence types. Scored SimulationOutcomeSummary values are appended to
DecisionCase.outcome_simulations; DecisionCase.simulations remains reserved
for the existing auction-simulation statistics.

Reference measurements remain passive evidence: they are not recommendations,
disagreements, votes, winners, or policy changes.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .decision_case import DecisionCase
from .double_dummy_evidence import DoubleDummyEvidence
from .simulation_outcome import SimulationOutcomeSummary


def add_outcome_evidence(
    case: DecisionCase,
    *,
    outcome_simulations: Iterable[SimulationOutcomeSummary] = (),
    double_dummy: Iterable[DoubleDummyEvidence] = (),
    notes: Iterable[str] = (),
) -> DecisionCase:
    """Return a new DecisionCase with passive outcome evidence appended."""
    if not isinstance(case, DecisionCase):
        raise TypeError("case must be DecisionCase")

    simulation_items = _typed_tuple(
        "outcome_simulations",
        outcome_simulations,
        SimulationOutcomeSummary,
    )
    double_dummy_items = _typed_tuple(
        "double_dummy",
        double_dummy,
        DoubleDummyEvidence,
    )
    note_items = _notes_tuple(notes)

    return replace(
        case,
        outcome_simulations=case.outcome_simulations + simulation_items,
        double_dummy=case.double_dummy + double_dummy_items,
        notes=case.notes + note_items,
    )


def _typed_tuple(name: str, values, expected_type: type) -> tuple:
    try:
        items = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable") from exc

    for item in items:
        if not isinstance(item, expected_type):
            raise TypeError(
                f"{name} entries must be {expected_type.__name__}"
            )
    return items


def _notes_tuple(values) -> tuple[str, ...]:
    try:
        items = tuple(values)
    except TypeError as exc:
        raise TypeError("notes must be an iterable") from exc

    cleaned = []
    for note in items:
        if not isinstance(note, str) or not note.strip():
            raise ValueError("notes entries must be non-blank strings")
        cleaned.append(note.strip())
    return tuple(cleaned)
