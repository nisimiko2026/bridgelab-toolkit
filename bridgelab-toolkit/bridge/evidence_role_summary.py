"""Passive summaries of semantic evidence roles.

A summary counts evidence by semantic role. It does not rank evidence,
compare recommendations, vote, score providers, or select a winner.
"""

from __future__ import annotations

from dataclasses import dataclass

from .decision_case_roles import DecisionCaseRoleView
from .evidence_roles import EvidenceRole


@dataclass(frozen=True, slots=True)
class EvidenceRoleSummary:
    """Counts of evidence items grouped by semantic role."""

    counts: tuple[tuple[EvidenceRole, int], ...]
    total: int

    def count(
        self,
        role: EvidenceRole,
    ) -> int:
        """Return the number of evidence items carrying one role."""

        for candidate, value in self.counts:
            if candidate is role:
                return value
        return 0

    @property
    def roles_present(self) -> tuple[EvidenceRole, ...]:
        """Return roles having at least one evidence item."""

        return tuple(
            role
            for role, value in self.counts
            if value > 0
        )


def summarize_evidence_roles(
    view: DecisionCaseRoleView,
) -> EvidenceRoleSummary:
    """Count evidence in a role-aware DecisionCase view."""

    counts = tuple(
        (
            role,
            sum(
                1
                for item in view.evidence
                if item.role is role
            ),
        )
        for role in EvidenceRole
    )

    return EvidenceRoleSummary(
        counts=counts,
        total=len(view.evidence),
    )
