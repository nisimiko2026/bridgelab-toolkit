"""Focused Phase 29D tests for presentation-only auction helpers."""

from bridge.bidding_read_only_gui import (
    ALL_CANONICAL_CALLS,
    AuctionEntryModel,
    BiddingForm,
    analyze_bidding_view,
    canonical_call,
    friendly_call,
)


def test_special_calls_have_friendly_labels():
    assert friendly_call("P") == "Pass"
    assert friendly_call("X") == "Double"
    assert friendly_call("XX") == "Redouble"


def test_suits_use_symbols_and_notrump_remains_nt():
    assert tuple(friendly_call(value) for value in ("1C", "2D", "3H", "4S")) == (
        "1♣", "2♦", "3♥", "4♠"
    )
    assert friendly_call("7NT") == "7NT"


def test_all_possible_call_labels_are_deterministic_and_reversible():
    first = tuple(friendly_call(value) for value in ALL_CANONICAL_CALLS)
    assert len(first) == 38 and len(set(first)) == 38
    assert tuple(canonical_call(label) for label in first) == ALL_CANONICAL_CALLS
    assert tuple(friendly_call(value) for value in ALL_CANONICAL_CALLS) == first


def test_opening_call_appears_under_dealer_and_calls_rotate_by_canonical_entries():
    model = AuctionEntryModel.create("N").add("1C").add("P").add("1H").add("P")
    assert model.table_rows == (("1♣", "Pass", "1♥", "Pass"),)


def test_non_north_dealer_starts_in_its_column_and_wraps():
    model = AuctionEntryModel.create("S").add("1C").add("P").add("1H")
    assert model.table_rows == (
        ("", "", "1♣", "Pass"),
        ("1♥", "", "", ""),
    )


def test_undo_clear_and_completion_update_table_data():
    complete = AuctionEntryModel.create().add("1C").add("P").add("P").add("P")
    assert complete.is_complete
    reopened = complete.undo()
    assert not reopened.is_complete
    assert reopened.table_rows == (("1♣", "Pass", "Pass", ""),)
    assert complete.clear().table_rows == ()


def test_controlled_serialization_and_analysis_path_are_unchanged():
    model = AuctionEntryModel.create().add("1C").add("1D")
    assert model.to_bidding_calls() == ("1C", "1D")
    view = analyze_bidding_view(
        BiddingForm("KQJ876.32.43.543", auction_calls=model.calls).to_payload()
    )
    assert (view["status"], view["call"]) == ("abstain", None)


def test_recommendation_preserves_engine_supplied_fields():
    view = analyze_bidding_view(BiddingForm("KQJ876.32.43.543").to_payload())
    assert view["status"] == "recommendation" and view["call"]
    assert view["explanation"] and view["sources"] and view["rule_id"]
    assert view["route_id"] == "sayc.opening"


def test_presentation_helpers_have_no_decision_fields():
    prohibited = ("recommend", "rule", "route", "threshold", "priority")
    assert not any(word in name for name in ("friendly_call", "canonical_call") for word in prohibited)
