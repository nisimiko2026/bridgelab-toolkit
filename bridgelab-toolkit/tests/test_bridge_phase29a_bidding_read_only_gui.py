"""Focused checks for the read-only application view."""

from copy import deepcopy

from bridge.bidding_read_only_gui import analyze_bidding_view


def _payload(calls=()):
    return {
        "requested_stages": ["auction"],
        "bidding": {
            "hand": "KQJ876.32.43.543",
            "auction": {"dealer": "N", "calls": list(calls)},
            "vulnerability": "None",
            "system": {"id": "SAYC", "options": {}},
        },
    }


def test_recommendation_preserves_action_explanation_source_and_identity():
    payload = _payload()
    before = deepcopy(payload)
    view = analyze_bidding_view(payload)
    assert view["status"] == "recommendation"
    assert view["call"] is not None
    assert view["explanation"]
    assert view["sources"]
    assert view["rule_id"] and view["route_id"] == "sayc.opening"
    assert view["system"] == view["profile"] == "SAYC"
    assert view["seat"] == "N"
    assert payload == before
    assert analyze_bidding_view(payload) == view


def test_no_route_abstains_without_a_guessed_call_or_source():
    view = analyze_bidding_view(_payload(("1C", "1D")))
    assert view["status"] == "abstain"
    assert view["call"] is None
    assert view["abstention_code"] == "no-route"
    assert view["explanation"] == "No production route supports this auction."
    assert view["sources"] == ()
    assert view["rule_id"] is None


def test_invalid_input_returns_an_error_without_running_engine():
    payload = _payload()
    payload["bidding"]["hand"] = "AKQ"
    view = analyze_bidding_view(payload)
    assert view["status"] == "error"
    assert "four dot-separated suits" in view["errors"][0]


def test_only_bidding_auction_stage_is_accepted():
    payload = _payload()
    payload["requested_stages"] = ["declarer-play"]
    assert analyze_bidding_view(payload)["status"] == "error"
