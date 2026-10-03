"""A7.3 parallel bidding evidence integration tests."""

import pytest

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
)
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.multi_bidding_adviser import BiddingAdviserRequest
from bridge.parallel_bidding_evidence import (
    ParallelBiddingEvidenceResult,
    compose_parallel_bidding_evidence,
)


class StubTransport:
    def __init__(self, observation):
        self.observation = observation
        self.calls = []

    def observe(self, context):
        self.calls.append(context)
        return self.observation


def _context():
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(Seat.NORTH, ("1C", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


def _external(provider_id, recommendation, *, source_id=None):
    observation = ExternalBiddingObservation(
        status=ProviderStatus.SUCCESS,
        recommendation=recommendation,
        source_ids=((source_id or f"{provider_id}:test"),),
        model_id=f"{provider_id}-model",
        explanation=f"{provider_id} recommendation",
    )
    transport = StubTransport(observation)
    adviser = ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.BIDDING,
            implementation=f"{provider_id}-test",
            version="test",
        ),
        transport=transport,
    )
    return adviser, transport


def _bridgelab(call="3C"):
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
        explanation="BridgeLab policy recommendation",
    )
    return DecisionEvidence(
        result=result,
        scope=EvidenceScope.PARTNERSHIP,
        system_id="TWO_OVER_ONE_GF",
        partnership_id="nisim-nily",
    )


def test_two_advisers_feed_one_decision_case_in_request_order():
    ben, ben_transport = _external("ben", "4H")
    brl, brl_transport = _external("brl", "3NT")
    registry = CapabilityProviderRegistry((brl, ben))
    context = _context()

    result = compose_parallel_bidding_evidence(
        case_id="a73-two",
        bridgelab=_bridgelab("3C"),
        registry=registry,
        context=context,
        requests=(
            BiddingAdviserRequest("ben"),
            BiddingAdviserRequest("brl"),
        ),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    assert isinstance(result, ParallelBiddingEvidenceResult)
    assert result.decision_case.case_id == "a73-two"
    assert tuple(
        evidence.result.provider.provider_id
        for evidence in result.decision_case.external
    ) == ("ben", "brl")
    assert result.decision_case.external == result.gathered.evidence
    assert ben_transport.calls == [context]
    assert brl_transport.calls == [context]


def test_each_external_is_compared_independently_with_bridgelab():
    ben, _ = _external("ben", "3C")
    brl, _ = _external("brl", "4H")
    registry = CapabilityProviderRegistry((ben, brl))

    result = compose_parallel_bidding_evidence(
        case_id="a73-disagreement",
        bridgelab=_bridgelab("3C"),
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("ben"),
            BiddingAdviserRequest("brl"),
        ),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    disagreements = result.decision_case.disagreements
    assert len(disagreements) == 2
    assert disagreements[0].left_provider_id == "bridgelab"
    assert disagreements[0].right_provider_id == "ben"
    assert disagreements[0].kind is DisagreementKind.AGREEMENT
    assert disagreements[1].left_provider_id == "bridgelab"
    assert disagreements[1].right_provider_id == "brl"
    assert disagreements[1].kind is DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM


def test_adviser_provenance_and_scope_are_preserved():
    ben, _ = _external("ben", "2H", source_id="ben:live")
    registry = CapabilityProviderRegistry((ben,))

    result = compose_parallel_bidding_evidence(
        case_id="a73-provenance",
        bridgelab=_bridgelab(),
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest(
                "ben",
                system_id="SAYC",
                convention_id="Stayman",
                treatment_id="standard",
                partnership_id="external-pair",
                confidence=0.8,
            ),
        ),
        disagreement_contexts=(DisagreementContext(same_system=False),),
    )

    evidence = result.decision_case.external[0]
    assert evidence.scope is EvidenceScope.PROVIDER
    assert evidence.system_id == "SAYC"
    assert evidence.convention_id == "Stayman"
    assert evidence.treatment_id == "standard"
    assert evidence.partnership_id == "external-pair"
    assert evidence.confidence == 0.8
    assert evidence.result.evidence.source_ids == ("ben:live",)
    assert evidence.result.evidence.model_id == "ben-model"


