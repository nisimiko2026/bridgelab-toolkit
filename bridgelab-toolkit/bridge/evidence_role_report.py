"""Serializable reporting view for BridgeLab evidence roles.

The report exposes evidence-role counts for presentation and integration.
It does not rank evidence, compare recommendations, score providers,
select a winner, or promote external evidence into BridgeLab policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .decision_case_roles import DecisionCaseRoleView
from .evidence_role_summary import (
    EvidenceRoleSummary,
    summarize_evidence_roles,
)


@dataclass(frozen=True, slots=True)
class EvidenceRoleReport:
    """Serializable evidence-role report for one decision case."""

    case_id: str
    total: int
    counts: tuple[tuple[str, int], ...]
    roles_present: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-friendly representation."""

        return {
            "case_id": self.case_id,
            "total": self.total,
            "counts": {
                role: count
                for role, count in self.counts
            },
            "roles_present": list(self.roles_present),
        }


def build_evidence_role_report(
    view: DecisionCaseRoleView,
    *,
    summary: EvidenceRoleSummary | None = None,
) -> EvidenceRoleReport:
    """Build a passive report from a role-aware decision-case view."""

    if summary is None:
        summary = summarize_evidence_roles(view)

    counts = tuple(
        (role.value, count)
        for role, count in summary.counts
    )

    roles_present = tuple(
        role.value
        for role in summary.roles_present
    )

    return EvidenceRoleReport(
        case_id=view.case_id,
        total=summary.total,
        counts=counts,
        roles_present=roles_present,
    )
