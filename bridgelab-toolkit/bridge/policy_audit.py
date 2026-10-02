"""Structured audit candidates derived from BridgeLab decision cases.

This module identifies decision cases that existing disagreement
classification has already marked for policy or engine review.

It does not reclassify disagreements, rank evidence, vote, decide which
recommendation is correct, or modify BridgeLab policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call
from .decision_case import DecisionCase
from .decision_evidence import DisagreementKind
from .evidence_source_manifest import build_evidence_source_manifest
from .evidence_source_report import (
    EvidenceSourceReport,
    build_evidence_source_report,
)


_AUDITABLE_KINDS = frozenset(
    {
        DisagreementKind.POSSIBLE_POLICY_GAP,
        DisagreementKind.POSSIBLE_ENGINE_DEFECT,
    }
)


@dataclass(frozen=True, slots=True)
class PolicyAuditCandidate:
    """One explicitly classified BridgeLab audit candidate."""

    case_id: str
    kind: DisagreementKind

    bridgelab_provider_id: str
    bridgelab_recommendation: Call | None

    external_provider_id: str
    external_recommendation: Call | None

    system_id: str | None
    convention_id: str | None
    treatment_id: str | None
    partnership_id: str | None

    source_report: EvidenceSourceReport


def build_policy_audit_candidates(
    case: DecisionCase,
) -> tuple[PolicyAuditCandidate, ...]:
    """Build audit candidates from already-classified disagreements.

    Only POSSIBLE_POLICY_GAP and POSSIBLE_ENGINE_DEFECT are surfaced.

    Other disagreement kinds remain evidence in the DecisionCase but are not
    promoted into audit candidates by this function.
    """

    if not isinstance(case, DecisionCase):
        raise TypeError("case must be DecisionCase")

    if case.bridgelab is None:
        return ()

    manifest = build_evidence_source_manifest(case)
    source_report = build_evidence_source_report(manifest)

    external_by_provider: dict[str, list[object]] = {}

    for evidence in case.external:
        provider_id = evidence.result.provider.provider_id
        external_by_provider.setdefault(
            provider_id,
            [],
        ).append(evidence)

    used_provider_occurrences: dict[str, int] = {}
    candidates: list[PolicyAuditCandidate] = []

    for disagreement in case.disagreements:
        if disagreement.kind not in _AUDITABLE_KINDS:
            continue

        provider_id = disagreement.right_provider_id
        occurrence = used_provider_occurrences.get(
            provider_id,
            0,
        )

        matching = external_by_provider.get(
            provider_id,
            [],
        )

        if occurrence >= len(matching):
            raise ValueError(
                "auditable disagreement has no matching "
                "external evidence"
            )

        external = matching[occurrence]
        used_provider_occurrences[provider_id] = (
            occurrence + 1
        )

        candidates.append(
            PolicyAuditCandidate(
                case_id=case.case_id,
                kind=disagreement.kind,
                bridgelab_provider_id=(
                    case.bridgelab.result.provider.provider_id
                ),
                bridgelab_recommendation=(
                    case.bridgelab.recommendation
                ),
                external_provider_id=provider_id,
                external_recommendation=(
                    external.recommendation
                ),
                system_id=case.bridgelab.system_id,
                convention_id=case.bridgelab.convention_id,
                treatment_id=case.bridgelab.treatment_id,
                partnership_id=case.bridgelab.partnership_id,
                source_report=source_report,
            )
        )

    return tuple(candidates)
