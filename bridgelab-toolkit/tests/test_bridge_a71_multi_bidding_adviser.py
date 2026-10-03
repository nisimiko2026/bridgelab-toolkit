"""A7.1 multi-adviser bidding contract tests."""

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_providers import (
    Capability,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.capability_registry import CapabilityProviderRegistry
from bridge.decision_evidence import DecisionEvidence, EvidenceScope
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.multi_bidding_adviser import (
    BiddingAdviserEvidence,
    BiddingAdviserRequest,
    MultiAdviserBiddingResult,
    gather_bidding_adviser_evidence,
)


class StubTransport:
    def __init__(self, observation):
        self.observation = observation
        self.calls = []

    def observe(self, context):
        self.calls.append(context)
        return self.observation


def _descriptor(provider_id):
    return ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation=f"{provider_id}-test",
    )


def _provider(provider_id, recommendation, *, status=ProviderStatus.SUCCESS):
    observation = ExternalBiddingObservation(
        status=status,
        recommendation=recommendation if status is ProviderStatus.SUCCESS else None,
        model_id=f"{provider_id}-model",
    )
    transport = StubTransport(observation)
    adviser = ExternalBiddingAdviserAdapter(
        descriptor=_descriptor(provider_id),
        transport=transport,
    )
    return adviser, transport


def _context():
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(Seat.NORTH, ("1C", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


def test_request_normalizes_metadata():
    request = BiddingAdviserRequest(
        " ben ",
        system_id=" SAYC ",
        convention_id=" Stayman ",
        treatment_id=" standard ",
        partnership_id=" pair-a ",
        confidence=0.75,
    )
    assert request.provider_id == "ben"
    assert request.system_id == "SAYC"
    assert request.convention_id == "Stayman"
    assert request.treatment_id == "standard"
    assert request.partnership_id == "pair-a"
    assert request.confidence == 0.75


@pytest.mark.parametrize(
    "kwargs",
    [
        {"provider_id": ""},
        {"provider_id": " "},
        {"provider_id": "ben", "system_id": ""},
        {"provider_id": "ben", "convention_id": " "},
        {"provider_id": "ben", "treatment_id": ""},
        {"provider_id": "ben", "partnership_id": " "},
    ],
)
def test_request_rejects_blank_identifiers(kwargs):
    with pytest.raises(ValueError):
        BiddingAdviserRequest(**kwargs)


@pytest.mark.parametrize("confidence", (-0.01, 1.01))
def test_request_rejects_out_of_range_confidence(confidence):
    with pytest.raises(ValueError):
        BiddingAdviserRequest("ben", confidence=confidence)


@pytest.mark.parametrize("confidence", (True, "0.5"))
def test_request_rejects_non_numeric_confidence(confidence):
    with pytest.raises(TypeError):
        BiddingAdviserRequest("ben", confidence=confidence)


def test_gather_calls_multiple_registered_advisers_in_request_order():
    ben, ben_transport = _provider("ben", "1S")
    other, other_transport = _provider("other-ai", "1NT")
    registry = CapabilityProviderRegistry((other, ben))
    context = _context()

    result = gather_bidding_adviser_evidence(
        registry=registry,
        context=context,
        requests=(
            BiddingAdviserRequest("ben"),
            BiddingAdviserRequest("other-ai"),
        ),
    )

    assert result.total == 2
    assert tuple(item.provider_id for item in result.observations) == (
        "ben",
        "other-ai",
    )
    assert result.observation("BEN").evidence.result.recommendation == Call.parse("1S")
    assert result.observation("other-ai").evidence.result.recommendation == Call.parse("1NT")
    assert ben_transport.calls == [context]
    assert other_transport.calls == [context]


def test_gather_preserves_system_and_partnership_scope():
    ben, _ = _provider("ben", "2H")
    registry = CapabilityProviderRegistry((ben,))

    result = gather_bidding_adviser_evidence(
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest(
                "ben",
                system_id="external-system-unknown",
                convention_id="external-convention",
                treatment_id="external-treatment",
                partnership_id="external-pair",
                confidence=0.6,
            ),
        ),
    )

    evidence = result.observation("ben").evidence
    assert evidence.scope is EvidenceScope.PROVIDER
    assert evidence.system_id == "external-system-unknown"
    assert evidence.convention_id == "external-convention"
    assert evidence.treatment_id == "external-treatment"
    assert evidence.partnership_id == "external-pair"
    assert evidence.confidence == 0.6


def test_non_success_adviser_remains_independent_evidence():
    unavailable, _ = _provider(
        "offline-ai",
        None,
        status=ProviderStatus.UNAVAILABLE,
    )
    ben, _ = _provider("ben", "1S")
    registry = CapabilityProviderRegistry((unavailable, ben))

    result = gather_bidding_adviser_evidence(
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("offline-ai"),
            BiddingAdviserRequest("ben"),
        ),
    )

    assert result.total == 2
    assert result.observation("offline-ai").evidence.result.status is ProviderStatus.UNAVAILABLE
    assert result.observation("ben").evidence.result.status is ProviderStatus.SUCCESS


def test_empty_request_set_is_valid_and_passive():
    result = gather_bidding_adviser_evidence(
        registry=CapabilityProviderRegistry(),
        context=_context(),
        requests=(),
    )
    assert result.total == 0
    assert result.evidence == ()


def test_duplicate_requested_provider_ids_rejected_case_insensitively():
    ben, _ = _provider("ben", "1S")
    registry = CapabilityProviderRegistry((ben,))
    with pytest.raises(ValueError, match="requested provider_id values must be unique"):
        gather_bidding_adviser_evidence(
            registry=registry,
            context=_context(),
            requests=(
                BiddingAdviserRequest("ben"),
                BiddingAdviserRequest("BEN"),
            ),
        )


def test_unknown_provider_raises_key_error():
    with pytest.raises(KeyError):
        gather_bidding_adviser_evidence(
            registry=CapabilityProviderRegistry(),
            context=_context(),
            requests=(BiddingAdviserRequest("missing"),),
        )


def test_observation_lookup_is_case_insensitive():
    ben, _ = _provider("ben", "1S")
    registry = CapabilityProviderRegistry((ben,))
    result = gather_bidding_adviser_evidence(
        registry=registry,
        context=_context(),
        requests=(BiddingAdviserRequest("ben"),),
    )
    assert result.observation("BEN").provider_id == "ben"


def test_observation_lookup_missing_raises_key_error():
    result = MultiAdviserBiddingResult(())
    with pytest.raises(KeyError):
        result.observation("missing")


def test_result_rejects_duplicate_observation_ids_case_insensitively():
    ben, _ = _provider("ben", "1S")
    evidence = ben.evidence(_context())
    with pytest.raises(ValueError, match="provider_id values must be unique"):
        MultiAdviserBiddingResult(
            (
                BiddingAdviserEvidence("ben", evidence),
                BiddingAdviserEvidence("BEN", evidence),
            )
        )


def test_surface_contains_no_voting_ranking_or_winner_semantics():
    result = MultiAdviserBiddingResult(())
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
        "policy",
    ):
        assert not hasattr(result, name)
