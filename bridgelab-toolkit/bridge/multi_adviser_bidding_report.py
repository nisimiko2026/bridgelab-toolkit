"""Passive report model for multi-adviser bidding evidence.

A7.8 — Multi-Adviser Report.

The report exposes BridgeLab policy evidence, every external adviser with
provenance/status, independent disagreement classification, and optional A7.7
outcome candidates. It deliberately contains no winner, ranking, vote, score,
or policy-override mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass

from .bidding_outcome_connection import BiddingOutcomeCandidates
from .capability_providers import ProviderStatus
from .decision_evidence import DecisionEvidence, DisagreementKind
from .multi_adviser_disagreement import MultiAdviserDisagreementResult


@dataclass(frozen=True, slots=True)
class AdviserReportRow:
    provider_id: str
    status: ProviderStatus
    recommendation: object | None
    system_id: str | None
    convention_id: str | None
    treatment_id: str | None
    partnership_id: str | None
    confidence: float | None
    source_ids: tuple[str, ...]
    model_id: str | None
    disagreement: DisagreementKind | None


@dataclass(frozen=True, slots=True)
class OutcomeCandidateReportRow:
    alternative_id: str
    contract: str
    provider_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MultiAdviserBiddingReport:
    case_id: str
    bridgelab: AdviserReportRow
    advisers: tuple[AdviserReportRow, ...]
    outcomes: tuple[OutcomeCandidateReportRow, ...]
    failures: tuple[str, ...]
    notes: tuple[str, ...]


def _row(
    evidence: DecisionEvidence[object],
    disagreement: DisagreementKind | None,
) -> AdviserReportRow:
    provider_evidence = evidence.result.evidence
    return AdviserReportRow(
        provider_id=evidence.result.provider.provider_id,
        status=evidence.result.status,
        recommendation=evidence.recommendation,
        system_id=evidence.system_id,
        convention_id=evidence.convention_id,
        treatment_id=evidence.treatment_id,
        partnership_id=evidence.partnership_id,
        confidence=evidence.confidence,
        source_ids=provider_evidence.source_ids,
        model_id=provider_evidence.model_id,
        disagreement=disagreement,
    )


def build_multi_adviser_bidding_report(
    analysis: MultiAdviserDisagreementResult,
    *,
    outcome_candidates: BiddingOutcomeCandidates | None = None,
) -> MultiAdviserBiddingReport:
    """Build an audit/report view without selecting a preferred action."""
    if not isinstance(analysis, MultiAdviserDisagreementResult):
        raise TypeError("analysis must be MultiAdviserDisagreementResult")
    if outcome_candidates is not None and not isinstance(
        outcome_candidates, BiddingOutcomeCandidates
    ):
        raise TypeError("outcome_candidates must be BiddingOutcomeCandidates or None")

    case = analysis.decision_case
    if case.bridgelab is None:
        raise ValueError("analysis decision_case must contain BridgeLab evidence")

    advisers = tuple(
        _row(
            evidence,
            None if disagreement is None else disagreement.kind,
        )
        for evidence, disagreement in zip(
            case.external,
            analysis.disagreements,
        )
    )

    outcomes = ()
    if outcome_candidates is not None:
        outcomes = tuple(
            OutcomeCandidateReportRow(
                alternative_id=item.alternative.alternative_id,
                contract=item.contract.serialize(),
                provider_ids=item.provider_ids,
            )
            for item in outcome_candidates.candidates
        )

    failures = tuple(
        f"{item.provider_id}: {item.exception_type}: {item.message}"
        for item in analysis.gathered.failures
    )

    return MultiAdviserBiddingReport(
        case_id=case.case_id,
        bridgelab=_row(case.bridgelab, None),
        advisers=advisers,
        outcomes=outcomes,
        failures=failures,
        notes=case.notes,
    )
