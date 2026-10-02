"""A4.4 end-to-end BridgeLab decision evidence pipeline."""

from bridge.auction import Auction, Call
from bridge.bidding_decision_evaluation import (
    ExternalBiddingEvaluation,
    evaluate_bidding_decision,
)
from bridge.bidding_engine import BiddingEngine
from bridge.bidding_rules import (
    BiddingContext,
    KnowledgeSource,
    RuleDecision,
    SystemContext,
)
from bridge.capability_providers import (
    Capability,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.corpus import (
    CanonicalBoardRecord,
    SourceProvenance,
)
from bridge.decision_case_enrichment import enrich_decision_case
from bridge.decision_case_roles import build_decision_case_role_view
from bridge.decision_evidence import (
    DisagreementContext,
    DisagreementKind,
    EvidenceScope,
)
from bridge.double_dummy_evidence import DoubleDummyEvidence
from bridge.engine_router import BiddingEngineRouter, EngineRoute
from bridge.evidence_roles import EvidenceRole
from bridge.evidence_source_manifest import build_evidence_source_manifest
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.simulation_statistics import SimulationStatistics
from bridge.trick_solver import (
    TrickSolverResult,
    TrickSolverStatus,
)


class ProductionRule:
    rule_id = "a44.production.rule"

    def evaluate(
        self,
        context: BiddingContext,
    ) -> RuleDecision:
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("3C"),
            explanation="BridgeLab production policy recommends 3C.",
            sources=(
                KnowledgeSource(
                    article_id="test/a44-policy",
                ),
            ),
        )


class ExternalTransport:
    def __init__(
        self,
        *,
        recommendation: str,
    ) -> None:
        self.recommendation = recommendation
        self.calls = 0

    def observe(
        self,
        context: BiddingContext,
    ) -> ExternalBiddingObservation:
        self.calls += 1

        return ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation=self.recommendation,
            model_id="a44-model",
            source_ids=("a44-external-source",),
            explanation="External adviser recommendation.",
        )


def make_context() -> BiddingContext:
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(
            dealer=Seat.NORTH,
            calls=(),
        ),
        seat=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
        system=SystemContext("test-system"),
    )


def make_router() -> BiddingEngineRouter:
    engine = BiddingEngine(
        (
            ProductionRule(),
        )
    )

    return BiddingEngineRouter(
        routes=(
            EngineRoute(
                route_id="a44-production-route",
                matcher=lambda context: True,
                engine=engine,
            ),
        ),
    )


def make_external(
    provider_id: str,
    recommendation: str,
) -> tuple[ExternalBiddingEvaluation, ExternalTransport]:
    transport = ExternalTransport(
        recommendation=recommendation,
    )

    adviser = ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.BIDDING,
            implementation=f"{provider_id}-implementation",
            version="1",
        ),
        transport=transport,
    )

    return (
        ExternalBiddingEvaluation(
            adviser=adviser,
            disagreement_context=DisagreementContext(
                external_system_known=False,
            ),
        ),
        transport,
    )


def make_corpus() -> CanonicalBoardRecord:
    return CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider="expert-corpus",
            source="a44-source",
            record_id="board-44",
            provider_version="2026",
        ),
        dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
    )


def make_simulation() -> SimulationStatistics:
    return SimulationStatistics(
        runs=1000,
        completed=1000,
        abstained=0,
        max_steps=0,
        total_calls_added=1000,
        max_calls_added=1,
        stop_reason_counts=(),
        stopped_seat_counts=(),
    )


def make_double_dummy() -> DoubleDummyEvidence:
    provider = ProviderDescriptor(
        provider_id="dds-a44",
        capability=Capability.DOUBLE_DUMMY,
        implementation="dds-test",
        version="1",
    )

    result = TrickSolverResult(
        implementation="dds-test",
        version="1",
        deal_id="deal-44",
        declarer=Seat.NORTH,
        strain=None,
        opening_lead=None,
        status=TrickSolverStatus.SUCCESS,
        maximum_declarer_tricks=10,
        elapsed_seconds=0.01,
    )

    return DoubleDummyEvidence(
        provider=provider,
        result=result,
    )


def build_complete_case():
    ben, ben_transport = make_external(
        "ben",
        "4H",
    )

    brl, brl_transport = make_external(
        "brl",
        "3H",
    )

    evaluated = evaluate_bidding_decision(
        case_id="a44-end-to-end",
        context=make_context(),
        router=make_router(),
        bridgelab_scope=EvidenceScope.TREATMENT,
        bridgelab_system_id="2/1",
        bridgelab_convention_id="test-convention",
        bridgelab_treatment_id="test-treatment",
        bridgelab_partnership_id="nisim-nily",
        external=(
            ben,
            brl,
        ),
        notes=("A4.4 production evaluation",),
    )

    enriched = enrich_decision_case(
        evaluated,
        corpus=(make_corpus(),),
        simulations=(make_simulation(),),
        double_dummy=(make_double_dummy(),),
        notes=("A4.4 reference evidence",),
    )

    return (
        enriched,
        ben_transport,
        brl_transport,
    )


