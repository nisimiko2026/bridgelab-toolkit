"""A7.8 multi-adviser bidding report tests."""

import pytest

from bridge.auction import Bid, Call, Contract, Strain
from bridge.bidding_outcome_connection import (
    BiddingOutcomeCandidates,
    OutcomeCandidate,
)
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderEvidence,
    ProviderStatus,
)
from bridge.contract_alternative_evaluation import ContractAlternative
from bridge.decision_case import DecisionCase
from bridge.decision_evidence import (
    DecisionEvidence,
    Disagreement,
    DisagreementContext,
    DisagreementKind,
    EvidenceScope,
)
from bridge.isolated_bidding_evidence import (
    AdviserFailure,
    IsolatedMultiAdviserBiddingResult,
)
from bridge.models import Seat
from bridge.multi_adviser_bidding_report import (
    MultiAdviserBiddingReport,
    build_multi_adviser_bidding_report,
)
from bridge.multi_adviser_disagreement import MultiAdviserDisagreementResult
from bridge.multi_bidding_adviser import (
    BiddingAdviserEvidence,
    MultiAdviserBiddingResult,
)


def _evidence(
    provider_id,
    call=None,
    *,
    status=ProviderStatus.SUCCESS,
    system_id=None,
    convention_id=None,
    treatment_id=None,
    partnership_id=None,
    confidence=None,
    source_ids=(),
    model_id=None,
):
    descriptor = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation=f"{provider_id}-test",
        version="test",
    )
    recommendation = Call.parse(call) if status is ProviderStatus.SUCCESS else None
    return DecisionEvidence(
        result=CapabilityResult(
            provider=descriptor,
            status=status,
            recommendation=recommendation,
            evidence=ProviderEvidence(
                source_ids=source_ids,
                model_id=model_id,
            ),
        ),
        scope=EvidenceScope.PROVIDER,
        system_id=system_id,
        convention_id=convention_id,
        treatment_id=treatment_id,
        partnership_id=partnership_id,
        confidence=confidence,
    )


def _analysis(
    externals=(),
    disagreements=None,
    *,
    failures=(),
    notes=("audit-note",),
):
    bridge = _evidence(
        "bridgelab",
        "3NT",
        system_id="TWO_OVER_ONE_GF",
        convention_id="base",
        partnership_id="nisim-nily",
        confidence=1.0,
        source_ids=("policy:1",),
        model_id="bridgelab-policy",
    )
    if disagreements is None:
        disagreements = tuple(None for _ in externals)

    gathered = MultiAdviserBiddingResult(
        tuple(
            BiddingAdviserEvidence(x.result.provider.provider_id, x)
            for x in externals
        )
    )
    isolated = IsolatedMultiAdviserBiddingResult(
        gathered=gathered,
        failures=tuple(failures),
    )
    case_disagreements = tuple(x for x in disagreements if x is not None)
    case = DecisionCase(
        case_id="report-case",
        bridgelab=bridge,
        external=tuple(externals),
        disagreements=case_disagreements,
        notes=notes,
    )
    return MultiAdviserDisagreementResult(
        gathered=isolated,
        contexts=tuple(DisagreementContext() for _ in externals),
        disagreements=tuple(disagreements),
        decision_case=case,
    )


def _disagreement(right_provider, kind):
    return Disagreement(
        kind=kind,
        left_provider_id="bridgelab",
        right_provider_id=right_provider,
        explanation="test",
    )


def test_report_exposes_bridge_and_all_external_advisers():
    ben = _evidence("ben", "4S")
    ai2 = _evidence("ai2", "4H")
    report = build_multi_adviser_bidding_report(_analysis((ben, ai2)))

    assert isinstance(report, MultiAdviserBiddingReport)
    assert report.case_id == "report-case"
    assert report.bridgelab.provider_id == "bridgelab"
    assert tuple(x.provider_id for x in report.advisers) == ("ben", "ai2")


def test_report_preserves_provenance_and_semantic_metadata():
    ben = _evidence(
        "ben",
        "4S",
        system_id="SAYC",
        convention_id="stayman",
        treatment_id="standard",
        partnership_id="pair-x",
        confidence=0.81,
        source_ids=("ben:42", "model-card:7"),
        model_id="ben-0.8",
    )
    row = build_multi_adviser_bidding_report(_analysis((ben,))).advisers[0]

    assert row.system_id == "SAYC"
    assert row.convention_id == "stayman"
    assert row.treatment_id == "standard"
    assert row.partnership_id == "pair-x"
    assert row.confidence == pytest.approx(0.81)
    assert row.source_ids == ("ben:42", "model-card:7")
    assert row.model_id == "ben-0.8"


def test_report_preserves_provider_status_and_recommendation():
    success = _evidence("ok", "4S")
    abstain = _evidence("skip", status=ProviderStatus.ABSTAIN)
    unavailable = _evidence("offline", status=ProviderStatus.UNAVAILABLE)
    failed = _evidence("broken", status=ProviderStatus.FAILED)

    report = build_multi_adviser_bidding_report(
        _analysis((success, abstain, unavailable, failed))
    )

    assert tuple(x.status for x in report.advisers) == (
        ProviderStatus.SUCCESS,
        ProviderStatus.ABSTAIN,
        ProviderStatus.UNAVAILABLE,
        ProviderStatus.FAILED,
    )
    assert report.advisers[0].recommendation == Call.parse("4S")
    assert all(x.recommendation is None for x in report.advisers[1:])


