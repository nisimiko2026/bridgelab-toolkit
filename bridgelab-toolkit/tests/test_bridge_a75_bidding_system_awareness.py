"""A7.5 bidding system-awareness tests."""

import pytest

from bridge.auction import Call
from bridge.bidding_system_awareness import (
    BiddingSystemRelationship,
    bidding_system_relationship,
    system_aware_disagreement_context,
    system_aware_disagreement_contexts,
)
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_evidence import (
    DecisionEvidence,
    DisagreementKind,
    EvidenceScope,
    classify_disagreement,
)


def _evidence(provider_id, call, *, system_id=None):
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
        scope=(
            EvidenceScope.PARTNERSHIP
            if provider_id == "bridgelab"
            else EvidenceScope.PROVIDER
        ),
        system_id=system_id,
    )


def test_unknown_external_system_stays_unknown():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")
    external = _evidence("ben", "4S")

    relationship = bidding_system_relationship(bridge, external)

    assert relationship == BiddingSystemRelationship(
        bridgelab_system_id="TWO_OVER_ONE_GF",
        external_system_id=None,
        external_system_known=False,
        same_system=None,
    )


def test_known_same_system_is_detected_case_insensitively():
    bridge = _evidence("bridgelab", "3NT", system_id="Two_Over_One_GF")
    external = _evidence("ai-2", "4S", system_id="two_over_one_gf")

    relationship = bidding_system_relationship(bridge, external)

    assert relationship.external_system_known is True
    assert relationship.same_system is True


def test_known_different_system_is_detected():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")
    external = _evidence("ai-2", "4S", system_id="SAYC")

    relationship = bidding_system_relationship(bridge, external)

    assert relationship.external_system_known is True
    assert relationship.same_system is False


def test_known_external_with_unknown_bridgelab_system_does_not_guess():
    bridge = _evidence("bridgelab", "3NT")
    external = _evidence("ai-2", "4S", system_id="SAYC")

    relationship = bidding_system_relationship(bridge, external)

    assert relationship.external_system_known is True
    assert relationship.same_system is None


def test_unknown_external_system_drives_unknown_system_disagreement():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")
    external = _evidence("ben", "4S")

    context = system_aware_disagreement_context(bridge, external)
    disagreement = classify_disagreement(bridge, external, context=context)

    assert disagreement.kind is DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM


def test_explicit_different_system_drives_system_difference():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")
    external = _evidence("ai-2", "4S", system_id="SAYC")

    context = system_aware_disagreement_context(bridge, external)
    disagreement = classify_disagreement(bridge, external, context=context)

    assert disagreement.kind is DisagreementKind.SYSTEM_DIFFERENCE


def test_same_system_different_bid_can_remain_judgment_difference():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")
    external = _evidence("ai-2", "4S", system_id="two_over_one_gf")

    context = system_aware_disagreement_context(bridge, external)
    disagreement = classify_disagreement(bridge, external, context=context)

    assert disagreement.kind is DisagreementKind.JUDGMENT_DIFFERENCE


def test_same_bid_is_agreement_even_when_external_system_is_unknown():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")
    external = _evidence("ben", "3NT")

    context = system_aware_disagreement_context(bridge, external)
    disagreement = classify_disagreement(bridge, external, context=context)

    assert disagreement.kind is DisagreementKind.AGREEMENT


def test_provider_name_does_not_imply_system():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")

    for provider_id in ("ben", "sayc-engine", "two-over-one-ai", "precision-bot"):
        external = _evidence(provider_id, "4S")
        relationship = bidding_system_relationship(bridge, external)
        assert relationship.external_system_known is False
        assert relationship.same_system is None


def test_recommendation_does_not_imply_system():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")

    for call in ("1C", "1NT", "2C", "4S"):
        external = _evidence("external", call)
        relationship = bidding_system_relationship(bridge, external)
        assert relationship.external_system_known is False


def test_optional_semantic_context_is_preserved():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")
    external = _evidence("ai-2", "4S", system_id="TWO_OVER_ONE_GF")

    context = system_aware_disagreement_context(
        bridge,
        external,
        same_convention=False,
        same_treatment=False,
        same_partnership_agreement=False,
        bridgelab_policy_expected=True,
        engine_defect_evidence=True,
    )

    assert context.external_system_known is True
    assert context.same_system is True
    assert context.same_convention is False
    assert context.same_treatment is False
    assert context.same_partnership_agreement is False
    assert context.bridgelab_policy_expected is True
    assert context.engine_defect_evidence is True


def test_contexts_are_built_independently_per_adviser():
    bridge = _evidence("bridgelab", "3NT", system_id="TWO_OVER_ONE_GF")
    external = (
        _evidence("ben", "4S"),
        _evidence("sayc-ai", "4H", system_id="SAYC"),
        _evidence("two-one-ai", "3NT", system_id="TWO_OVER_ONE_GF"),
    )

    contexts = system_aware_disagreement_contexts(bridge, external)

    assert tuple(x.external_system_known for x in contexts) == (
        False, True, True
    )
    assert tuple(x.same_system for x in contexts) == (
        None, False, True
    )


def test_relationship_rejects_unknown_external_with_same_system_claim():
    with pytest.raises(ValueError, match="unknown external system"):
        BiddingSystemRelationship(
            bridgelab_system_id="SAYC",
            external_system_id=None,
            external_system_known=False,
            same_system=True,
        )


def test_contexts_require_tuple():
    bridge = _evidence("bridgelab", "3NT", system_id="SAYC")
    with pytest.raises(TypeError, match="external must be a tuple"):
        system_aware_disagreement_contexts(bridge, [])


def test_relationship_requires_decision_evidence():
    evidence = _evidence("bridgelab", "3NT", system_id="SAYC")

    with pytest.raises(TypeError, match="bridgelab must be DecisionEvidence"):
        bidding_system_relationship(object(), evidence)

    with pytest.raises(TypeError, match="external must be DecisionEvidence"):
        bidding_system_relationship(evidence, object())
