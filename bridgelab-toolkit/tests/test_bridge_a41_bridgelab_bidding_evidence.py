"""A4.1 BridgeLab production bidding evidence adapter tests."""

import pytest

from bridge.auction import Call
from bridge.bidding_engine import BiddingEngineResult
from bridge.bidding_rules import KnowledgeSource, RuleDecision
from bridge.bridgelab_bidding_evidence import (
    BRIDGELAB_BIDDING_IMPLEMENTATION,
    BRIDGELAB_BIDDING_PROVIDER_ID,
    bidding_result_to_evidence,
    bridgelab_bidding_provider,
)
from bridge.capability_providers import (
    Capability,
    ProviderStatus,
)
from bridge.decision_evidence import EvidenceScope


def decision(
    *,
    rule_id: str,
    call: str,
    explanation: str = "Source-grounded recommendation.",
    article_id: str = "bidding/test-policy",
    heading: str | None = None,
    priority: int = 0,
) -> RuleDecision:
    return RuleDecision.recommend(
        rule_id=rule_id,
        candidate=Call.parse(call),
        explanation=explanation,
        sources=(
            KnowledgeSource(
                article_id=article_id,
                heading=heading,
            ),
        ),
        priority=priority,
    )


def test_provider_descriptor_identifies_bridgelab_bidding_engine():
    provider = bridgelab_bidding_provider()

    assert provider.provider_id == BRIDGELAB_BIDDING_PROVIDER_ID
    assert provider.capability is Capability.BIDDING
    assert provider.implementation == BRIDGELAB_BIDDING_IMPLEMENTATION


def test_recommended_call_becomes_successful_decision_evidence():
    recommended = decision(
        rule_id="test.opening",
        call="1S",
    )

    result = BiddingEngineResult(
        recommended=recommended,
        alternatives=(),
        decisions=(recommended,),
    )

    evidence = bidding_result_to_evidence(
        result,
        scope=EvidenceScope.SYSTEM,
        system_id="2/1",
    )

    assert evidence.scope is EvidenceScope.SYSTEM
    assert evidence.system_id == "2/1"
    assert evidence.result.status is ProviderStatus.SUCCESS
    assert evidence.recommendation == Call.parse("1S")


def test_canonical_source_provenance_is_preserved():
    recommended = decision(
        rule_id="test.source",
        call="2H",
        article_id="conventions/test-convention",
        heading="Responder continuation",
    )

    result = BiddingEngineResult(
        recommended=recommended,
        alternatives=(),
        decisions=(recommended,),
    )

    evidence = bidding_result_to_evidence(
        result,
        scope=EvidenceScope.CONVENTION,
        convention_id="test-convention",
    )

    assert evidence.result.evidence.source_ids == (
        "conventions/test-convention#Responder continuation",
    )


def test_rule_identity_is_preserved_as_provider_evidence_note():
    recommended = decision(
        rule_id="test.rule.identity",
        call="3C",
    )

    result = BiddingEngineResult(
        recommended=recommended,
        alternatives=(),
        decisions=(recommended,),
    )

    evidence = bidding_result_to_evidence(
        result,
        scope=EvidenceScope.TREATMENT,
        treatment_id="test-treatment",
    )

    assert evidence.result.evidence.notes == (
        "rule_id=test.rule.identity",
    )


def test_explanation_is_preserved():
    recommended = decision(
        rule_id="test.explanation",
        call="1NT",
        explanation="Balanced hand in the configured range.",
    )

    result = BiddingEngineResult(
        recommended=recommended,
        alternatives=(),
        decisions=(recommended,),
    )

    evidence = bidding_result_to_evidence(
        result,
        scope=EvidenceScope.SYSTEM,
    )

    assert evidence.result.explanation == (
        "Balanced hand in the configured range."
    )


def test_alternatives_preserve_engine_order():
    recommended = decision(
        rule_id="test.primary",
        call="1S",
    )
    first_alternative = decision(
        rule_id="test.alt.one",
        call="1NT",
    )
    second_alternative = decision(
        rule_id="test.alt.two",
        call="2S",
    )

    result = BiddingEngineResult(
        recommended=recommended,
        alternatives=(
            first_alternative,
            second_alternative,
        ),
        decisions=(
            recommended,
            first_alternative,
            second_alternative,
        ),
    )

    evidence = bidding_result_to_evidence(
        result,
        scope=EvidenceScope.SYSTEM,
    )

    assert evidence.result.alternatives == (
        Call.parse("1NT"),
        Call.parse("2S"),
    )


def test_abstention_remains_explicit_abstention():
    result = BiddingEngineResult(
        recommended=None,
        alternatives=(),
        decisions=(),
    )

    evidence = bidding_result_to_evidence(
        result,
        scope=EvidenceScope.PARTNERSHIP,
        partnership_id="nisim-nily",
    )

    assert evidence.scope is EvidenceScope.PARTNERSHIP
    assert evidence.partnership_id == "nisim-nily"
    assert evidence.result.status is ProviderStatus.ABSTAIN
    assert evidence.recommendation is None
    assert evidence.result.alternatives == ()


def test_scope_and_policy_identity_are_not_inferred():
    recommended = decision(
        rule_id="test.explicit.scope",
        call="4H",
    )

    result = BiddingEngineResult(
        recommended=recommended,
        alternatives=(),
        decisions=(recommended,),
    )

    evidence = bidding_result_to_evidence(
        result,
        scope=EvidenceScope.TREATMENT,
    )

    assert evidence.scope is EvidenceScope.TREATMENT
    assert evidence.system_id is None
    assert evidence.convention_id is None
    assert evidence.treatment_id is None
    assert evidence.partnership_id is None


def test_all_explicit_policy_ids_are_preserved():
    recommended = decision(
        rule_id="test.ids",
        call="3D",
    )

    result = BiddingEngineResult(
        recommended=recommended,
        alternatives=(),
        decisions=(recommended,),
    )

    evidence = bidding_result_to_evidence(
        result,
        scope=EvidenceScope.PARTNERSHIP,
        system_id="2/1",
        convention_id="bergen",
        treatment_id="nisim-nily-bergen",
        partnership_id="nisim-nily",
    )

    assert evidence.system_id == "2/1"
    assert evidence.convention_id == "bergen"
    assert evidence.treatment_id == "nisim-nily-bergen"
    assert evidence.partnership_id == "nisim-nily"


def test_invalid_result_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="result must be BiddingEngineResult",
    ):
        bidding_result_to_evidence(
            object(),
            scope=EvidenceScope.SYSTEM,
        )


def test_invalid_scope_type_is_rejected():
    result = BiddingEngineResult(
        recommended=None,
        alternatives=(),
        decisions=(),
    )

    with pytest.raises(
        TypeError,
        match="scope must be EvidenceScope",
    ):
        bidding_result_to_evidence(
            result,
            scope="system",
        )


def test_adapter_does_not_mutate_engine_result():
    recommended = decision(
        rule_id="test.immutable",
        call="1D",
    )

    result = BiddingEngineResult(
        recommended=recommended,
        alternatives=(),
        decisions=(recommended,),
    )

    original_decisions = result.decisions

    bidding_result_to_evidence(
        result,
        scope=EvidenceScope.SYSTEM,
    )

    assert result.recommended is recommended
    assert result.decisions is original_decisions
    assert result.decisions[0] is recommended
