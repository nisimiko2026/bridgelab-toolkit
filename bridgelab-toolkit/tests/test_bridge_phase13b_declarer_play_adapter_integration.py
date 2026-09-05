from benchmarks.declarer_play_adapter_integration import (
    run_declarer_play_adapter_integration_benchmark,
)
from bridge import (
    AbstentionCode,
    ActionKind,
    AnalysisStage,
    AnalysisStatus,
    DealAnalysisContext,
    Subsystem,
    analyze_deal_decision,
    create_standard_sayc_router,
)


ROUTER = create_standard_sayc_router()
BENCHMARK = run_declarer_play_adapter_integration_benchmark()


def declarer_result():
    return analyze_deal_decision(DealAnalysisContext(stage=AnalysisStage.DECLARER_PLAY), bidding_router=ROUTER)


def row(name):
    return next(item for item in BENCHMARK.fixture_results if item["name"] == name)


def test_declarer_stage_dispatches_to_explicit_adapter_boundary():
    actual = declarer_result()
    assert actual.stage is AnalysisStage.DECLARER_PLAY
    assert actual.subsystem_results[0].subsystem is Subsystem.DECLARER_PLAY
    assert actual.subsystem_results[0].attempted


def test_missing_engine_never_fabricates_success_or_card():
    actual = declarer_result()
    assert actual.status is AnalysisStatus.NO_DECISION
    assert actual.action.kind is ActionKind.NONE
    assert actual.action.card is None


def test_declarer_abstention_has_stable_missing_state_code():
    assert declarer_result().abstention_code is AbstentionCode.MISSING_STATE


def test_missing_state_explanation_is_factual():
    assert "no production declarer state model" in declarer_result().explanation.lower()


def test_no_source_or_probability_evidence_is_invented():
    actual = declarer_result()
    assert actual.evidence == ()
    assert actual.probability_evidence == ()


def test_no_numeric_confidence_is_invented():
    assert not hasattr(declarer_result(), "confidence")


def test_repeated_declarer_analysis_is_structurally_identical():
    assert declarer_result() == declarer_result()


def test_inventory_records_no_callable_production_target():
    inventory = BENCHMARK.declarer_inventory[0]
    assert inventory["entry_point"] is None
    assert inventory["returns_card"] is False
    assert inventory["canonical_target"] is False


def test_probability_families_are_not_claimed_as_integrated():
    assert set(BENCHMARK.probability_inventory.values()) == {"NOT USED BY CURRENT DECLARER ENGINE"}


def test_bidding_success_is_unchanged():
    assert row("bidding-success")["action"] == "2S"
    assert row("bidding-success")["status"] == "recommendation"


def test_phase12n_two_notrump_still_works_through_top_level():
    assert row("strong-2c-phase12n")["action"] == "2NT"


def test_routes_remain_45_and_no_route_was_added():
    assert len(ROUTER.routes) == BENCHMARK.phase12_guards["routes"] == 45


def test_defensive_play_remains_explicitly_unintegrated():
    assert row("defensive-play-gap")["status"] == "no-decision"
    assert row("defensive-play-gap")["abstention_code"] == "unsupported-stage"


def test_extended_architecture_counts_are_exact():
    assert (BENCHMARK.analyzed_positions, BENCHMARK.recommendations) == (10, 2)
    assert (BENCHMARK.abstentions, BENCHMARK.no_decisions, BENCHMARK.errors) == (3, 5, 0)
    assert BENCHMARK.stage_counts == {
        "auction": 5, "deal-summary": 1, "declarer-play": 3, "defensive-play": 1,
    }
    assert BENCHMARK.action_counts == {"bid": 2, "none": 8}


def test_declarer_fixture_is_deterministic():
    assert row("declarer-missing-state") == row("declarer-repeat") | {"name": "declarer-missing-state"}


def test_ordinary_benchmark_guard_is_unchanged():
    assert BENCHMARK.ordinary_benchmark == {
        "seeds": 10_000, "production_calls": 7_871, "completed": 761, "abstained": 9_239,
    }


def test_phase12_guards_are_preserved():
    guards = BENCHMARK.phase12_guards
    assert guards["phase12n"] == 24 and guards["phase12o"] == 23
    assert guards["phase12q"] == 1_194 and guards["phase12r"] == 166
    assert guards["phase12s"] == 540 and guards["phase12t"] == 33
    assert guards["phase12g"] == {"4H": 17, "4S": 21}
    assert guards["phase12h"] == 197 and guards["phase12l"] == {"completed": 5, "abstained": 7}
    assert guards["jacoby"] == {"hearts": 62, "spades": 61}


def test_phase13c_direction_is_declarer_state_architecture():
    assert BENCHMARK.phase13c_direction == "D. DECLARER STATE ARCHITECTURE"


def test_benchmark_is_repeatable():
    assert BENCHMARK == run_declarer_play_adapter_integration_benchmark()


def test_existing_phase13a_fixture_names_are_retained():
    assert [item["name"] for item in BENCHMARK.fixture_results[:8]] == [
        "bidding-success", "routed-source-abstention", "no-route", "missing-policy",
        "strong-2c-phase12n", "declarer-play-gap", "defensive-play-gap", "incomplete-state",
    ]
