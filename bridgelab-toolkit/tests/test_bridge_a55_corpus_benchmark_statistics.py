"""A5.5 corpus benchmark statistics tests."""

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_engine import BiddingEngine
from bridge.bidding_rules import (
    BiddingContext,
    KnowledgeSource,
    RuleDecision,
)
from bridge.corpus import (
    CanonicalBoardRecord,
    SourceProvenance,
)
from bridge.corpus_benchmark import (
    CorpusBenchmarkStatus,
    benchmark_corpus_decision,
)
from bridge.corpus_benchmark_statistics import (
    CorpusBenchmarkStatistics,
    summarize_corpus_benchmark,
)
from bridge.corpus_decisions import (
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
            explanation="A5.5 test recommendation.",
            sources=(
                KnowledgeSource(
                    "tests/a55-corpus-statistics"
                ),
            ),
        )


def make_decision(
    *,
    observed_call: str = "1S",
    system_id: str | None = "2/1",
    seed: int = 55,
):
    record = CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider="expert-corpus",
            source="a55-test",
            record_id=f"board-{seed}",
        ),
        dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
        deal=generate_deal(seed),
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
                    "a55.fixed",
                    call,
                ),
            )
        )
    )


def benchmark(
    *,
    observed: str = "1S",
    recommended: str | None = "1S",
    system_id: str | None = "2/1",
    context: DisagreementContext = DisagreementContext(),
    seed: int = 55,
):
    decision = make_decision(
        observed_call=observed,
        system_id=system_id,
        seed=seed,
    )

    router = (
        BiddingEngineRouter()
        if recommended is None
        else router_recommending(recommended)
    )

    return benchmark_corpus_decision(
        decision=decision,
        router=router,
        bridgelab_scope=EvidenceScope.SYSTEM,
        disagreement_context=context,
    )


def test_empty_summary():
    stats = summarize_corpus_benchmark(())

    assert stats.total == 0
    assert stats.evaluated == 0
    assert stats.skipped_unknown_system == 0
    assert stats.bridgelab_recommended == 0
    assert stats.bridgelab_abstained == 0
    assert stats.agreements == 0


def test_empty_rates_are_zero():
    stats = summarize_corpus_benchmark(())

    assert stats.system_known_rate == 0.0
    assert stats.bridgelab_coverage_rate == 0.0
    assert stats.bridgelab_abstention_rate == 0.0
    assert stats.agreement_rate == 0.0


def test_agreement_is_counted():
    result = benchmark()

    stats = summarize_corpus_benchmark(
        (result,)
    )

    assert stats.total == 1
    assert stats.evaluated == 1
    assert stats.agreements == 1
    assert stats.count(
        DisagreementKind.AGREEMENT
    ) == 1


def test_judgment_difference_is_counted():
    result = benchmark(
        observed="1S",
        recommended="1H",
    )

    stats = summarize_corpus_benchmark(
        (result,)
    )

    assert stats.count(
        DisagreementKind.JUDGMENT_DIFFERENCE
    ) == 1
    assert stats.agreements == 0


def test_policy_gap_is_counted_without_reclassification():
    result = benchmark(
        observed="1S",
        recommended="1H",
        context=DisagreementContext(
            bridgelab_policy_expected=True,
        ),
    )

    stats = summarize_corpus_benchmark(
        (result,)
    )

    assert stats.count(
        DisagreementKind.POSSIBLE_POLICY_GAP
    ) == 1


def test_engine_defect_is_counted_without_reclassification():
    result = benchmark(
        observed="1S",
        recommended="1H",
        context=DisagreementContext(
            engine_defect_evidence=True,
        ),
    )

    stats = summarize_corpus_benchmark(
        (result,)
    )

    assert stats.count(
        DisagreementKind.POSSIBLE_ENGINE_DEFECT
    ) == 1


def test_unknown_system_is_skipped():
    result = benchmark(
        system_id=None,
    )

    assert (
        result.status
        is CorpusBenchmarkStatus.SKIPPED_UNKNOWN_SYSTEM
    )

    stats = summarize_corpus_benchmark(
        (result,)
    )

    assert stats.total == 1
    assert stats.evaluated == 0
    assert stats.skipped_unknown_system == 1


def test_skipped_position_does_not_enter_disagreement_counts():
    result = benchmark(
        system_id=None,
    )

    stats = summarize_corpus_benchmark(
        (result,)
    )

    assert sum(
        count
        for _, count in stats.disagreement_counts
    ) == 0


def test_bridgelab_recommendation_is_counted():
    result = benchmark()

    stats = summarize_corpus_benchmark(
        (result,)
    )

    assert stats.bridgelab_recommended == 1
    assert stats.bridgelab_abstained == 0


