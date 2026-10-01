"""Role-aware views over a BridgeLab DecisionCase.

This module exposes the semantic role of evidence already stored in a
DecisionCase. It does not rank evidence, compare external providers,
select a recommendation, or modify the underlying DecisionCase.
"""

from __future__ import annotations

from dataclasses import dataclass

from .decision_case import DecisionCase
from .evidence_roles import (
    EvidenceRole,
    RoleEvidence,
    external_recommendation,
    observed_action,
    outcome_measurement,
    policy_recommendation,
    statistical_estimate,
)


@dataclass(frozen=True, slots=True)
class DecisionCaseRoleView:
    """Immutable role-aware view of one DecisionCase."""

    case_id: str
    evidence: tuple[RoleEvidence, ...]

    def for_role(
        self,
        role: EvidenceRole,
    ) -> tuple[RoleEvidence, ...]:
        """Return evidence carrying one semantic role."""

        return tuple(
            item
            for item in self.evidence
            if item.role is role
        )


def build_decision_case_role_view(
    case: DecisionCase,
) -> DecisionCaseRoleView:
    """Build a passive semantic-role view over a DecisionCase."""

    items: list[RoleEvidence] = []

    if case.bridgelab is not None:
        items.append(
            policy_recommendation(case.bridgelab)
        )

    items.extend(
        external_recommendation(item)
        for item in case.external
    )

    items.extend(
        observed_action(item)
        for item in case.corpus
    )

    items.extend(
        statistical_estimate(item)
        for item in case.simulations
    )

    items.extend(
        outcome_measurement(item)
        for item in case.double_dummy
    )

    return DecisionCaseRoleView(
        case_id=case.case_id,
        evidence=tuple(items),
    )