def test_report_attaches_independent_disagreement_kinds():
    ben = _evidence("ben", "4S")
    ai2 = _evidence("ai2", "4H")
    disagreements = (
        _disagreement("ben", DisagreementKind.SYSTEM_DIFFERENCE),
        _disagreement("ai2", DisagreementKind.JUDGMENT_DIFFERENCE),
    )

    report = build_multi_adviser_bidding_report(
        _analysis((ben, ai2), disagreements)
    )

    assert tuple(x.disagreement for x in report.advisers) == (
        DisagreementKind.SYSTEM_DIFFERENCE,
        DisagreementKind.JUDGMENT_DIFFERENCE,
    )


def test_operational_failure_has_no_fake_disagreement():
    failed = _evidence("broken", status=ProviderStatus.FAILED)
    report = build_multi_adviser_bidding_report(_analysis((failed,), (None,)))
    assert report.advisers[0].status is ProviderStatus.FAILED
    assert report.advisers[0].disagreement is None


def test_runtime_failure_details_are_reported():
    failed = _evidence("broken", status=ProviderStatus.FAILED)
    failure = AdviserFailure("broken", "RuntimeError", "boom")
    report = build_multi_adviser_bidding_report(
        _analysis((failed,), (None,), failures=(failure,))
    )
    assert report.failures == ("broken: RuntimeError: boom",)


def test_notes_are_preserved():
    report = build_multi_adviser_bidding_report(
        _analysis(notes=("first", "second"))
    )
    assert report.notes == ("first", "second")


def test_outcome_candidates_are_optional():
    report = build_multi_adviser_bidding_report(_analysis())
    assert report.outcomes == ()


def test_outcome_candidates_preserve_contract_and_provider_provenance():
    analysis = _analysis((_evidence("ben", "4S"),))
    outcomes = BiddingOutcomeCandidates(
        (
            OutcomeCandidate(
                ContractAlternative(
                    "candidate-1",
                    Contract(Bid(3, Strain.NOTRUMP), Seat.NORTH),
                ),
                ("bridgelab",),
            ),
            OutcomeCandidate(
                ContractAlternative(
                    "candidate-2",
                    Contract(Bid(4, Strain.SPADES), Seat.SOUTH),
                ),
                ("ben",),
            ),
        )
    )

    report = build_multi_adviser_bidding_report(
        analysis,
        outcome_candidates=outcomes,
    )

    assert tuple(x.alternative_id for x in report.outcomes) == (
        "candidate-1",
        "candidate-2",
    )
    assert report.outcomes[0].provider_ids == ("bridgelab",)
    assert report.outcomes[1].provider_ids == ("ben",)
    assert "3NT" in report.outcomes[0].contract
    assert "4S" in report.outcomes[1].contract


def test_same_outcome_candidate_can_show_multiple_provider_sources():
    outcomes = BiddingOutcomeCandidates(
        (
            OutcomeCandidate(
                ContractAlternative(
                    "candidate-1",
                    Contract(Bid(4, Strain.SPADES), Seat.NORTH),
                ),
                ("ben", "ai2"),
            ),
        )
    )
    report = build_multi_adviser_bidding_report(
        _analysis((_evidence("ben", "4S"), _evidence("ai2", "4S"))),
        outcome_candidates=outcomes,
    )
    assert report.outcomes[0].provider_ids == ("ben", "ai2")


def test_report_has_no_winner_voting_or_ranking_surface():
    report = build_multi_adviser_bidding_report(
        _analysis((_evidence("a", "4S"), _evidence("b", "4S")))
    )
    for name in (
        "winner",
        "vote",
        "votes",
        "majority",
        "ranking",
        "rank",
        "preferred",
        "selected",
        "best",
    ):
        assert not hasattr(report, name)


def test_report_requires_analysis_type():
    with pytest.raises(TypeError, match="analysis must be"):
        build_multi_adviser_bidding_report(object())


def test_report_rejects_invalid_outcome_candidates():
    with pytest.raises(TypeError, match="outcome_candidates"):
        build_multi_adviser_bidding_report(
            _analysis(),
            outcome_candidates=object(),
        )


def test_empty_external_adviser_set_is_valid():
    report = build_multi_adviser_bidding_report(_analysis())
    assert report.advisers == ()
    assert report.failures == ()


def test_bridge_metadata_and_provenance_are_reported():
    report = build_multi_adviser_bidding_report(_analysis())
    assert report.bridgelab.system_id == "TWO_OVER_ONE_GF"
    assert report.bridgelab.convention_id == "base"
    assert report.bridgelab.partnership_id == "nisim-nily"
    assert report.bridgelab.confidence == pytest.approx(1.0)
    assert report.bridgelab.source_ids == ("policy:1",)
    assert report.bridgelab.model_id == "bridgelab-policy"
