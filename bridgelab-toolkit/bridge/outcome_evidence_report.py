"""Serializable reporting view for BridgeLab outcome evidence.

A6.8 — Outcome Evidence Report.

The report exposes passive double-dummy and scored simulation outcome
measurements for presentation and integration. It does not rank alternatives,
select a winner, compare bidding recommendations, or mutate policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .decision_case import DecisionCase
from .trick_solver import TrickSolverStatus


@dataclass(frozen=True, slots=True)
class DoubleDummyOutcomeReportEntry:
    provider_id: str
    implementation: str
    version: str | None
    status: str
    deal_id: str
    declarer: str
    strain: str | None
    maximum_declarer_tricks: int | None

    def as_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "implementation": self.implementation,
            "version": self.version,
            "status": self.status,
            "deal_id": self.deal_id,
            "declarer": self.declarer,
            "strain": self.strain,
            "maximum_declarer_tricks": self.maximum_declarer_tricks,
        }


@dataclass(frozen=True, slots=True)
class SimulationOutcomeReportEntry:
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

    def as_dict(self) -> dict[str, object]:
        return {
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
        }


@dataclass(frozen=True, slots=True)
class OutcomeEvidenceReport:
    case_id: str
    double_dummy: tuple[DoubleDummyOutcomeReportEntry, ...]
    outcome_simulations: tuple[SimulationOutcomeReportEntry, ...]

    @property
    def double_dummy_total(self) -> int:
        return len(self.double_dummy)

    @property
    def outcome_simulation_total(self) -> int:
        return len(self.outcome_simulations)

    @property
    def total(self) -> int:
        return self.double_dummy_total + self.outcome_simulation_total

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "total": self.total,
            "double_dummy_total": self.double_dummy_total,
            "outcome_simulation_total": self.outcome_simulation_total,
            "double_dummy": [entry.as_dict() for entry in self.double_dummy],
            "outcome_simulations": [
                entry.as_dict() for entry in self.outcome_simulations
            ],
        }


def _enum_value(value: object) -> str:
    """Return a stable textual value for ordinary string-like enums."""
    raw = getattr(value, "value", value)
    return str(raw)


def _suit_text(suit) -> str | None:
    """Return bridge notation for Suit values; None represents notrump."""
    if suit is None:
        return None
    letter = getattr(suit, "letter", None)
    if isinstance(letter, str):
        return letter
    raise TypeError("suit must expose bridge letter notation")


def _contract_text(contract) -> str:
    bid = contract.bid
    suit = bid.strain.suit
    strain_text = "NT" if suit is None else _suit_text(suit)

    doubling = _enum_value(contract.doubling)
    suffix = {
        "undoubled": "",
        "doubled": "X",
        "redoubled": "XX",
    }.get(doubling, "")

    return f"{bid.level}{strain_text}{suffix}"


def _double_dummy_entry(evidence) -> DoubleDummyOutcomeReportEntry:
    result = evidence.result
    return DoubleDummyOutcomeReportEntry(
        provider_id=evidence.provider.provider_id,
        implementation=result.implementation,
        version=result.version,
        status=_enum_value(result.status),
        deal_id=result.deal_id,
        declarer=_enum_value(result.declarer),
        strain=_suit_text(result.strain),
        maximum_declarer_tricks=result.maximum_declarer_tricks,
    )


def _simulation_entry(summary) -> SimulationOutcomeReportEntry:
    return SimulationOutcomeReportEntry(
        contract=_contract_text(summary.contract),
        declarer=_enum_value(summary.contract.declarer),
        vulnerability=_enum_value(summary.vulnerability),
        sample_count=summary.sample_count,
        mean_declarer_score=summary.mean_declarer_score,
        median_declarer_score=summary.median_declarer_score,
        mean_ns_score=summary.mean_ns_score,
        median_ns_score=summary.median_ns_score,
        make_probability=summary.make_probability,
        down_probability=summary.down_probability,
        min_declarer_score=summary.min_declarer_score,
        max_declarer_score=summary.max_declarer_score,
    )


def build_outcome_evidence_report(case: DecisionCase) -> OutcomeEvidenceReport:
    """Build a passive serializable report from one DecisionCase."""
    if not isinstance(case, DecisionCase):
        raise TypeError("case must be DecisionCase")

    return OutcomeEvidenceReport(
        case_id=case.case_id,
        double_dummy=tuple(
            _double_dummy_entry(evidence)
            for evidence in case.double_dummy
        ),
        outcome_simulations=tuple(
            _simulation_entry(summary)
            for summary in case.outcome_simulations
        ),
    )
