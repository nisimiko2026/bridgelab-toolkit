"""Composition helpers for BridgeLab decision evidence.

This module assembles already-produced evidence into a DecisionCase.
It does not rank providers, select a preferred recommendation, or
promote external evidence into BridgeLab policy.
"""

from __future__ import annotations

from .decision_case import DecisionCase
from .decision_evidence import (
    DecisionEvidence,
    DisagreementContext,
    classify_disagreement,
)


def compose_bidding_decision_case(
    *,
    case_id: str,
    bridgelab: DecisionEvidence[object],
    external: DecisionEvidence[object],
    disagreement_context: DisagreementContext = DisagreementContext(),
    notes: tuple[str, ...] = (),
) -> DecisionCase:
    """Compose one BridgeLab/external bidding comparison."""

    disagreement = classify_disagreement(
        bridgelab,
        external,
        context=disagreement_context,
    )

    return DecisionCase(
        case_id=case_id,
        bridgelab=bridgelab,
        external=(external,),
        disagreements=(disagreement,),
        notes=notes,
    )


def compose_multi_external_bidding_decision_case(
    *,
    case_id: str,
    bridgelab: DecisionEvidence[object],
    external: tuple[DecisionEvidence[object], ...],
    disagreement_contexts: tuple[DisagreementContext, ...],
    notes: tuple[str, ...] = (),
) -> DecisionCase:
    """Compose BridgeLab evidence with multiple external observations.

    Each external observation is compared independently with BridgeLab.
    External observations are not compared with one another, ranked,
    voted on, or promoted into BridgeLab policy.
    """

    if len(external) != len(disagreement_contexts):
        raise ValueError(
            "external and disagreement_contexts must have equal length"
        )

    disagreements = tuple(
        classify_disagreement(
            bridgelab,
            observation,
            context=context,
        )
        for observation, context in zip(
            external,
            disagreement_contexts,
        )
    )

    return DecisionCase(
        case_id=case_id,
        bridgelab=bridgelab,
        external=external,
        disagreements=disagreements,
        notes=notes,
    )
