"""A3.1 provider-neutral external bidding adviser adapter."""

from dataclasses import dataclass

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_providers import (
    BiddingAdviser,
    Capability,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_evidence import EvidenceScope
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
    ExternalBiddingTransport,
)
from bridge.models import Hand, Seat, Vulnerability


def context():
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(
            Seat.NORTH,
            ("1S", "P"),
        ),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


@dataclass
class FakeTransport:
    observation: ExternalBiddingObservation

    def observe(self, supplied_context):
        assert isinstance(supplied_context, BiddingContext)
        return self.observation


def descriptor():
    return ProviderDescriptor(
        provider_id="external-test",
        capability=Capability.BIDDING,
        implementation="fake-external-adviser",
        version="1",
    )


def adapter(observation):
    return ExternalBiddingAdviserAdapter(
        descriptor=descriptor(),
        transport=FakeTransport(observation),
    )


def test_adapter_satisfies_existing_bidding_adviser_contract():
    adviser = adapter(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="2S",
        )
    )

    assert isinstance(adviser, BiddingAdviser)
    assert isinstance(adviser._transport, ExternalBiddingTransport)


def test_success_normalizes_external_calls_and_provenance():
    adviser = adapter(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="2S",
            alternatives=("3S", "4S"),
            source_ids=("case-17",),
            model_id="model-x",
            notes=("external observation",),
            explanation="provider preferred the major raise",
            elapsed_seconds=0.25,
        )
    )

    result = adviser.advise(context())

    assert result.status is ProviderStatus.SUCCESS
    assert result.recommendation.serialize() == "2S"
    assert tuple(
        call.serialize()
        for call in result.alternatives
    ) == ("3S", "4S")

    assert result.provider == adviser.descriptor
    assert result.evidence.source_ids == ("case-17",)
    assert result.evidence.model_id == "model-x"
    assert result.evidence.notes == ("external observation",)
    assert result.explanation == "provider preferred the major raise"
    assert result.elapsed_seconds == 0.25


@pytest.mark.parametrize(
    "status",
    (
        ProviderStatus.ABSTAIN,
        ProviderStatus.UNAVAILABLE,
        ProviderStatus.FAILED,
    ),
)
def test_non_success_preserves_status_without_fabricating_bid(status):
    adviser = adapter(
        ExternalBiddingObservation(
            status=status,
            explanation="no external recommendation",
        )
    )

    result = adviser.advise(context())

    assert result.status is status
    assert result.recommendation is None
    assert result.alternatives == ()


def test_invalid_external_call_fails_at_adapter_boundary():
    adviser = adapter(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="NOT-A-BID",
        )
    )

    with pytest.raises(ValueError, match="valid bridge call"):
        adviser.advise(context())


def test_non_bidding_descriptor_is_rejected():
    wrong = ProviderDescriptor(
        provider_id="wrong",
        capability=Capability.PLAY,
        implementation="fake",
    )

    with pytest.raises(ValueError, match="BIDDING"):
        ExternalBiddingAdviserAdapter(
            descriptor=wrong,
            transport=FakeTransport(
                ExternalBiddingObservation(
                    status=ProviderStatus.ABSTAIN,
                )
            ),
        )


def test_success_requires_external_recommendation():
    with pytest.raises(ValueError, match="needs a recommendation"):
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
        )


def test_non_success_cannot_smuggle_recommendation():
    with pytest.raises(
        ValueError,
        match="cannot contain recommendations",
    ):
        ExternalBiddingObservation(
            status=ProviderStatus.ABSTAIN,
            recommendation="2S",
        )


def test_evidence_wraps_result_without_promoting_it_to_policy():
    adviser = adapter(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="4S",
            source_ids=("expert-case-9",),
            model_id="external-model",
        )
    )

    evidence = adviser.evidence(
        context(),
        system_id="unknown-external-system",
        partnership_id="external-pair",
        confidence=0.72,
    )

    assert evidence.scope is EvidenceScope.PROVIDER
    assert evidence.recommendation.serialize() == "4S"
    assert evidence.system_id == "unknown-external-system"
    assert evidence.partnership_id == "external-pair"
    assert evidence.confidence == 0.72


def test_external_system_can_remain_unknown():
    adviser = adapter(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="3S",
        )
    )

    evidence = adviser.evidence(context())

    assert evidence.system_id is None
    assert evidence.convention_id is None
    assert evidence.treatment_id is None
    assert evidence.partnership_id is None


def test_adapter_does_not_mutate_context():
    original = context()

    original_hand = original.hand
    original_auction = original.auction
    original_vulnerability = original.vulnerability
    original_system = original.system

    adviser = adapter(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="2S",
        )
    )

    adviser.advise(original)

    assert original.hand is original_hand
    assert original.auction is original_auction
    assert original.vulnerability is original_vulnerability
    assert original.system is original_system
