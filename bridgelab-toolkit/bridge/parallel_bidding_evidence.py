"""Parallel external bidding evidence composition.

A7.3 — Parallel Evidence.

Gather evidence from explicitly requested advisers and attach it to one
DecisionCase. Each adviser remains an independent evidence source. This layer
does not rank, vote, select, retry, or silently fall back between advisers.
"""
from __future__ import annotations

from dataclasses import dataclass

from .bidding_rules import BiddingContext
from .capability_registry import CapabilityProviderRegistry
from .decision_case import DecisionCase
from .decision_case_composition import compose_multi_external_bidding_decision_case
from .decision_evidence import DecisionEvidence, DisagreementContext
from .multi_bidding_adviser import (
    BiddingAdviserRequest,
    MultiAdviserBiddingResult,
    gather_bidding_adviser_evidence,
)


@dataclass(frozen=True, slots=True)
class ParallelBiddingEvidenceResult:
    gathered: MultiAdviserBiddingResult
    decision_case: DecisionCase

    def __post_init__(self) -> None:
        if not isinstance(self.gathered, MultiAdviserBiddingResult):
            raise TypeError("gathered must be MultiAdviserBiddingResult")
        if not isinstance(self.decision_case, DecisionCase):
            raise TypeError("decision_case must be DecisionCase")
        if self.decision_case.external != self.gathered.evidence:
            raise ValueError(
                "decision_case external evidence must match gathered evidence"
            )


def compose_parallel_bidding_evidence(
    *,
    case_id: str,
    bridgelab: DecisionEvidence[object],
    registry: CapabilityProviderRegistry,
    context: BiddingContext,
    requests: tuple[BiddingAdviserRequest, ...],
    disagreement_contexts: tuple[DisagreementContext, ...],
    notes: tuple[str, ...] = (),
) -> ParallelBiddingEvidenceResult:
    """Gather requested advisers and compose one passive DecisionCase."""
    if not isinstance(bridgelab, DecisionEvidence):
        raise TypeError("bridgelab must be DecisionEvidence")
    if not isinstance(requests, tuple):
        raise TypeError("requests must be a tuple")
    if not isinstance(disagreement_contexts, tuple):
        raise TypeError("disagreement_contexts must be a tuple")
    if not all(isinstance(x, BiddingAdviserRequest) for x in requests):
        raise TypeError("requests must contain BiddingAdviserRequest")
    if not all(isinstance(x, DisagreementContext) for x in disagreement_contexts):
        raise TypeError(
            "disagreement_contexts must contain DisagreementContext"
        )
    if len(requests) != len(disagreement_contexts):
        raise ValueError(
            "requests and disagreement_contexts must have equal length"
        )

    gathered = gather_bidding_adviser_evidence(
        registry=registry,
        context=context,
        requests=requests,
    )

    decision_case = compose_multi_external_bidding_decision_case(
        case_id=case_id,
        bridgelab=bridgelab,
        external=gathered.evidence,
        disagreement_contexts=disagreement_contexts,
        notes=notes,
    )

    return ParallelBiddingEvidenceResult(
        gathered=gathered,
        decision_case=decision_case,
    )
