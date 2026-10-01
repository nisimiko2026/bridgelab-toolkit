"""A3.4 end-to-end BEN evidence integration.

The tests prove that a registered BEN adviser can contribute provider evidence
to disagreement analysis without becoming BridgeLab policy, without inferring
BEN's bidding system, and without selecting a winner.
"""

from bridge.auction import Auction, Call
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.capability_registry import CapabilityProviderRegistry
from bridge.decision_evidence import (
    DecisionEvidence,
    DisagreementContext,
    DisagreementKind,
    EvidenceScope,
    classify_disagreement,
)
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)
from bridge.models import Hand, Seat, Vulnerability


class StubBenTransport:
    """Offline BEN stand-in: transport behavior only, no policy semantics."""

    def __init__(
        self,
        observation: ExternalBiddingObservation,
    ) -> None:
        self.observation = observation
        self.calls = 0

    def observe(
        self,
        context: BiddingContext,
    ) -> ExternalBiddingObservation:
        self.calls += 1
        return self.observation


def context() -> BiddingContext:
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(
            Seat.NORTH,
            ("1C", "P"),
        ),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


def ben_adviser(
    observation: ExternalBiddingObservation,
) -> ExternalBiddingAdviserAdapter:
    return ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id="ben",
            capability=Capability.BIDDING,
            implementation="ben-rest",
            version="test",
        ),
        transport=StubBenTransport(observation),
    )


def bridgelab_evidence(
    call: str = "3C",
) -> DecisionEvidence:
    descriptor = ProviderDescriptor(
        provider_id="bridgelab",
        capability=Capability.BIDDING,
        implementation="bridgelab-policy",
        version="test",
    )

    result = CapabilityResult(
        provider=descriptor,
        status=ProviderStatus.SUCCESS,
        recommendation=Call.parse(call),
        explanation="BridgeLab policy recommendation.",
    )

    return DecisionEvidence(
        result=result,
        scope=EvidenceScope.PARTNERSHIP,
        system_id="TWO_OVER_ONE_GF",
        partnership_id="nisim-nily",
    )


def test_registered_ben_can_produce_decision_evidence():
    registry = CapabilityProviderRegistry()

    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="4H",
            alternatives=("3H",),
            source_ids=("ben:test",),
            model_id="ben-test-model",
            explanation="BEN recommendation.",
        )
    )
    registry.register(adviser)

    registered = registry.require(
        Capability.BIDDING,
        "ben",
    )
    evidence = registered.evidence(context())

    assert evidence.scope is EvidenceScope.PROVIDER
    assert evidence.result.provider.provider_id == "ben"
    assert evidence.recommendation == Call.parse("4H")
    assert evidence.result.alternatives == (
        Call.parse("3H"),
    )
    assert evidence.result.evidence.source_ids == (
        "ben:test",
    )
    assert (
        evidence.result.evidence.model_id
        == "ben-test-model"
    )


def test_ben_system_remains_unknown_unless_explicitly_supplied():
    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="4H",
        )
    )

    evidence = adviser.evidence(context())

    assert evidence.system_id is None
    assert evidence.convention_id is None
    assert evidence.treatment_id is None
    assert evidence.partnership_id is None


def test_different_ben_bid_with_unknown_system_is_not_policy_gap():
    bridge = bridgelab_evidence("3C")

    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="4H",
        )
    )
    ben = adviser.evidence(context())

    disagreement = classify_disagreement(
        bridge,
        ben,
        context=DisagreementContext(
            external_system_known=False,
            bridgelab_policy_expected=True,
        ),
    )

    assert (
        disagreement.kind
        is DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM
    )
    assert (
        disagreement.left_provider_id
        == "bridgelab"
    )
    assert disagreement.right_provider_id == "ben"


def test_same_bid_is_agreement_even_when_external_system_unknown():
    bridge = bridgelab_evidence("3C")

    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="3C",
        )
    )
    ben = adviser.evidence(context())

    disagreement = classify_disagreement(
        bridge,
        ben,
        context=DisagreementContext(
            external_system_known=False,
        ),
    )

    assert (
        disagreement.kind
        is DisagreementKind.AGREEMENT
    )


def test_ben_abstention_remains_external_model_abstention():
    bridge = bridgelab_evidence("3C")

    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=ProviderStatus.ABSTAIN,
            explanation="BEN abstained.",
        )
    )
    ben = adviser.evidence(context())

    disagreement = classify_disagreement(
        bridge,
        ben,
        context=DisagreementContext(
            external_system_known=False,
        ),
    )

    assert ben.recommendation is None
    assert (
        disagreement.kind
        is DisagreementKind.EXTERNAL_MODEL_ABSTAIN
    )


def test_evidence_collection_does_not_change_registry_selection_semantics():
    registry = CapabilityProviderRegistry()

    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="4H",
        )
    )
    registry.register(adviser)

    assert registry.providers_for(
        Capability.BIDDING
    ) == (adviser,)

    evidence = adviser.evidence(context())

    assert evidence.recommendation == Call.parse("4H")
    assert registry.providers_for(
        Capability.BIDDING
    ) == (adviser,)


def test_explicit_external_system_can_be_recorded_without_inference():
    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="4H",
        )
    )

    evidence = adviser.evidence(
        context(),
        system_id="explicit-test-system",
    )

    assert evidence.system_id == "explicit-test-system"


def test_ben_evidence_does_not_mutate_bridgelab_evidence():
    bridge = bridgelab_evidence("3C")

    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="4H",
        )
    )
    ben = adviser.evidence(context())

    assert bridge.recommendation == Call.parse("3C")
    assert ben.recommendation == Call.parse("4H")
    assert (
        bridge.result.provider.provider_id
        == "bridgelab"
    )
    assert ben.result.provider.provider_id == "ben"
