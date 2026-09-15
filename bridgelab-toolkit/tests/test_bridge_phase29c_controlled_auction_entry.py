"""Focused Phase 29C checks for canonical incremental auction entry."""

import pytest

from bridge.bidding_read_only_gui import (
    AuctionEntryModel,
    BiddingForm,
    analyze_bidding_view,
)
from bridge.models import Seat


def test_empty_model_uses_dealer_and_canonical_turn():
    model = AuctionEntryModel.create("S")
    assert model.dealer is model.next_seat is Seat.SOUTH
    assert model.calls == () and not model.is_complete


def test_add_opening_and_multiple_calls_preserves_order_and_turn():
    model = AuctionEntryModel.create("N").add("1c").add("pass").add("1H")
    assert model.calls == ("1C", "P", "1H")
    assert model.next_seat is Seat.WEST


def test_pass_double_and_redouble_use_canonical_legal_calls():
    model = AuctionEntryModel.create().add("1H")
    assert "P" in model.legal_call_values and "X" in model.legal_call_values
    model = model.add("X")
    assert "XX" in model.legal_call_values
    assert model.add("XX").calls == ("1H", "X", "XX")


def test_illegal_call_is_rejected_without_mutating_previous_state():
    model = AuctionEntryModel.create().add("1H")
    with pytest.raises(ValueError, match="illegal call"):
        model.add("1D")
    assert model.calls == ("1H",) and model.next_seat is Seat.EAST


def test_malformed_call_is_rejected_without_mutation():
    model = AuctionEntryModel.create()
    with pytest.raises(ValueError, match="invalid bid"):
        model.add("8C")
    assert model.calls == ()


def test_undo_removes_latest_and_is_safe_when_empty():
    model = AuctionEntryModel.create().add("1C").add("P")
    assert model.undo().calls == ("1C",)
    assert AuctionEntryModel.create().undo().calls == ()


def test_clear_and_dealer_change_reset_deterministically():
    model = AuctionEntryModel.create().add("1C")
    assert model.clear() == AuctionEntryModel.create("N")
    changed = model.change_dealer("W")
    assert changed.calls == () and changed.dealer is changed.next_seat is Seat.WEST
    assert model.change_dealer("W") == changed


def test_bidding_form_receives_exact_controlled_call_order():
    model = AuctionEntryModel.create("E").add("1C").add("P")
    form = BiddingForm("KQJ876.32.43.543", "E", model.to_bidding_calls())
    assert form.to_payload()["bidding"]["auction"] == {
        "dealer": "E", "calls": ["1C", "P"]
    }


def test_valid_unsupported_route_still_abstains_without_call():
    model = AuctionEntryModel.create().add("1C").add("1D")
    form = BiddingForm("KQJ876.32.43.543", auction_calls=model.calls)
    view = analyze_bidding_view(form.to_payload())
    assert (view["status"], view["call"], view["abstention_code"]) == (
        "abstain", None, "no-route"
    )


def test_recommendation_keeps_explanation_provenance_rule_and_route():
    form = BiddingForm("KQJ876.32.43.543")
    view = analyze_bidding_view(form.to_payload())
    assert view["status"] == "recommendation" and view["call"]
    assert view["explanation"] and view["sources"] and view["rule_id"]
    assert view["route_id"] == "sayc.opening"


def test_entry_model_contains_state_operations_but_no_decision_fields():
    assert set(AuctionEntryModel.__dataclass_fields__) == {"dealer", "calls"}
    assert not any(
        name in AuctionEntryModel.__dict__
        for name in ("recommend", "decide", "rule_id", "route_id", "threshold")
    )
