"""A7.4 abstention / failure isolation tests."""

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
from bridge.decision_evidence import DecisionEvidence, EvidenceScope
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)
from bridge.isolated_bidding_evidence import (
    AdviserFailure,
    IsolatedMultiAdviserBiddingResult,
    gather_bidding_adviser_evidence_isolated,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.multi_bidding_adviser import BiddingAdviserRequest


def _context():
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(Seat.NORTH, ("1C", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


class StubTransport:
    def __init__(self, observation):
        self.observation = observation
        self.calls = 0

    def observe(self, context):
        self.calls += 1
        return self.observation


def _external(provider_id, status, recommendation=None):
    transport = StubTransport(
        ExternalBiddingObservation(
            status=status,
            recommendation=recommendation,
            source_ids=(f"{provider_id}:test",),
            model_id=f"{provider_id}-model",
        )
    )
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


class RaisingAdviser:
    def __init__(self, provider_id="broken"):
        self.descriptor = ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.BIDDING,
            implementation="raising-test",
            version="test",
        )
        self.calls = 0

    def advise(self, context):
        raise AssertionError("advise should not be called")

    def evidence(self, context, **kwargs):
        self.calls += 1
        raise RuntimeError("provider exploded")


class BadEvidenceAdviser:
    descriptor = ProviderDescriptor(
        provider_id="bad-contract",
        capability=Capability.BIDDING,
        implementation="bad-contract-test",
    )

    def advise(self, context):
        raise AssertionError("advise should not be called")

    def evidence(self, context, **kwargs):
        return object()


def test_success_abstain_unavailable_and_failed_are_preserved():
    providers = [
        _external("success", ProviderStatus.SUCCESS, "1S")[0],
        _external("abstain", ProviderStatus.ABSTAIN)[0],
        _external("unavailable", ProviderStatus.UNAVAILABLE)[0],
        _external("failed", ProviderStatus.FAILED)[0],
    ]
    registry = CapabilityProviderRegistry(providers)

    result = gather_bidding_adviser_evidence_isolated(
        registry=registry,
        context=_context(),
        requests=tuple(BiddingAdviserRequest(x.descriptor.provider_id) for x in providers),
    )

    assert tuple(x.result.status for x in result.evidence) == (
        ProviderStatus.SUCCESS,
        ProviderStatus.ABSTAIN,
        ProviderStatus.UNAVAILABLE,
        ProviderStatus.FAILED,
    )
    assert result.failures == ()


def test_runtime_exception_becomes_failed_evidence():
    broken = RaisingAdviser()
    registry = CapabilityProviderRegistry((broken,))

    result = gather_bidding_adviser_evidence_isolated(
        registry=registry,
        context=_context(),
        requests=(BiddingAdviserRequest("broken"),),
    )

    assert isinstance(result, IsolatedMultiAdviserBiddingResult)
    assert result.evidence[0].result.status is ProviderStatus.FAILED
    assert result.evidence[0].recommendation is None
    assert result.evidence[0].scope is EvidenceScope.PROVIDER
    assert len(result.failures) == 1
    assert result.failures[0] == AdviserFailure(
        provider_id="broken",
        exception_type="RuntimeError",
        message="provider exploded",
    )


def test_runtime_failure_does_not_stop_later_adviser():
    broken = RaisingAdviser()
    good, good_transport = _external("good", ProviderStatus.SUCCESS, "2H")
    registry = CapabilityProviderRegistry((broken, good))

    result = gather_bidding_adviser_evidence_isolated(
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("broken"),
            BiddingAdviserRequest("good"),
        ),
    )

    assert broken.calls == 1
    assert good_transport.calls == 1
    assert tuple(x.result.status for x in result.evidence) == (
        ProviderStatus.FAILED,
        ProviderStatus.SUCCESS,
    )
    assert result.evidence[1].recommendation == Call.parse("2H")


def test_runtime_failure_does_not_stop_adviser_after_or_before_it():
    first, first_transport = _external("first", ProviderStatus.SUCCESS, "1S")
    broken = RaisingAdviser()
    last, last_transport = _external("last", ProviderStatus.ABSTAIN)
    registry = CapabilityProviderRegistry((first, broken, last))

    result = gather_bidding_adviser_evidence_isolated(
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("first"),
            BiddingAdviserRequest("broken"),
            BiddingAdviserRequest("last"),
        ),
    )

    assert first_transport.calls == 1
    assert broken.calls == 1
    assert last_transport.calls == 1
    assert tuple(x.result.status for x in result.evidence) == (
        ProviderStatus.SUCCESS,
        ProviderStatus.FAILED,
        ProviderStatus.ABSTAIN,
    )


