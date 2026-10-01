"""A3.6 BEN disagreement composition integration.

The tests prove that BridgeLab and BEN evidence can be assembled into
one DecisionCase without ranking, voting, policy promotion, or
inference of BEN's bidding system.
"""

from bridge.auction import Auction, Call
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_case_composition import compose_bidding_decision_case
from bridge.decision_evidence import (
    DecisionEvidence,
    DisagreementContext,
    DisagreementKind,
    EvidenceScope,
)
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)
from bridge.models import Hand, Seat, Vulnerability


class StubBenTransport:
    """Offline BEN stand-in used only at the transport boundary."""

    def __init__(
        self,
        observation: ExternalBiddingObservation,
    ) -> None:
        self.observation = observation

    def observe(
        self,
        context: BiddingContext,
    ) -> ExternalBiddingObservation:
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


def ben_evidence(
    *,
    recommendation: str | None = "4H",
    status: ProviderStatus = ProviderStatus.SUCCESS,
) -> DecisionEvidence:
    adviser = ben_adviser(
        ExternalBiddingObservation(
            status=status,
            recommendation=recommendation,
            explanation="BEN recommendation.",
        )
    )
    return adviser.evidence(context())


def test_composes_bridgelab_and_ben_into_one_decision_case():
    bridge = bridgelab_evidence("3C")
    ben = ben_evidence(recommendation="4H")

    case = compose_bidding_decision_case(
        case_id="a36-ben-001",
        bridgelab=bridge,
        external=ben,
        disagreement_context=DisagreementContext(
            external_system_known=False,
        ),
    )

    assert case.case_id == "a36-ben-001"
    assert case.bridgelab is bridge
    assert case.external == (ben,)
    assert len(case.disagreements) == 1


def test_unknown_ben_system_remains_unknown_external_system():
    case = compose_bidding_decision_case(
        case_id="a36-ben-002",
        bridgelab=bridgelab_evidence("3C"),
        external=ben_evidence(recommendation="4H"),
        disagreement_context=DisagreementContext(
            external_system_known=False,
            bridgelab_policy_expected=True,
        ),
    )

    assert (
        case.disagreements[0].kind
        is DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM
    )


def test_same_bid_is_recorded_as_agreement():
    case = compose_bidding_decision_case(
        case_id="a36-ben-003",
        bridgelab=bridgelab_evidence("3C"),
        external=ben_evidence(recommendation="3C"),
        disagreement_context=DisagreementContext(
            external_system_known=False,
        ),
    )

    assert (
        case.disagreements[0].kind
        is DisagreementKind.AGREEMENT
    )


def test_ben_abstention_is_preserved():
    case = compose_bidding_decision_case(
        case_id="a36-ben-004",
        bridgelab=bridgelab_evidence("3C"),
        external=ben_evidence(
            recommendation=None,
            status=ProviderStatus.ABSTAIN,
        ),
        disagreement_context=DisagreementContext(
            external_system_known=False,
        ),
    )

    assert case.external[0].recommendation is None
    assert (
        case.disagreements[0].kind
        is DisagreementKind.EXTERNAL_MODEL_ABSTAIN
    )


def test_external_evidence_remains_provider_scoped():
    ben = ben_evidence(recommendation="4H")

    case = compose_bidding_decision_case(
        case_id="a36-ben-005",
        bridgelab=bridgelab_evidence("3C"),
        external=ben,
        disagreement_context=DisagreementContext(
            external_system_known=False,
        ),
    )

    assert case.external[0].scope is EvidenceScope.PROVIDER
    assert case.external[0].system_id is None
    assert case.external[0].convention_id is None
    assert case.external[0].treatment_id is None
    assert case.external[0].partnership_id is None


def test_bridgelab_policy_evidence_remains_separate():
    bridge = bridgelab_evidence("3C")

    case = compose_bidding_decision_case(
        case_id="a36-ben-006",
        bridgelab=bridge,
        external=ben_evidence(recommendation="4H"),
        disagreement_context=DisagreementContext(
            external_system_known=False,
        ),
    )

    assert case.bridgelab is bridge
    assert case.bridgelab.scope is EvidenceScope.PARTNERSHIP
    assert case.bridgelab.system_id == "TWO_OVER_ONE_GF"
    assert case.bridgelab.partnership_id == "nisim-nily"
    assert case.bridgelab.recommendation == Call.parse("3C")


def test_provider_identity_is_preserved_in_disagreement():
    case = compose_bidding_decision_case(
        case_id="a36-ben-007",
        bridgelab=bridgelab_evidence("3C"),
        external=ben_evidence(recommendation="4H"),
        disagreement_context=DisagreementContext(
            external_system_known=False,
        ),
    )

    disagreement = case.disagreements[0]

    assert disagreement.left_provider_id == "bridgelab"
    assert disagreement.right_provider_id == "ben"


def test_notes_are_preserved_without_affecting_evidence():
    bridge = bridgelab_evidence("3C")
    ben = ben_evidence(recommendation="4H")

    case = compose_bidding_decision_case(
        case_id="a36-ben-008",
        bridgelab=bridge,
        external=ben,
        disagreement_context=DisagreementContext(
            external_system_known=False,
        ),
        notes=("A3.6 BEN comparison.",),
    )

    assert case.notes == ("A3.6 BEN comparison.",)
    assert case.bridgelab is bridge
    assert case.external == (ben,)
