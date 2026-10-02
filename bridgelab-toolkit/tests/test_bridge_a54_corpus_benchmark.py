"""A5.4 corpus benchmark runner tests."""

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_engine import BiddingEngine
from bridge.bidding_rules import (
    BiddingContext,
    KnowledgeSource,
    RuleDecision,
)
from bridge.bridgelab_bidding_evidence import (
    BRIDGELAB_BIDDING_PROVIDER_ID,
)
from bridge.corpus import (
    CanonicalBoardRecord,
    SourceProvenance,
)
from bridge.corpus_benchmark import (
    CORPUS_OBSERVATION_IMPLEMENTATION,
    CorpusBenchmarkResult,
    CorpusBenchmarkStatus,
    benchmark_corpus_decision,
    benchmark_corpus_decisions,
    corpus_decision_evidence,
)
from bridge.corpus_decisions import (
    CorpusBiddingDecision,
    extract_corpus_bidding_decisions,
)
from bridge.deals import generate_deal
from bridge.decision_evidence import (
    DisagreementContext,
    DisagreementKind,
    EvidenceScope,
)
from bridge.engine_router import BiddingEngineRouter
from bridge.models import Seat, Vulnerability


class FixedRule:
    def __init__(
        self,
        rule_id: str,
        call: str,
    ) -> None:
        self._rule_id = rule_id
        self._call = Call.parse(call)

    @property
    def rule_id(self) -> str:
        return self._rule_id

    def evaluate(
        self,
        context: BiddingContext,
    ) -> RuleDecision:
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=self._call,
            explanation="A5.4 test recommendation.",
            sources=(
                KnowledgeSource(
                    "tests/a54-corpus-benchmark"
                ),
            ),
        )


def make_decision(
    *,
    observed_call: str = "1S",
    system_id: str | None = "2/1",
    record_id: str = "board-54",
) -> CorpusBiddingDecision:
    record = CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider="expert-corpus",
            source="a54-test",
            record_id=record_id,
            provider_version="2026.1",
        ),
        dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
        deal=generate_deal(54),
        auction=Auction(
            Seat.NORTH,
            (
                observed_call,
                "P",
                "P",
                "P",
            ),
        ),
        ns_system=system_id,
    )

    return extract_corpus_bidding_decisions(
        record
    )[0]


def router_recommending(
    call: str,
) -> BiddingEngineRouter:
    return BiddingEngineRouter(
        fallback=BiddingEngine(
            (
                FixedRule(
                    "a54.fixed",
                    call,
                ),
            )
        )
    )


def test_corpus_observation_becomes_expert_corpus_evidence():
    decision = make_decision(
        observed_call="1S",
    )

    evidence = corpus_decision_evidence(
        decision
    )

    assert evidence.scope is EvidenceScope.EXPERT_CORPUS
    assert evidence.recommendation == Call.parse("1S")

    assert (
        evidence.result.provider.provider_id
        == "expert-corpus"
    )
    assert (
        evidence.result.provider.implementation
        == CORPUS_OBSERVATION_IMPLEMENTATION
    )
    assert (
        evidence.result.provider.version
        == "2026.1"
    )


def test_corpus_evidence_preserves_record_id():
    decision = make_decision(
        record_id="record-123",
    )

    evidence = corpus_decision_evidence(
        decision
    )

    assert evidence.result.evidence.source_ids == (
        "record-123",
    )


def test_corpus_evidence_preserves_system_identity():
    decision = make_decision(
        system_id="2/1",
    )

    evidence = corpus_decision_evidence(
        decision
    )

    assert evidence.system_id == "2/1"


def test_unknown_system_is_skipped_not_invented():
    decision = make_decision(
        system_id=None,
    )

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    assert (
        result.status
        is CorpusBenchmarkStatus.SKIPPED_UNKNOWN_SYSTEM
    )
    assert result.case is None
    assert result.reason == (
        "corpus bidding system is unknown"
    )


def test_known_system_is_evaluated():
    decision = make_decision(
        observed_call="1S",
        system_id="2/1",
    )

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    assert (
        result.status
        is CorpusBenchmarkStatus.EVALUATED
    )
    assert result.case is not None
    assert result.reason is None


def test_bridge_and_corpus_agreement_is_classified():
    decision = make_decision(
        observed_call="1S",
    )

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    case = result.case
    assert case is not None

    assert len(case.disagreements) == 1
    assert (
        case.disagreements[0].kind
        is DisagreementKind.AGREEMENT
    )


def test_difference_is_not_automatically_policy_gap():
    decision = make_decision(
        observed_call="1S",
    )

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1H"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    case = result.case
    assert case is not None

    assert len(case.disagreements) == 1
    assert (
        case.disagreements[0].kind
        is DisagreementKind.JUDGMENT_DIFFERENCE
    )


def test_explicit_policy_gap_context_is_respected():
    decision = make_decision(
        observed_call="1S",
    )

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1H"),
        bridgelab_scope=EvidenceScope.SYSTEM,
        disagreement_context=DisagreementContext(
           bridgelab_policy_expected=True,
        ),
    )

    case = result.case
    assert case is not None

    assert (
        case.disagreements[0].kind
        is DisagreementKind.POSSIBLE_POLICY_GAP
    )


