"""Adapt BridgeLab production bidding results into decision evidence.

This module preserves the recommendation and canonical source provenance
already produced by BridgeLab. It does not rerank rules, reinterpret policy,
compare external advisers, or select a winner.

The semantic evidence role (for example, POLICY_RECOMMENDATION) is separate
from EvidenceScope. Scope identifies where the BridgeLab bidding knowledge
belongs: system, convention, treatment, partnership, or another supported
scope supplied explicitly by the caller.
"""

from __future__ import annotations

from .bidding_engine import BiddingEngineResult
from .capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderEvidence,
    ProviderStatus,
)
from .decision_evidence import (
    DecisionEvidence,
    EvidenceScope,
)


BRIDGELAB_BIDDING_PROVIDER_ID = "bridgelab"
BRIDGELAB_BIDDING_IMPLEMENTATION = "bidding-engine"


def bridgelab_bidding_provider() -> ProviderDescriptor:
    """Return the descriptor for BridgeLab's production bidding engine."""

    return ProviderDescriptor(
        provider_id=BRIDGELAB_BIDDING_PROVIDER_ID,
        capability=Capability.BIDDING,
        implementation=BRIDGELAB_BIDDING_IMPLEMENTATION,
    )


def bidding_result_to_evidence(
    result: BiddingEngineResult,
    *,
    scope: EvidenceScope,
    system_id: str | None = None,
    convention_id: str | None = None,
    treatment_id: str | None = None,
    partnership_id: str | None = None,
) -> DecisionEvidence[object]:
    """Convert one BridgeLab bidding result into decision evidence.

    The function preserves the production engine's selected recommendation,
    alternatives, explanation, rule identity, and canonical knowledge-source
    references.

    It does not infer the evidence scope. The caller must provide the scope
    explicitly because a BridgeLab recommendation may originate from system,
    convention, treatment, or partnership policy.
    """

    if not isinstance(result, BiddingEngineResult):
        raise TypeError("result must be BiddingEngineResult")

    if not isinstance(scope, EvidenceScope):
        raise TypeError("scope must be EvidenceScope")

    provider = bridgelab_bidding_provider()

    if result.recommended is None:
        capability_result = CapabilityResult(
            provider=provider,
            status=ProviderStatus.ABSTAIN,
            recommendation=None,
            alternatives=(),
            evidence=ProviderEvidence(),
            explanation="BridgeLab bidding engine abstained.",
        )

        return DecisionEvidence(
            scope=scope,
            result=capability_result,
            system_id=system_id,
            convention_id=convention_id,
            treatment_id=treatment_id,
            partnership_id=partnership_id,
        )

    recommended = result.recommended

    source_ids = tuple(
        source.serialize()
        for source in recommended.sources
    )

    alternatives = tuple(
        decision.candidate
        for decision in result.alternatives
        if decision.candidate is not None
    )

    capability_result = CapabilityResult(
        provider=provider,
        status=ProviderStatus.SUCCESS,
        recommendation=recommended.candidate,
        alternatives=alternatives,
        evidence=ProviderEvidence(
            source_ids=source_ids,
            notes=(
                f"rule_id={recommended.rule_id}",
            ),
        ),
        explanation=recommended.explanation,
    )

    return DecisionEvidence(
        scope=scope,
        result=capability_result,
        system_id=system_id,
        convention_id=convention_id,
        treatment_id=treatment_id,
        partnership_id=partnership_id,
    )