def test_bridgelab_abstention_is_counted():
    result = benchmark(
        recommended=None,
    )

    stats = summarize_corpus_benchmark(
        (result,)
    )

    assert stats.bridgelab_recommended == 0
    assert stats.bridgelab_abstained == 1
    assert stats.count(
        DisagreementKind.BRIDGELAB_ABSTAIN
    ) == 1


def test_system_known_rate():
    results = (
        benchmark(seed=551),
        benchmark(
            system_id=None,
            seed=552,
        ),
    )

    stats = summarize_corpus_benchmark(
        results
    )

    assert stats.system_known_rate == 0.5


def test_bridgelab_coverage_rate():
    results = (
        benchmark(
            recommended="1S",
            seed=553,
        ),
        benchmark(
            recommended=None,
            seed=554,
        ),
    )

    stats = summarize_corpus_benchmark(
        results
    )

    assert stats.bridgelab_coverage_rate == 0.5
    assert stats.bridgelab_abstention_rate == 0.5


def test_agreement_rate_is_descriptive_fraction():
    results = (
        benchmark(
            observed="1S",
            recommended="1S",
            seed=555,
        ),
        benchmark(
            observed="1S",
            recommended="1H",
            seed=556,
        ),
    )

    stats = summarize_corpus_benchmark(
        results
    )

    assert stats.agreement_rate == 0.5


def test_mixed_summary_counts_all_positions():
    results = (
        benchmark(
            observed="1S",
            recommended="1S",
            seed=557,
        ),
        benchmark(
            observed="1S",
            recommended="1H",
            seed=558,
        ),
        benchmark(
            recommended=None,
            seed=559,
        ),
        benchmark(
            system_id=None,
            seed=560,
        ),
    )

    stats = summarize_corpus_benchmark(
        results
    )

    assert stats.total == 4
    assert stats.evaluated == 3
    assert stats.skipped_unknown_system == 1
    assert stats.bridgelab_recommended == 2
    assert stats.bridgelab_abstained == 1
    assert stats.agreements == 1


def test_disagreement_counts_follow_enum_order():
    stats = summarize_corpus_benchmark(
        (
            benchmark(),
        )
    )

    assert tuple(
        kind
        for kind, _ in stats.disagreement_counts
    ) == tuple(DisagreementKind)


def test_all_disagreement_kinds_are_present_even_when_zero():
    stats = summarize_corpus_benchmark(())

    assert len(stats.disagreement_counts) == len(
        tuple(DisagreementKind)
    )

    assert all(
        count == 0
        for _, count in stats.disagreement_counts
    )


def test_count_rejects_invalid_kind():
    stats = summarize_corpus_benchmark(())

    with pytest.raises(
        TypeError,
        match="kind must be DisagreementKind",
    ):
        stats.count("agreement")


def test_summary_requires_tuple():
    with pytest.raises(
        TypeError,
        match="results must be a tuple",
    ):
        summarize_corpus_benchmark([])


def test_summary_rejects_invalid_element():
    with pytest.raises(
        TypeError,
        match=(
            "results must contain "
            "CorpusBenchmarkResult values"
        ),
    ):
        summarize_corpus_benchmark(
            (object(),)
        )


def test_statistics_reject_inconsistent_position_totals():
    with pytest.raises(
        ValueError,
        match=(
            "evaluated plus skipped positions "
            "must equal total"
        ),
    ):
        CorpusBenchmarkStatistics(
            total=2,
            evaluated=1,
            skipped_unknown_system=0,
            bridgelab_recommended=1,
            bridgelab_abstained=0,
            agreements=1,
            disagreement_counts=tuple(
                (
                    kind,
                    1
                    if kind is DisagreementKind.AGREEMENT
                    else 0,
                )
                for kind in DisagreementKind
            ),
        )


def test_statistics_reject_inconsistent_bridge_counts():
    with pytest.raises(
        ValueError,
        match=(
            "BridgeLab recommendation counts "
            "must equal evaluated"
        ),
    ):
        CorpusBenchmarkStatistics(
            total=1,
            evaluated=1,
            skipped_unknown_system=0,
            bridgelab_recommended=0,
            bridgelab_abstained=0,
            agreements=1,
            disagreement_counts=tuple(
                (
                    kind,
                    1
                    if kind is DisagreementKind.AGREEMENT
                    else 0,
                )
                for kind in DisagreementKind
            ),
        )


def test_statistics_reject_duplicate_disagreement_kind():
    counts = (
        (
            DisagreementKind.AGREEMENT,
            1,
        ),
        (
            DisagreementKind.AGREEMENT,
            0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="duplicate disagreement kind",
    ):
        CorpusBenchmarkStatistics(
            total=1,
            evaluated=1,
            skipped_unknown_system=0,
            bridgelab_recommended=1,
            bridgelab_abstained=0,
            agreements=1,
            disagreement_counts=counts,
        )
