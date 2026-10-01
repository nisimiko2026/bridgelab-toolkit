"""A4.2 production bidding decision evaluation tests."""

from bridge.auction import Auction, Call
from bridge.bidding_engine import BiddingEngine
from bridge.bidding_decision_evaluation import (
    ExternalBiddingEvaluation,
    evaluate_bidding_decision,
)
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
from bridge.decision_evidence import (
    DisagreementContext,
    DisagreementKind,
    EvidenceScope,
)
from bridge.engine_router import BiddingEngineRouter, EngineRoute
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)
from bridge.models import Hand, Seat, Vulnerability


class StaticRule:
    def __init__(
        self,
        *,
        rule_id: str,
        call: str,
    ) -> None:
        self.rule_id = rule_id
        self._call = call

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse(self._call),
            explanation=f"{self.rule_id} recommendation.",
            sources=(
                KnowledgeSource(
                    article_id=f"test/{self.rule_id}",
                ),
            ),
        )


class StaticTransport:
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


def make_router(call: str = "1S") -> BiddingEngineRouter:
    engine = BiddingEngine(
        (
            StaticRule(
                rule_id="test.production.rule",
                call=call,
            ),
        )
    )

    return BiddingEngineRouter(
        routes=(
            EngineRoute(
                route_id="test-route",
                matcher=lambda context: True,
                engine=engine,
            ),
        ),
    )


def make_external(
    provider_id: str,
    call: str,
) -> tuple[ExternalBiddingEvaluation, StaticTransport]:
    transport = StaticTransport(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation=call,
            explanation=f"{provider_id} recommendation.",
        )
    )

    adviser = ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.BIDDING,
            implementation=f"{provider_id}-test",
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


def test_bridgelab_production_result_becomes_case_policy_evidence():
    case = evaluate_bidding_decision(
        case_id="a42-policy",
        context=make_context(),
        router=make_router("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
        bridgelab_system_id="test-system",
    )

    assert case.case_id == "a42-policy"
    assert case.bridgelab is not None
    assert case.bridgelab.scope is EvidenceScope.SYSTEM
    assert case.bridgelab.system_id == "test-system"
    assert case.bridgelab.recommendation == Call.parse("1S")
    assert case.external == ()
    assert case.disagreements == ()


def test_one_external_adviser_is_composed_into_same_case():
    external, transport = make_external(
        "external-one",
        "4H",
    )

    case = evaluate_bidding_decision(
        case_id="a42-one-external",
        context=make_context(),
        router=make_router("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
        external=(external,),
    )

    assert len(case.external) == 1
    assert case.external[0].recommendation == Call.parse("4H")
    assert transport.calls == 1


def test_unknown_external_system_is_classified_explicitly():
    external, _ = make_external(
        "external-unknown-system",
        "4H",
    )

    case = evaluate_bidding_decision(
        case_id="a42-unknown-system",
        context=make_context(),
        router=make_router("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
        external=(external,),
    )

    assert len(case.disagreements) == 1
    assert (
        case.disagreements[0].kind
        is DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM
    )


def test_same_external_recommendation_is_agreement_even_when_system_unknown():
    external, _ = make_external(
        "external-agreement",
        "1S",
    )

    case = evaluate_bidding_decision(
        case_id="a42-agreement",
        context=make_context(),
        router=make_router("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
        external=(external,),
    )

    assert (
        case.disagreements[0].kind
        is DisagreementKind.AGREEMENT
    )


def test_multiple_external_advisers_preserve_caller_order():
    first, first_transport = make_external(
        "external-first",
        "4H",
    )
    second, second_transport = make_external(
        "external-second",
        "3H",
    )

    case = evaluate_bidding_decision(
        case_id="a42-multiple",
        context=make_context(),
        router=make_router("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
        external=(first, second),
    )

    assert tuple(
        evidence.result.provider.provider_id
        for evidence in case.external
    ) == (
        "external-first",
        "external-second",
    )

    assert first_transport.calls == 1
    assert second_transport.calls == 1
    assert len(case.disagreements) == 2


def test_external_policy_identity_is_preserved():
    transport = StaticTransport(
        ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation="3C",
        )
    )

    adviser = ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id="external-policy",
            capability=Capability.BIDDING,
            implementation="test",
        ),
        transport=transport,
    )

    external = ExternalBiddingEvaluation(
        adviser=adviser,
        disagreement_context=DisagreementContext(
            same_system=True,
            same_convention=True,
            same_treatment=False,
        ),
        system_id="2/1",
        convention_id="bergen",
        treatment_id="other-treatment",
        partnership_id="other-partnership",
        confidence=0.75,
    )

    case = evaluate_bidding_decision(
        case_id="a42-policy-identity",
        context=make_context(),
        router=make_router("1S"),
        bridgelab_scope=EvidenceScope.PARTNERSHIP,
        bridgelab_system_id="2/1",
        bridgelab_convention_id="bergen",
        bridgelab_treatment_id="nisim-nily-bergen",
        bridgelab_partnership_id="nisim-nily",
        external=(external,),
    )

    evidence = case.external[0]

    assert evidence.system_id == "2/1"
    assert evidence.convention_id == "bergen"
    assert evidence.treatment_id == "other-treatment"
    assert evidence.partnership_id == "other-partnership"
    assert evidence.confidence == 0.75

    assert (
        case.disagreements[0].kind
        is DisagreementKind.TREATMENT_DIFFERENCE
    )


def test_external_abstention_remains_external_model_abstain():
    transport = StaticTransport(
        ExternalBiddingObservation(
            status=ProviderStatus.ABSTAIN,
            explanation="No recommendation.",
        )
    )

    adviser = ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id="external-abstain",
            capability=Capability.BIDDING,
            implementation="test",
        ),
        transport=transport,
    )

    external = ExternalBiddingEvaluation(
        adviser=adviser,
    )

    case = evaluate_bidding_decision(
        case_id="a42-external-abstain",
        context=make_context(),
        router=make_router("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
        external=(external,),
    )

    assert (
        case.disagreements[0].kind
        is DisagreementKind.EXTERNAL_MODEL_ABSTAIN
    )


def test_bridgelab_abstention_is_preserved():
    router = BiddingEngineRouter()

    external, _ = make_external(
        "external-vs-abstain",
        "1S",
    )

    case = evaluate_bidding_decision(
        case_id="a42-bridgelab-abstain",
        context=make_context(),
        router=router,
        bridgelab_scope=EvidenceScope.SYSTEM,
        external=(external,),
    )

    assert case.bridgelab is not None
    assert case.bridgelab.result.status is ProviderStatus.ABSTAIN
    assert (
        case.disagreements[0].kind
        is DisagreementKind.BRIDGELAB_ABSTAIN
    )


def test_notes_are_preserved():
    case = evaluate_bidding_decision(
        case_id="a42-notes",
        context=make_context(),
        router=make_router(),
        bridgelab_scope=EvidenceScope.SYSTEM,
        notes=("production evaluation",),
    )

    assert case.notes == ("production evaluation",)


def test_case_id_is_normalized():
    case = evaluate_bidding_decision(
        case_id="  a42-normalized  ",
        context=make_context(),
        router=make_router(),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    assert case.case_id == "a42-normalized"
