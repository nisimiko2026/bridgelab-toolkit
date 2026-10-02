"""Benchmark BridgeLab bidding policy against observed corpus decisions.

This module evaluates BridgeLab at corpus-derived bidding positions for which
an explicit system identity is available.

The observed corpus call remains evidence. It is not assumed to be correct,
is not promoted to BridgeLab policy, and does not vote against the BridgeLab
recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bidding_rules import BiddingContext, SystemContext
from .bridgelab_bidding_evidence import bidding_result_to_evidence
from .capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderEvidence,
    ProviderStatus,
)
from .corpus_decisions import CorpusBiddingDecision
from .decision_case import DecisionCase
from .decision_evidence import (
    DecisionEvidence,
    DisagreementContext,
    EvidenceScope,
)
from .decision_case_composition import (
    compose_bidding_decision_case,
)
from .engine_router import BiddingEngineRouter


CORPUS_OBSERVATION_IMPLEMENTATION = "corpus-observation"


class CorpusBenchmarkStatus(Enum):
    EVALUATED = "EVALUATED"
    SKIPPED_UNKNOWN_SYSTEM = "SKIPPED_UNKNOWN_SYSTEM"


@dataclass(frozen=True, slots=True)
class CorpusBenchmarkResult:
    decision: CorpusBiddingDecision
    status: CorpusBenchmarkStatus
    case: DecisionCase | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.decision,
            CorpusBiddingDecision,
        ):
            raise TypeError(
                "decision must be CorpusBiddingDecision"
            )

        if not isinstance(
            self.status,
            CorpusBenchmarkStatus,
        ):
            raise TypeError(
                "status must be CorpusBenchmarkStatus"
            )

        if self.status is CorpusBenchmarkStatus.EVALUATED:
            if not isinstance(self.case, DecisionCase):
                raise ValueError(
                    "evaluated benchmark result requires a DecisionCase"
                )
            if self.reason is not None:
                raise ValueError(
                    "evaluated benchmark result cannot have a reason"
                )
        else:
            if self.case is not None:
                raise ValueError(
                    "skipped benchmark result cannot have a DecisionCase"
                )
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError(
                    "skipped benchmark result requires a reason"
                )


def _corpus_provider(
    decision: CorpusBiddingDecision,
) -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=decision.provenance.provider,
        capability=Capability.BIDDING,
        implementation=CORPUS_OBSERVATION_IMPLEMENTATION,
        version=decision.provenance.provider_version,
    )


def corpus_decision_evidence(
    decision: CorpusBiddingDecision,
) -> DecisionEvidence[object]:
    """Represent the observed corpus call as external evidence."""

    if not isinstance(decision, CorpusBiddingDecision):
        raise TypeError(
            "decision must be CorpusBiddingDecision"
        )

    source_ids = ()

    if decision.provenance.record_id is not None:
        source_ids = (
            decision.provenance.record_id,
        )

    result = CapabilityResult(
        provider=_corpus_provider(decision),
        status=ProviderStatus.SUCCESS,
        recommendation=decision.observed_call,
        evidence=ProviderEvidence(
            source_ids=source_ids,
            notes=(
                f"source={decision.provenance.source}",
                f"call_index={decision.call_index}",
            ),
        ),
        explanation="Observed corpus call.",
    )

    return DecisionEvidence(
        scope=EvidenceScope.EXPERT_CORPUS,
        result=result,
        system_id=decision.system_id,
    )


def benchmark_corpus_decision(
    *,
    decision: CorpusBiddingDecision,
    router: BiddingEngineRouter,
    bridgelab_scope: EvidenceScope,
    system_options: tuple[tuple[str, str], ...] = (),
    bridgelab_convention_id: str | None = None,
    bridgelab_treatment_id: str | None = None,
    bridgelab_partnership_id: str | None = None,
    disagreement_context: DisagreementContext = DisagreementContext(),
) -> CorpusBenchmarkResult:
    """Evaluate one corpus decision against BridgeLab policy."""

    if not isinstance(decision, CorpusBiddingDecision):
        raise TypeError(
            "decision must be CorpusBiddingDecision"
        )

    if not isinstance(router, BiddingEngineRouter):
        raise TypeError(
            "router must be BiddingEngineRouter"
        )

    if not isinstance(bridgelab_scope, EvidenceScope):
        raise TypeError(
            "bridgelab_scope must be EvidenceScope"
        )

    if not isinstance(
        disagreement_context,
        DisagreementContext,
    ):
        raise TypeError(
            "disagreement_context must be DisagreementContext"
        )

    if decision.system_id is None:
        return CorpusBenchmarkResult(
            decision=decision,
            status=(
                CorpusBenchmarkStatus.SKIPPED_UNKNOWN_SYSTEM
            ),
            reason="corpus bidding system is unknown",
        )

    system = SystemContext(
        system=decision.system_id,
        options=system_options,
    )

    context = BiddingContext.create(
        hand=decision.hand,
        auction=decision.auction,
        vulnerability=decision.vulnerability,
        system=system,
        seat=decision.seat,
    )

    engine_result = router.evaluate(context)

    bridgelab = bidding_result_to_evidence(
        engine_result,
        scope=bridgelab_scope,
        system_id=decision.system_id,
        convention_id=bridgelab_convention_id,
        treatment_id=bridgelab_treatment_id,
        partnership_id=bridgelab_partnership_id,
    )

    observed = corpus_decision_evidence(
        decision
    )

    case_id = (
        f"{decision.provenance.provider}:"
        f"{decision.provenance.record_id or 'unknown'}:"
        f"{decision.call_index}"
    )

    case = compose_bidding_decision_case(
        case_id=case_id,
        bridgelab=bridgelab,
        external=observed,
        disagreement_context=disagreement_context,
        notes=(
            "corpus benchmark",
            "observed call is evidence, not policy",
        ),
    )

    return CorpusBenchmarkResult(
        decision=decision,
        status=CorpusBenchmarkStatus.EVALUATED,
        case=case,
    )


def benchmark_corpus_decisions(
    *,
    decisions: tuple[CorpusBiddingDecision, ...],
    router: BiddingEngineRouter,
    bridgelab_scope: EvidenceScope,
    system_options: tuple[tuple[str, str], ...] = (),
    bridgelab_convention_id: str | None = None,
    bridgelab_treatment_id: str | None = None,
    bridgelab_partnership_id: str | None = None,
    disagreement_context: DisagreementContext = DisagreementContext(),
) -> tuple[CorpusBenchmarkResult, ...]:
    """Benchmark corpus decisions in their original order."""

    if not isinstance(decisions, tuple):
        raise TypeError(
            "decisions must be a tuple"
        )

    if not all(
        isinstance(item, CorpusBiddingDecision)
        for item in decisions
    ):
        raise TypeError(
            "decisions must contain CorpusBiddingDecision values"
        )

    return tuple(
        benchmark_corpus_decision(
            decision=decision,
            router=router,
            bridgelab_scope=bridgelab_scope,
            system_options=system_options,
            bridgelab_convention_id=(
                bridgelab_convention_id
            ),
            bridgelab_treatment_id=(
                bridgelab_treatment_id
            ),
            bridgelab_partnership_id=(
                bridgelab_partnership_id
            ),
            disagreement_context=(
                disagreement_context
            ),
        )
        for decision in decisions
    )
