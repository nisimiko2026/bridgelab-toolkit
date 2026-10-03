"""Multi-adviser disagreement analysis.

A7.6 — Multi-AI Disagreement.

Each external adviser is compared independently with BridgeLab. Provider
failures are isolated, system identity is derived only from explicit metadata,
and no adviser-to-adviser voting, ranking, or winner selection occurs.
"""
from __future__ import annotations

from dataclasses import dataclass

from .bidding_rules import BiddingContext
from .bidding_system_awareness import system_aware_disagreement_context
from .capability_providers import ProviderStatus
from .capability_registry import CapabilityProviderRegistry
from .decision_case import DecisionCase
from .decision_evidence import (
    DecisionEvidence,
    Disagreement,
    DisagreementContext,
    DisagreementKind,
    classify_disagreement,
)
from .isolated_bidding_evidence import (
    IsolatedMultiAdviserBiddingResult,
    gather_bidding_adviser_evidence_isolated,
)
from .multi_bidding_adviser import BiddingAdviserRequest


@dataclass(frozen=True, slots=True)
class AdviserSemanticContext:
    """Optional explicit semantic relationship beyond system identity."""
    same_convention: bool | None = None
    same_treatment: bool | None = None
    same_partnership_agreement: bool | None = None
    bridgelab_policy_expected: bool = False
    engine_defect_evidence: bool = False


@dataclass(frozen=True, slots=True)
class MultiAdviserDisagreementResult:
    gathered: IsolatedMultiAdviserBiddingResult
    contexts: tuple[DisagreementContext, ...]
    disagreements: tuple[Disagreement | None, ...]
    decision_case: DecisionCase

    def __post_init__(self) -> None:
        n = self.gathered.gathered.total
        if len(self.contexts) != n or len(self.disagreements) != n:
            raise ValueError("contexts and disagreements must align with gathered advisers")
        if self.decision_case.external != self.gathered.evidence:
            raise ValueError("decision_case external evidence must match gathered evidence")

    @property
    def classified(self) -> tuple[Disagreement, ...]:
        return tuple(x for x in self.disagreements if x is not None)


def analyze_multi_adviser_disagreement(
    *,
    case_id: str,
    bridgelab: DecisionEvidence[object],
    registry: CapabilityProviderRegistry,
    context: BiddingContext,
    requests: tuple[BiddingAdviserRequest, ...],
    semantic_contexts: tuple[AdviserSemanticContext, ...] | None = None,
    notes: tuple[str, ...] = (),
) -> MultiAdviserDisagreementResult:
    """Gather and independently classify usable external adviser evidence."""
    if not isinstance(bridgelab, DecisionEvidence):
        raise TypeError("bridgelab must be DecisionEvidence")
    if semantic_contexts is None:
        semantic_contexts = tuple(AdviserSemanticContext() for _ in requests)
    if not isinstance(semantic_contexts, tuple):
        raise TypeError("semantic_contexts must be a tuple or None")
    if len(semantic_contexts) != len(requests):
        raise ValueError("requests and semantic_contexts must have equal length")
    if not all(isinstance(x, AdviserSemanticContext) for x in semantic_contexts):
        raise TypeError("semantic_contexts must contain AdviserSemanticContext")

    gathered = gather_bidding_adviser_evidence_isolated(
        registry=registry,
        context=context,
        requests=requests,
    )

    contexts = []
    disagreements = []
    for observation, semantic in zip(gathered.evidence, semantic_contexts):
        dc = system_aware_disagreement_context(
            bridgelab,
            observation,
            same_convention=semantic.same_convention,
            same_treatment=semantic.same_treatment,
            same_partnership_agreement=semantic.same_partnership_agreement,
            bridgelab_policy_expected=semantic.bridgelab_policy_expected,
            engine_defect_evidence=semantic.engine_defect_evidence,
        )
        contexts.append(dc)

        # UNAVAILABLE/FAILED are operational evidence, not bidding opinions.
        # They therefore do not enter the disagreement taxonomy as votes.
        if observation.result.status in (
            ProviderStatus.UNAVAILABLE,
            ProviderStatus.FAILED,
        ):
            disagreements.append(None)
        else:
            disagreements.append(
                classify_disagreement(bridgelab, observation, context=dc)
            )

    decision_case = DecisionCase(
        case_id=case_id,
        bridgelab=bridgelab,
        external=gathered.evidence,
        disagreements=tuple(x for x in disagreements if x is not None),
        notes=notes,
    )

    return MultiAdviserDisagreementResult(
        gathered=gathered,
        contexts=tuple(contexts),
        disagreements=tuple(disagreements),
        decision_case=decision_case,
    )