def test_notes_are_preserved_on_decision_case():
    ben, _ = _external("ben", "2H")
    registry = CapabilityProviderRegistry((ben,))

    result = compose_parallel_bidding_evidence(
        case_id="a73-notes",
        bridgelab=_bridgelab(),
        registry=registry,
        context=_context(),
        requests=(BiddingAdviserRequest("ben"),),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
        ),
        notes=("parallel evidence test",),
    )

    assert result.decision_case.notes == ("parallel evidence test",)


def test_empty_external_request_set_is_valid():
    result = compose_parallel_bidding_evidence(
        case_id="a73-empty",
        bridgelab=_bridgelab(),
        registry=CapabilityProviderRegistry(),
        context=_context(),
        requests=(),
        disagreement_contexts=(),
    )

    assert result.gathered.total == 0
    assert result.decision_case.external == ()
    assert result.decision_case.disagreements == ()


def test_request_and_context_lengths_must_match_before_provider_calls():
    ben, transport = _external("ben", "2H")
    registry = CapabilityProviderRegistry((ben,))

    with pytest.raises(ValueError, match="equal length"):
        compose_parallel_bidding_evidence(
            case_id="a73-length",
            bridgelab=_bridgelab(),
            registry=registry,
            context=_context(),
            requests=(BiddingAdviserRequest("ben"),),
            disagreement_contexts=(),
        )

    assert transport.calls == []


def test_requests_must_be_tuple():
    with pytest.raises(TypeError, match="requests must be a tuple"):
        compose_parallel_bidding_evidence(
            case_id="a73-request-type",
            bridgelab=_bridgelab(),
            registry=CapabilityProviderRegistry(),
            context=_context(),
            requests=[],
            disagreement_contexts=(),
        )


def test_disagreement_contexts_must_be_tuple():
    with pytest.raises(TypeError, match="disagreement_contexts must be a tuple"):
        compose_parallel_bidding_evidence(
            case_id="a73-context-type",
            bridgelab=_bridgelab(),
            registry=CapabilityProviderRegistry(),
            context=_context(),
            requests=(),
            disagreement_contexts=[],
        )


def test_bridge_evidence_is_required():
    with pytest.raises(TypeError, match="bridgelab must be DecisionEvidence"):
        compose_parallel_bidding_evidence(
            case_id="a73-bridge-type",
            bridgelab=object(),
            registry=CapabilityProviderRegistry(),
            context=_context(),
            requests=(),
            disagreement_contexts=(),
        )


def test_external_advisers_are_not_compared_with_each_other():
    ben, _ = _external("ben", "4H")
    brl, _ = _external("brl", "4H")
    registry = CapabilityProviderRegistry((ben, brl))

    result = compose_parallel_bidding_evidence(
        case_id="a73-no-peer-vote",
        bridgelab=_bridgelab("3C"),
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("ben"),
            BiddingAdviserRequest("brl"),
        ),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    pairs = {
        (x.left_provider_id, x.right_provider_id)
        for x in result.decision_case.disagreements
    }
    assert pairs == {
        ("bridgelab", "ben"),
        ("bridgelab", "brl"),
    }
    assert ("ben", "brl") not in pairs
    assert ("brl", "ben") not in pairs


def test_two_matching_external_bids_do_not_override_bridgelab_policy():
    ben, _ = _external("ben", "4H")
    brl, _ = _external("brl", "4H")
    bridge = _bridgelab("3C")
    registry = CapabilityProviderRegistry((ben, brl))

    result = compose_parallel_bidding_evidence(
        case_id="a73-no-majority",
        bridgelab=bridge,
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("ben"),
            BiddingAdviserRequest("brl"),
        ),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    assert result.decision_case.bridgelab is bridge
    assert result.decision_case.bridgelab.recommendation == Call.parse("3C")
    assert tuple(
        x.recommendation for x in result.decision_case.external
    ) == (Call.parse("4H"), Call.parse("4H"))


def test_result_surface_has_no_winner_ranking_or_voting_semantics():
    ben, _ = _external("ben", "4H")
    result = compose_parallel_bidding_evidence(
        case_id="a73-surface",
        bridgelab=_bridgelab(),
        registry=CapabilityProviderRegistry((ben,)),
        context=_context(),
        requests=(BiddingAdviserRequest("ben"),),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
        ),
    )

    for name in (
        "winner",
        "best",
        "rank",
        "ranking",
        "vote",
        "votes",
        "selected",
        "preferred",
        "recommendation",
        "fallback",
    ):
        assert not hasattr(result, name)
