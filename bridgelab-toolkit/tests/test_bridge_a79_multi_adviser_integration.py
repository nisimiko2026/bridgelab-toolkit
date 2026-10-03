"""A7.9 integration tests: BridgeLab + multiple external advisers."""

import pytest

from bridge.auction import Auction, Bid, Call, Contract, Strain
from bridge.bidding_outcome_connection import EvidenceContract, build_bidding_outcome_candidates
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_providers import (
    Capability, CapabilityResult, ProviderDescriptor, ProviderStatus,
)
from bridge.capability_registry import CapabilityProviderRegistry
from bridge.decision_evidence import DecisionEvidence, DisagreementKind, EvidenceScope
from bridge.external_bidding_adviser import ExternalBiddingAdviserAdapter, ExternalBiddingObservation
from bridge.models import Hand, Seat, Vulnerability
from bridge.multi_adviser_bidding_report import build_multi_adviser_bidding_report
from bridge.multi_adviser_disagreement import analyze_multi_adviser_disagreement
from bridge.multi_bidding_adviser import BiddingAdviserRequest


def _context():
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(Seat.NORTH, ("1C", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


def _bridge(call="3NT"):
    return DecisionEvidence(
        result=CapabilityResult(
            provider=ProviderDescriptor(
                provider_id="bridgelab",
                capability=Capability.BIDDING,
                implementation="bridgelab-policy",
                version="test",
            ),
            status=ProviderStatus.SUCCESS,
            recommendation=Call.parse(call),
        ),
        scope=EvidenceScope.PARTNERSHIP,
        system_id="TWO_OVER_ONE_GF",
        partnership_id="nisim-nily",
    )


class StubTransport:
    def __init__(self, observation):
        self.observation = observation
        self.calls = 0

    def observe(self, context):
        self.calls += 1
        return self.observation


def _external(provider_id, status, call=None):
    transport = StubTransport(
        ExternalBiddingObservation(
            status=status,
            recommendation=call if status is ProviderStatus.SUCCESS else None,
            source_ids=(f"{provider_id}:integration",),
            model_id=f"{provider_id}-model",
        )
    )
    adviser = ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.BIDDING,
            implementation=f"{provider_id}-integration",
            version="test",
        ),
        transport=transport,
    )
    return adviser, transport


class RaisingAdviser:
    descriptor = ProviderDescriptor(
        provider_id="broken",
        capability=Capability.BIDDING,
        implementation="raising-integration",
        version="test",
    )

    def __init__(self):
        self.calls = 0

    def advise(self, context):
        raise AssertionError("advise should not be called")

    def evidence(self, context, **kwargs):
        self.calls += 1
        raise RuntimeError("integration boom")


def _run(providers, requests):
    return analyze_multi_adviser_disagreement(
        case_id="a79-integration",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry(tuple(providers)),
        context=_context(),
        requests=tuple(requests),
        notes=("A7.9 integration",),
    )


def test_bridge_ben_and_second_adviser_flow_end_to_end():
    ben, ben_transport = _external("ben", ProviderStatus.SUCCESS, "4S")
    ai2, ai2_transport = _external("ai2", ProviderStatus.SUCCESS, "4H")

    analysis = _run(
        (ben, ai2),
        (
            BiddingAdviserRequest("ben"),
            BiddingAdviserRequest("ai2", system_id="TWO_OVER_ONE_GF"),
        ),
    )
    outcomes = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("bridgelab", Contract(Bid(3, Strain.NOTRUMP), Seat.NORTH)),
            EvidenceContract("ben", Contract(Bid(4, Strain.SPADES), Seat.NORTH)),
            EvidenceContract("ai2", Contract(Bid(4, Strain.HEARTS), Seat.NORTH)),
        ),
    )
    report = build_multi_adviser_bidding_report(analysis, outcome_candidates=outcomes)

    assert ben_transport.calls == 1
    assert ai2_transport.calls == 1
    assert tuple(x.provider_id for x in report.advisers) == ("ben", "ai2")
    assert tuple(x.disagreement for x in report.advisers) == (
        DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
        DisagreementKind.JUDGMENT_DIFFERENCE,
    )
    assert tuple(x.contract for x in report.outcomes) == ("3NT N", "4S N", "4H N")


def test_two_external_advisers_agree_but_do_not_form_majority_or_override_bridge():
    ben, _ = _external("ben", ProviderStatus.SUCCESS, "4S")
    ai2, _ = _external("ai2", ProviderStatus.SUCCESS, "4S")
    analysis = _run(
        (ben, ai2),
        (
            BiddingAdviserRequest("ben", system_id="TWO_OVER_ONE_GF"),
            BiddingAdviserRequest("ai2", system_id="TWO_OVER_ONE_GF"),
        ),
    )
    same = Contract(Bid(4, Strain.SPADES), Seat.NORTH)
    outcomes = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("bridgelab", Contract(Bid(3, Strain.NOTRUMP), Seat.NORTH)),
            EvidenceContract("ben", same),
            EvidenceContract("ai2", same),
        ),
    )
    report = build_multi_adviser_bidding_report(analysis, outcome_candidates=outcomes)

    assert report.bridgelab.recommendation == Call.parse("3NT")
    assert len(report.outcomes) == 2
    assert report.outcomes[1].provider_ids == ("ben", "ai2")
    assert tuple(x.disagreement for x in report.advisers) == (
        DisagreementKind.JUDGMENT_DIFFERENCE,
        DisagreementKind.JUDGMENT_DIFFERENCE,
    )
    for name in ("winner", "votes", "majority", "ranking", "selected", "preferred"):
        assert not hasattr(report, name)


