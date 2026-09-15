"""Focused Phase 29B form-model and controlled-validation checks."""

from dataclasses import FrozenInstanceError

import pytest

from bridge.bidding_read_only_gui import (
    DEALER_VALUES,
    SYSTEM_VALUES,
    VULNERABILITY_VALUES,
    BiddingForm,
    analyze_bidding_view,
)


def _form(**changes):
    values = {"hand": "KQJ876.32.43.543"}
    values.update(changes)
    return BiddingForm(**values)


def test_typed_form_produces_expected_fresh_application_payload():
    form = _form(
        dealer="E", auction_calls=("1C", "P"), vulnerability="NS",
        system_options=(("two_over_one", "game_force"),),
    )
    expected = {
        "requested_stages": ["auction"],
        "bidding": {
            "hand": form.hand,
            "auction": {"dealer": "E", "calls": ["1C", "P"]},
            "vulnerability": "NS",
            "system": {"id": "SAYC", "options": {"two_over_one": "game_force"}},
        },
    }
    first = form.to_payload()
    assert first == expected
    first["requested_stages"].clear()
    assert form.to_payload() == expected
    with pytest.raises(FrozenInstanceError):
        form.dealer = "W"


def test_controlled_values_come_from_canonical_domain_models():
    assert DEALER_VALUES == ("N", "E", "S", "W")
    assert VULNERABILITY_VALUES == ("None", "NS", "EW", "Both")
    assert SYSTEM_VALUES == ("SAYC", "TWO_OVER_ONE_GF")


@pytest.mark.parametrize("field,value", [("hand", "AKQ"), ("dealer", "Q"), ("vulnerability", "All")])
def test_malformed_controlled_or_hand_input_is_an_input_error(field, value):
    view = analyze_bidding_view(_form(**{field: value}).to_payload())
    assert view["status"] == "error" and view["errors"]


@pytest.mark.parametrize("calls", [("8C",), ("1S", "1H")])
def test_canonical_parser_rejects_malformed_or_illegal_auction(calls):
    view = analyze_bidding_view(_form(auction_calls=calls).to_payload())
    assert view["status"] == "error" and view["errors"]


def test_unknown_system_is_an_input_error_but_recognized_profiles_are_supported():
    assert analyze_bidding_view(_form(system="unknown").to_payload())["status"] == "error"
    for system in SYSTEM_VALUES:
        assert analyze_bidding_view(_form(system=system).to_payload())["status"] != "error"


def test_valid_unsupported_route_remains_abstain_without_guessing():
    view = analyze_bidding_view(_form(auction_calls=("1C", "1D")).to_payload())
    assert (view["status"], view["call"], view["abstention_code"]) == (
        "abstain", None, "no-route"
    )


def test_recommendation_identity_explanation_and_provenance_survive():
    view = analyze_bidding_view(_form().to_payload())
    assert view["status"] == "recommendation"
    assert view["call"] and view["explanation"] and view["sources"]
    assert view["rule_id"] and view["route_id"] == "sayc.opening"


def test_form_only_normalizes_input_and_contains_no_decision_fields():
    assert set(BiddingForm.__dataclass_fields__) == {
        "hand", "dealer", "auction_calls", "vulnerability", "system", "system_options"
    }