def test_bridge_evidence_uses_bridgelab_provider():
    decision = make_decision()

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    case = result.case
    assert case is not None
    assert case.bridgelab is not None

    assert (
        case.bridgelab.result.provider.provider_id
        == BRIDGELAB_BIDDING_PROVIDER_ID
    )


def test_corpus_observation_is_external_evidence():
    decision = make_decision()

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    case = result.case
    assert case is not None

    assert len(case.external) == 1
    assert (
        case.external[0].scope
        is EvidenceScope.EXPERT_CORPUS
    )
    assert (
        case.external[0].recommendation
        == decision.observed_call
    )


def test_case_id_is_deterministic():
    decision = make_decision(
        record_id="abc",
    )

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    assert result.case is not None
    assert result.case.case_id == (
        "expert-corpus:abc:0"
    )


def test_bridge_policy_identity_is_preserved():
    decision = make_decision()

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.TREATMENT,
        bridgelab_convention_id="bergen",
        bridgelab_treatment_id="nisim-nily",
        bridgelab_partnership_id="nisim-nily",
    )

    case = result.case
    assert case is not None
    assert case.bridgelab is not None

    assert case.bridgelab.system_id == "2/1"
    assert case.bridgelab.convention_id == "bergen"
    assert (
        case.bridgelab.treatment_id
        == "nisim-nily"
    )
    assert (
        case.bridgelab.partnership_id
        == "nisim-nily"
    )


def test_empty_router_produces_bridgelab_abstention():
    decision = make_decision()

    result = benchmark_corpus_decision(
        decision=decision,
        router=BiddingEngineRouter(),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    case = result.case
    assert case is not None
    assert case.bridgelab is not None

    assert case.bridgelab.recommendation is None
    assert (
        case.disagreements[0].kind
        is DisagreementKind.BRIDGELAB_ABSTAIN
    )


def test_batch_preserves_input_order():
    first = make_decision(
        record_id="first",
    )
    second = make_decision(
        record_id="second",
    )

    results = benchmark_corpus_decisions(
        decisions=(
            first,
            second,
        ),
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    assert tuple(
        result.decision.provenance.record_id
        for result in results
    ) == (
        "first",
        "second",
    )


def test_batch_retains_skipped_and_evaluated_results():
    known = make_decision(
        system_id="2/1",
        record_id="known",
    )
    unknown = make_decision(
        system_id=None,
        record_id="unknown",
    )

    results = benchmark_corpus_decisions(
        decisions=(
            known,
            unknown,
        ),
        router=router_recommending("1S"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    assert tuple(
        result.status
        for result in results
    ) == (
        CorpusBenchmarkStatus.EVALUATED,
        CorpusBenchmarkStatus.SKIPPED_UNKNOWN_SYSTEM,
    )


def test_system_options_reach_router_context():
    seen = []

    class RecordingEngine:
        def evaluate(
            self,
            context: BiddingContext,
        ):
            seen.append(context.system)
            return BiddingEngine(
                (
                    FixedRule(
                        "a54.recording",
                        "1S",
                    ),
                )
            ).evaluate(context)

    decision = make_decision()

    router = BiddingEngineRouter(
        fallback=RecordingEngine()
    )

    benchmark_corpus_decision(
        decision=decision,
        router=router,
        bridgelab_scope=EvidenceScope.SYSTEM,
        system_options=(
            ("bergen", "on"),
        ),
    )

    assert len(seen) == 1
    assert seen[0].system == "2/1"
    assert seen[0].option("bergen") == "on"


def test_observed_call_does_not_replace_bridge_recommendation():
    decision = make_decision(
        observed_call="1S",
    )

    result = benchmark_corpus_decision(
        decision=decision,
        router=router_recommending("1H"),
        bridgelab_scope=EvidenceScope.SYSTEM,
    )

    case = result.case
    assert case is not None
    assert case.bridgelab is not None

    assert (
        case.bridgelab.recommendation
        == Call.parse("1H")
    )
    assert (
        case.external[0].recommendation
        == Call.parse("1S")
    )


def test_invalid_decision_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="decision must be CorpusBiddingDecision",
    ):
        benchmark_corpus_decision(
            decision=object(),
            router=router_recommending("1S"),
            bridgelab_scope=EvidenceScope.SYSTEM,
        )


def test_batch_requires_tuple():
    with pytest.raises(
        TypeError,
        match="decisions must be a tuple",
    ):
        benchmark_corpus_decisions(
            decisions=[],
            router=router_recommending("1S"),
            bridgelab_scope=EvidenceScope.SYSTEM,
        )


def test_batch_rejects_wrong_element_type():
    with pytest.raises(
        TypeError,
        match=(
            "decisions must contain "
            "CorpusBiddingDecision values"
        ),
    ):
        benchmark_corpus_decisions(
            decisions=(object(),),
            router=router_recommending("1S"),
            bridgelab_scope=EvidenceScope.SYSTEM,
        )


def test_result_invariants_reject_evaluated_without_case():
    decision = make_decision()

    with pytest.raises(
        ValueError,
        match=(
            "evaluated benchmark result "
            "requires a DecisionCase"
        ),
    ):
        CorpusBenchmarkResult(
            decision=decision,
            status=CorpusBenchmarkStatus.EVALUATED,
        )
