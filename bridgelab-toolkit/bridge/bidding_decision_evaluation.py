"""Production bidding decision evaluation orchestration.

This module evaluates one BridgeLab bidding decision together with zero or
more external bidding advisers and assembles the observations into a
DecisionCase.

It does not vote, rank external providers, select a winner, or allow external
evidence to override BridgeLab policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bidding_rules import BiddingContext
from .bridgelab_bidding_evidence import bidding_result_to_evidence
from .decision_case import DecisionCase
from .decision_case_composition import (
    compose_multi_external_bidding_decision_case,
)
from .decision_evidence import (
    DisagreementContext,
    EvidenceScope,
)
from .engine_router import BiddingEngineRouter
from .external_bidding_adviser import ExternalBiddingAdviserAdapter


@dataclass(frozen=True, slots=True)
class ExternalBiddingEvaluation:
    """One external adviser plus its explicit comparison context."""

    adviser: ExternalBiddingAdviserAdapter
    disagreement_context: DisagreementContext = DisagreementContext()

    system_id: str | None = None
    convention_id: str | None = None
    treatment_id: str | None = None
    partnership_id: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.adviser, ExternalBiddingAdviserAdapter):
            raise TypeError(
                "adviser must be ExternalBiddingAdviserAdapter"
            )

        if not isinstance(
            self.disagreement_context,
            DisagreementContext,
        ):
            raise TypeError(
                "disagreement_context must be DisagreementContext"
            )


def evaluate_bidding_decision(
    *,
    case_id: str,
    context: BiddingContext,
    router: BiddingEngineRouter,
    bridgelab_scope: EvidenceScope,
    bridgelab_system_id: str | None = None,
    bridgelab_convention_id: str | None = None,
    bridgelab_treatment_id: str | None = None,
    bridgelab_partnership_id: str | None = None,
    external: tuple[ExternalBiddingEvaluation, ...] = (),
    notes: tuple[str, ...] = (),
) -> DecisionCase:
    """Evaluate BridgeLab and external advisers into one DecisionCase.

    BridgeLab is evaluated once through the production router.

    External advisers are evaluated independently and retained in caller
    order.  Each external observation is compared only with BridgeLab using
    its explicitly supplied DisagreementContext.

    No provider ranking, voting, fallback between external advisers, or
    policy override occurs here.
    """

    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id must be a non-blank string")

    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")

    if not isinstance(router, BiddingEngineRouter):
        raise TypeError("router must be BiddingEngineRouter")

    if not isinstance(bridgelab_scope, EvidenceScope):
        raise TypeError("bridgelab_scope must be EvidenceScope")

    external = tuple(external)
    notes = tuple(notes)

    for item in external:
        if not isinstance(item, ExternalBiddingEvaluation):
            raise TypeError(
                "external must contain only ExternalBiddingEvaluation"
            )

    bridgelab_result = router.evaluate(context)

    bridgelab_evidence = bidding_result_to_evidence(
        bridgelab_result,
        scope=bridgelab_scope,
        system_id=bridgelab_system_id,
        convention_id=bridgelab_convention_id,
        treatment_id=bridgelab_treatment_id,
        partnership_id=bridgelab_partnership_id,
    )

    external_evidence = tuple(
        item.adviser.evidence(
            context,
            system_id=item.system_id,
            convention_id=item.convention_id,
            treatment_id=item.treatment_id,
            partnership_id=item.partnership_id,
            confidence=item.confidence,
        )
        for item in external
    )

    disagreement_contexts = tuple(
        item.disagreement_context
        for item in external
    )

    return compose_multi_external_bidding_decision_case(
        case_id=case_id.strip(),
        bridgelab=bridgelab_evidence,
        external=external_evidence,
        disagreement_contexts=disagreement_contexts,
        notes=notes,
    )
