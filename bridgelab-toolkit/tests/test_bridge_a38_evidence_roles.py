"""A3.8 evidence-role tests."""

from bridge.auction import Call
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_evidence import (
    DecisionEvidence,
    EvidenceScope,
)
from bridge.evidence_roles import (
    EvidenceRole,
    RoleEvidence,
    external_recommendation,
    observed_action,
    policy_recommendation,
)


def bidding_evidence(
    provider_id: str,
    call: str,
    scope: EvidenceScope,
) -> DecisionEvidence:
    descriptor = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation=f"{provider_id}-test",
        version="test",
    )

    result = CapabilityResult(
        provider=descriptor,
        status=ProviderStatus.SUCCESS,
        recommendation=Call.parse(call),
    )

    return DecisionEvidence(
        result=result,
        scope=scope,
    )


def test_policy_recommendation_role():
    evidence = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
    )

    tagged = policy_recommendation(evidence)

    assert tagged.role is EvidenceRole.POLICY_RECOMMENDATION
    assert tagged.evidence is evidence


def test_external_recommendation_role():
    evidence = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    tagged = external_recommendation(evidence)

    assert tagged.role is EvidenceRole.EXTERNAL_RECOMMENDATION
    assert tagged.evidence is evidence


def test_same_call_can_have_different_evidence_roles():
    bridgelab = bidding_evidence(
        "bridgelab",
        "4H",
        EvidenceScope.PARTNERSHIP,
    )
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    policy = policy_recommendation(bridgelab)
    external = external_recommendation(ben)

    assert policy.evidence.result.recommendation == Call.parse("4H")
    assert external.evidence.result.recommendation == Call.parse("4H")

    assert policy.role is EvidenceRole.POLICY_RECOMMENDATION
    assert external.role is EvidenceRole.EXTERNAL_RECOMMENDATION


def test_observed_action_is_not_external_recommendation():
    observed = {"source": "expert-corpus", "bid": "4H"}

    tagged = observed_action(observed)

    assert tagged.role is EvidenceRole.OBSERVED_ACTION
    assert tagged.evidence is observed
    assert tagged.role is not EvidenceRole.EXTERNAL_RECOMMENDATION


def test_role_evidence_is_immutable():
    evidence = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    tagged = external_recommendation(evidence)

    try:
        tagged.role = EvidenceRole.POLICY_RECOMMENDATION
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("RoleEvidence must be immutable")


def test_role_does_not_modify_original_evidence():
    evidence = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    original_scope = evidence.scope
    original_result = evidence.result

    tagged = external_recommendation(evidence)

    assert evidence.scope is original_scope
    assert evidence.result is original_result
    assert tagged.evidence is evidence


def test_role_names_are_stable():
    assert EvidenceRole.POLICY_RECOMMENDATION.value == (
        "policy_recommendation"
    )
    assert EvidenceRole.EXTERNAL_RECOMMENDATION.value == (
        "external_recommendation"
    )
    assert EvidenceRole.OBSERVED_ACTION.value == "observed_action"
    assert EvidenceRole.OUTCOME_MEASUREMENT.value == (
        "outcome_measurement"
    )
    assert EvidenceRole.STATISTICAL_ESTIMATE.value == (
        "statistical_estimate"
    )
