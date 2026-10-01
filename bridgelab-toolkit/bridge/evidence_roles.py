"""Semantic roles for evidence used by BridgeLab.

Evidence roles describe what an item of evidence represents.
They do not rank evidence, assign authority, select a winner,
or promote external evidence into BridgeLab policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .decision_evidence import DecisionEvidence
from .double_dummy_evidence import DoubleDummyEvidence
from .simulation_statistics import SimulationStatistics


class EvidenceRole(str, Enum):
    """Semantic role played by an evidence item."""

    POLICY_RECOMMENDATION = "policy_recommendation"
    EXTERNAL_RECOMMENDATION = "external_recommendation"
    OBSERVED_ACTION = "observed_action"
    OUTCOME_MEASUREMENT = "outcome_measurement"
    STATISTICAL_ESTIMATE = "statistical_estimate"


@dataclass(frozen=True, slots=True)
class RoleEvidence:
    """One evidence item together with its semantic role."""

    role: EvidenceRole
    evidence: object


def policy_recommendation(
    evidence: DecisionEvidence[object],
) -> RoleEvidence:
    """Mark a BridgeLab decision as policy evidence."""

    return RoleEvidence(
        role=EvidenceRole.POLICY_RECOMMENDATION,
        evidence=evidence,
    )


def external_recommendation(
    evidence: DecisionEvidence[object],
) -> RoleEvidence:
    """Mark an external adviser recommendation."""

    return RoleEvidence(
        role=EvidenceRole.EXTERNAL_RECOMMENDATION,
        evidence=evidence,
    )


def observed_action(
    evidence: object,
) -> RoleEvidence:
    """Mark an observed action from a corpus or recorded deal."""

    return RoleEvidence(
        role=EvidenceRole.OBSERVED_ACTION,
        evidence=evidence,
    )


def outcome_measurement(
    evidence: DoubleDummyEvidence,
) -> RoleEvidence:
    """Mark double-dummy evidence as an outcome measurement."""

    return RoleEvidence(
        role=EvidenceRole.OUTCOME_MEASUREMENT,
        evidence=evidence,
    )


def statistical_estimate(
    evidence: SimulationStatistics,
) -> RoleEvidence:
    """Mark simulation evidence as a statistical estimate."""

    return RoleEvidence(
        role=EvidenceRole.STATISTICAL_ESTIMATE,
        evidence=evidence,
    )
