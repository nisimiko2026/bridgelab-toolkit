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