@pytest.mark.parametrize(
    "status, expected_kind",
    [
        (ProviderStatus.ABSTAIN, DisagreementKind.EXTERNAL_MODEL_ABSTAIN),
        (ProviderStatus.UNAVAILABLE, None),
        (ProviderStatus.FAILED, None),
    ],
)
def test_non_success_status_survives_full_pipeline(status, expected_kind):
    ben, _ = _external("ben", status)
    analysis = _run((ben,), (BiddingAdviserRequest("ben"),))
    report = build_multi_adviser_bidding_report(analysis)

    assert report.advisers[0].status is status
    assert report.advisers[0].recommendation is None
    assert report.advisers[0].disagreement is expected_kind


def test_runtime_exception_is_isolated_and_later_adviser_still_runs():
    broken = RaisingAdviser()
    ai2, ai2_transport = _external("ai2", ProviderStatus.SUCCESS, "4H")
    analysis = _run(
        (broken, ai2),
        (
            BiddingAdviserRequest("broken"),
            BiddingAdviserRequest("ai2", system_id="TWO_OVER_ONE_GF"),
        ),
    )
    report = build_multi_adviser_bidding_report(analysis)

    assert broken.calls == 1
    assert ai2_transport.calls == 1
    assert report.advisers[0].status is ProviderStatus.FAILED
    assert report.advisers[0].disagreement is None
    assert report.advisers[1].status is ProviderStatus.SUCCESS
    assert report.advisers[1].disagreement is DisagreementKind.JUDGMENT_DIFFERENCE
    assert report.failures == ("broken: RuntimeError: integration boom",)


def test_failed_and_unavailable_sources_need_no_outcome_contract():
    unavailable, _ = _external("offline", ProviderStatus.UNAVAILABLE)
    broken = RaisingAdviser()
    analysis = _run(
        (unavailable, broken),
        (
            BiddingAdviserRequest("offline"),
            BiddingAdviserRequest("broken"),
        ),
    )
    outcomes = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("bridgelab", Contract(Bid(3, Strain.NOTRUMP), Seat.NORTH)),
        ),
    )
    report = build_multi_adviser_bidding_report(analysis, outcome_candidates=outcomes)

    assert tuple(x.status for x in report.advisers) == (
        ProviderStatus.UNAVAILABLE,
        ProviderStatus.FAILED,
    )
    assert tuple(x.disagreement for x in report.advisers) == (None, None)
    assert tuple(x.provider_ids for x in report.outcomes) == (("bridgelab",),)


def test_unknown_external_system_remains_unknown_in_integrated_report():
    ben, _ = _external("ben", ProviderStatus.SUCCESS, "4S")
    report = build_multi_adviser_bidding_report(
        _run((ben,), (BiddingAdviserRequest("ben"),))
    )
    assert report.advisers[0].system_id is None
    assert report.advisers[0].disagreement is DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM


def test_explicit_different_system_is_reported_not_normalized_to_bridge_system():
    ben, _ = _external("ben", ProviderStatus.SUCCESS, "4S")
    report = build_multi_adviser_bidding_report(
        _run((ben,), (BiddingAdviserRequest("ben", system_id="SAYC"),))
    )
    assert report.advisers[0].system_id == "SAYC"
    assert report.advisers[0].disagreement is DisagreementKind.SYSTEM_DIFFERENCE


def test_provider_provenance_survives_analysis_to_report():
    ben, _ = _external("ben", ProviderStatus.SUCCESS, "4S")
    report = build_multi_adviser_bidding_report(
        _run((ben,), (BiddingAdviserRequest("ben"),))
    )
    assert report.advisers[0].source_ids == ("ben:integration",)
    assert report.advisers[0].model_id == "ben-model"


def test_request_order_survives_collection_analysis_and_report():
    a, _ = _external("a", ProviderStatus.SUCCESS, "4S")
    b, _ = _external("b", ProviderStatus.SUCCESS, "4H")
    c, _ = _external("c", ProviderStatus.ABSTAIN)
    report = build_multi_adviser_bidding_report(
        _run(
            (a, b, c),
            (
                BiddingAdviserRequest("c"),
                BiddingAdviserRequest("a", system_id="TWO_OVER_ONE_GF"),
                BiddingAdviserRequest("b", system_id="TWO_OVER_ONE_GF"),
            ),
        )
    )
    assert tuple(x.provider_id for x in report.advisers) == ("c", "a", "b")


def test_notes_survive_integrated_pipeline():
    ben, _ = _external("ben", ProviderStatus.SUCCESS, "4S")
    report = build_multi_adviser_bidding_report(
        _run((ben,), (BiddingAdviserRequest("ben"),))
    )
    assert report.notes == ("A7.9 integration",)