def test_complete_pipeline_preserves_all_evidence_categories():
    case, _, _ = build_complete_case()

    assert case.bridgelab is not None
    assert len(case.external) == 2
    assert len(case.corpus) == 1
    assert len(case.simulations) == 1
    assert len(case.double_dummy) == 1
    assert len(case.disagreements) == 2


def test_bridgelab_policy_remains_the_case_policy_recommendation():
    case, _, _ = build_complete_case()

    assert case.bridgelab.recommendation == Call.parse("3C")
    assert case.bridgelab.scope is EvidenceScope.TREATMENT
    assert case.bridgelab.system_id == "2/1"
    assert case.bridgelab.convention_id == "test-convention"
    assert case.bridgelab.treatment_id == "test-treatment"
    assert case.bridgelab.partnership_id == "nisim-nily"


def test_external_recommendations_are_retained_without_voting():
    case, ben_transport, brl_transport = build_complete_case()

    assert tuple(
        evidence.recommendation
        for evidence in case.external
    ) == (
        Call.parse("4H"),
        Call.parse("3H"),
    )

    assert ben_transport.calls == 1
    assert brl_transport.calls == 1

    assert case.bridgelab.recommendation == Call.parse("3C")


def test_each_external_is_compared_only_with_bridgelab():
    case, _, _ = build_complete_case()

    assert tuple(
        disagreement.kind
        for disagreement in case.disagreements
    ) == (
        DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
        DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
    )

    assert tuple(
        disagreement.left_provider_id
        for disagreement in case.disagreements
    ) == (
        "bridgelab",
        "bridgelab",
    )

    assert tuple(
        disagreement.right_provider_id
        for disagreement in case.disagreements
    ) == (
        "ben",
        "brl",
    )


def test_role_view_exposes_five_semantic_evidence_roles():
    case, _, _ = build_complete_case()

    view = build_decision_case_role_view(case)

    assert tuple(
        item.role
        for item in view.evidence
    ) == (
        EvidenceRole.POLICY_RECOMMENDATION,
        EvidenceRole.EXTERNAL_RECOMMENDATION,
        EvidenceRole.EXTERNAL_RECOMMENDATION,
        EvidenceRole.OBSERVED_ACTION,
        EvidenceRole.STATISTICAL_ESTIMATE,
        EvidenceRole.OUTCOME_MEASUREMENT,
    )


def test_role_view_does_not_promote_measurements_to_recommendations():
    case, _, _ = build_complete_case()

    view = build_decision_case_role_view(case)

    policy = view.for_role(
        EvidenceRole.POLICY_RECOMMENDATION
    )
    statistical = view.for_role(
        EvidenceRole.STATISTICAL_ESTIMATE
    )
    outcome = view.for_role(
        EvidenceRole.OUTCOME_MEASUREMENT
    )

    assert len(policy) == 1
    assert len(statistical) == 1
    assert len(outcome) == 1

    assert policy[0].evidence is case.bridgelab
    assert statistical[0].evidence is case.simulations[0]
    assert outcome[0].evidence is case.double_dummy[0]


def test_source_manifest_preserves_complete_source_order():
    case, _, _ = build_complete_case()

    manifest = build_evidence_source_manifest(case)

    assert tuple(
        entry.role
        for entry in manifest.entries
    ) == (
        EvidenceRole.POLICY_RECOMMENDATION,
        EvidenceRole.EXTERNAL_RECOMMENDATION,
        EvidenceRole.EXTERNAL_RECOMMENDATION,
        EvidenceRole.OBSERVED_ACTION,
        EvidenceRole.STATISTICAL_ESTIMATE,
        EvidenceRole.OUTCOME_MEASUREMENT,
    )

    assert tuple(
        entry.source_id
        for entry in manifest.entries
    ) == (
        "bridgelab",
        "ben",
        "brl",
        "expert-corpus",
        None,
        "dds-a44",
    )


def test_corpus_provenance_survives_full_pipeline():
    case, _, _ = build_complete_case()

    manifest = build_evidence_source_manifest(case)

    observed = manifest.for_role(
        EvidenceRole.OBSERVED_ACTION
    )

    assert len(observed) == 1
    assert observed[0].source_kind == "corpus"
    assert observed[0].source_id == "expert-corpus"
    assert observed[0].version == "2026"
    assert observed[0].record_id == "board-44"


def test_double_dummy_provider_survives_full_pipeline():
    case, _, _ = build_complete_case()

    manifest = build_evidence_source_manifest(case)

    dd = manifest.for_role(
        EvidenceRole.OUTCOME_MEASUREMENT
    )

    assert len(dd) == 1
    assert dd[0].source_kind == "double_dummy"
    assert dd[0].source_id == "dds-a44"
    assert dd[0].implementation == "dds-test"
    assert dd[0].version == "1"


def test_notes_from_evaluation_and_enrichment_are_both_preserved():
    case, _, _ = build_complete_case()

    assert case.notes == (
        "A4.4 production evaluation",
        "A4.4 reference evidence",
    )
