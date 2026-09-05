from dataclasses import FrozenInstanceError

import pytest

from benchmarks.end_to_end_analysis_architecture import (
    _bidding,
    run_end_to_end_analysis_architecture_benchmark,
)
from bridge import (
    ActionKind,
    AnalysisAction,
    AnalysisStatus,
    Card,
    analyze_deal_decision,
    create_standard_sayc_router,
)


ROUTER = create_standard_sayc_router()
BENCHMARK = run_end_to_end_analysis_architecture_benchmark()


def result(name):
    return next(row for row in BENCHMARK.fixture_results if row["name"] == name)


def test_stage_detection_and_unsupported_state_are_stable():
    assert result("bidding-success")["stage"] == "auction"
    assert result("declarer-play-gap")["status"] == "no-decision"
    assert result("defensive-play-gap")["abstention_code"] == "missing-state"
    assert result("incomplete-state")["stage"] == "deal-summary"


def test_bidding_success_and_sources_are_normalized():
    actual = analyze_deal_decision(_bidding("KQJ876.32.43.543"), bidding_router=ROUTER)
    assert actual.status is AnalysisStatus.RECOMMENDATION
    assert actual.action.kind is ActionKind.BID
    assert actual.action.bid.serialize() == "2S"
    assert actual.evidence and actual.evidence[0].source is not None
    assert not hasattr(actual, "confidence")


def test_strong_two_club_phase12n_success():
    assert result("strong-2c-phase12n")["action"] == "2NT"
    assert result("strong-2c-phase12n")["status"] == "recommendation"


def test_all_abstention_modes_remain_abstentions():
    assert result("routed-source-abstention")["abstention_code"] == "rule-abstained"
    assert result("no-route")["abstention_code"] == "no-route"
    assert result("missing-policy")["abstention_code"] == "policy-required"
    assert all(result(name)["status"] == "abstain" for name in (
        "routed-source-abstention", "no-route", "missing-policy"
    ))


def test_action_model_distinguishes_bid_and_card_domains():
    card = Card.parse("AS")
    assert AnalysisAction(ActionKind.CARD_PLAY, card=card).card == card
    assert AnalysisAction(ActionKind.OPENING_LEAD, card=card).kind is ActionKind.OPENING_LEAD
    assert AnalysisAction(ActionKind.DEFENSIVE_CARD, card=card).kind is ActionKind.DEFENSIVE_CARD
    with pytest.raises(ValueError):
        AnalysisAction(ActionKind.BID, card=card)


def test_result_is_immutable_and_repeatable():
    actual = analyze_deal_decision(_bidding("KQJ876.32.43.543"), bidding_router=ROUTER)
    with pytest.raises(FrozenInstanceError):
        actual.status = AnalysisStatus.ERROR
    assert BENCHMARK == run_end_to_end_analysis_architecture_benchmark()


def test_architecture_benchmark_and_phase12_guards():
    assert (BENCHMARK.analyzed_positions, BENCHMARK.recommendations) == (8, 2)
    assert (BENCHMARK.abstentions, BENCHMARK.unsupported_states) == (3, 3)
    assert BENCHMARK.stage_counts == {"auction": 5, "deal-summary": 1, "declarer-play": 1, "defensive-play": 1}
    assert BENCHMARK.ordinary_benchmark == {"seeds": 10_000, "production_calls": 7_871, "completed": 761, "abstained": 9_239}
    assert BENCHMARK.phase12_guards["routes"] == 45
    assert BENCHMARK.phase12_guards["phase12n"] == 24
    assert BENCHMARK.phase13b_direction.startswith("A.")


def test_no_new_route_or_bidding_rule():
    assert len(ROUTER.routes) == 45