def test_failed_exception_evidence_preserves_request_metadata():
    broken = RaisingAdviser()
    registry = CapabilityProviderRegistry((broken,))

    result = gather_bidding_adviser_evidence_isolated(
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest(
                "broken",
                system_id="SAYC",
                convention_id="Stayman",
                treatment_id="standard",
                partnership_id="pair-x",
                confidence=0.7,
            ),
        ),
    )

    evidence = result.evidence[0]
    assert evidence.system_id == "SAYC"
    assert evidence.convention_id == "Stayman"
    assert evidence.treatment_id == "standard"
    assert evidence.partnership_id == "pair-x"
    assert evidence.confidence == 0.7


def test_failed_exception_records_failure_details_without_recommendation():
    broken = RaisingAdviser()
    registry = CapabilityProviderRegistry((broken,))

    result = gather_bidding_adviser_evidence_isolated(
        registry=registry,
        context=_context(),
        requests=(BiddingAdviserRequest("broken"),),
    )

    capability = result.evidence[0].result
    assert capability.recommendation is None
    assert capability.alternatives == ()
    assert "RuntimeError: provider exploded" in capability.evidence.notes
    assert "no recommendation was fabricated" in capability.explanation


def test_request_order_is_preserved_across_failures():
    good_a, _ = _external("a", ProviderStatus.SUCCESS, "1S")
    broken = RaisingAdviser("b")
    good_c, _ = _external("c", ProviderStatus.SUCCESS, "2H")
    registry = CapabilityProviderRegistry((good_c, broken, good_a))

    result = gather_bidding_adviser_evidence_isolated(
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("a"),
            BiddingAdviserRequest("b"),
            BiddingAdviserRequest("c"),
        ),
    )

    assert tuple(x.provider_id for x in result.gathered.observations) == (
        "a", "b", "c"
    )


def test_unknown_provider_remains_configuration_error():
    registry = CapabilityProviderRegistry()

    with pytest.raises(KeyError):
        gather_bidding_adviser_evidence_isolated(
            registry=registry,
            context=_context(),
            requests=(BiddingAdviserRequest("missing"),),
        )


def test_invalid_evidence_return_remains_contract_error():
    registry = CapabilityProviderRegistry((BadEvidenceAdviser(),))

    with pytest.raises(TypeError, match="must return DecisionEvidence"):
        gather_bidding_adviser_evidence_isolated(
            registry=registry,
            context=_context(),
            requests=(BiddingAdviserRequest("bad-contract"),),
        )


def test_duplicate_requests_are_rejected_before_any_provider_call():
    good, transport = _external("good", ProviderStatus.SUCCESS, "1S")
    registry = CapabilityProviderRegistry((good,))

    with pytest.raises(ValueError, match="must be unique"):
        gather_bidding_adviser_evidence_isolated(
            registry=registry,
            context=_context(),
            requests=(
                BiddingAdviserRequest("good"),
                BiddingAdviserRequest("GOOD"),
            ),
        )

    assert transport.calls == 0


def test_empty_requests_are_valid():
    result = gather_bidding_adviser_evidence_isolated(
        registry=CapabilityProviderRegistry(),
        context=_context(),
        requests=(),
    )

    assert result.gathered.total == 0
    assert result.evidence == ()
    assert result.failures == ()


def test_requests_must_be_tuple():
    with pytest.raises(TypeError, match="requests must be a tuple"):
        gather_bidding_adviser_evidence_isolated(
            registry=CapabilityProviderRegistry(),
            context=_context(),
            requests=[],
        )


def test_failure_result_has_no_winner_vote_or_fallback_surface():
    broken = RaisingAdviser()
    result = gather_bidding_adviser_evidence_isolated(
        registry=CapabilityProviderRegistry((broken,)),
        context=_context(),
        requests=(BiddingAdviserRequest("broken"),),
    )

    for name in (
        "winner", "best", "rank", "ranking", "vote", "votes",
        "selected", "preferred", "fallback",
    ):
        assert not hasattr(result, name)
