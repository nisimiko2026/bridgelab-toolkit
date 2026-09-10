import json
from io import StringIO

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.deal_analysis import AnalysisStage, AnalysisStatus
from bridge.deals import generate_deal
from bridge.full_deal_application import (
    FullDealApplicationErrorCode,
    FullDealApplicationRequest,
    analyze_full_deal_application,
    application_request_to_full_deal_input,
    full_deal_application_request_from_dict,
)
from bridge.full_deal_cli import EXIT_SUCCESS, run_cli
from bridge.models import Hand, Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


def _payload(
    calls=(),
    *,
    dealer="N",
    hand=None,
    vulnerability="None",
    system_options=None,
    requested_stages=("auction",),
):
    auction = Auction(Seat.parse(dealer), calls)
    actual_hand = hand or generate_deal(23).hand(auction.next_seat).serialize()
    return {
        "requested_stages": list(requested_stages),
        "bidding": {
            "hand": actual_hand,
            "auction": {"dealer": dealer, "calls": list(calls)},
            "vulnerability": vulnerability,
            "system": {"id": "SAYC", "options": system_options or {}},
        },
    }


def _typed_context(payload):
    bidding = payload["bidding"]
    auction_data = bidding["auction"]
    auction = Auction(Seat.parse(auction_data["dealer"]), auction_data["calls"])
    return BiddingContext.create(
        hand=Hand.parse(bidding["hand"]),
        auction=auction,
        vulnerability=Vulnerability(bidding["vulnerability"]),
        system=SystemContext.from_mapping(
            bidding["system"]["id"], bidding["system"].get("options", {})
        ),
    )


def test_existing_json_without_bidding_remains_compatible():
    request = full_deal_application_request_from_dict({"requested_stages": []})
    assert request == FullDealApplicationRequest(requested_stages=())


def test_valid_bidding_json_matches_equivalent_typed_context():
    payload = _payload(("1NT", "P"))
    parsed = full_deal_application_request_from_dict(payload).bidding
    expected = _typed_context(payload)
    assert parsed is not None
    assert parsed.hand == expected.hand
    assert parsed.evaluation == expected.evaluation
    assert parsed.auction.serialize() == expected.auction.serialize()
    assert parsed.seat is expected.seat
    assert parsed.vulnerability is expected.vulnerability
    assert parsed.system == expected.system


def test_evaluation_and_current_bidder_are_derived():
    payload = _payload(("1C", "P"), dealer="E")
    parsed = full_deal_application_request_from_dict(payload).bidding
    assert parsed is not None
    assert parsed.seat is parsed.auction.next_seat is Seat.WEST
    assert parsed.evaluation == _typed_context(payload).evaluation


@pytest.mark.parametrize("forbidden", ["route_id", "rule", "router", "owner", "evaluation", "seat"])
def test_internal_bidding_fields_are_not_accepted(forbidden):
    payload = _payload()
    payload["bidding"][forbidden] = "not-public"
    with pytest.raises(ValueError, match="Unsupported bidding field"):
        full_deal_application_request_from_dict(payload)


def test_unknown_auction_field_is_rejected():
    payload = _payload()
    payload["bidding"]["auction"]["route"] = "internal"
    with pytest.raises(ValueError, match="Unsupported bidding.auction field"):
        full_deal_application_request_from_dict(payload)


def test_unknown_system_field_is_rejected():
    payload = _payload()
    payload["bidding"]["system"]["implementation"] = "not-public"
    with pytest.raises(ValueError, match="Unsupported bidding.system field"):
        full_deal_application_request_from_dict(payload)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("bidding",), [], "bidding must be a JSON object"),
        (("bidding", "system"), [], "bidding.system must be a JSON object"),
        (
            ("bidding", "system", "options"),
            [],
            "bidding.system.options must be a JSON object",
        ),
        (
            ("bidding", "system", "options"),
            {"policy": 1},
            "bidding.system.options values must be strings",
        ),
    ],
)
def test_malformed_bidding_containers_and_option_values_are_rejected(
    path, value, message
):
    payload = _payload()
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(TypeError, match=message):
        full_deal_application_request_from_dict(payload)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("hand",), "AKQ", "hand must contain four"),
        (("auction", "dealer"), "Q", "invalid seat"),
        (("vulnerability",), "All", "must be one of"),
        (("auction", "calls"), ["8C"], "invalid bid"),
        (("auction", "calls"), ["1S", "1H"], "illegal call"),
    ],
)
def test_invalid_canonical_bidding_values_are_rejected(path, value, message):
    payload = _payload()
    target = payload["bidding"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError, match=message):
        full_deal_application_request_from_dict(payload)


def test_empty_calls_and_system_options_default_canonically():
    payload = _payload()
    del payload["bidding"]["auction"]["calls"]
    del payload["bidding"]["system"]["options"]
    bidding = full_deal_application_request_from_dict(payload).bidding
    assert bidding is not None
    assert bidding.auction.calls == ()
    assert bidding.system.options == ()


@pytest.mark.parametrize("missing", ["hand", "auction", "vulnerability", "system"])
def test_required_bidding_fields_are_enforced(missing):
    payload = _payload()
    del payload["bidding"][missing]
    with pytest.raises(ValueError, match="Missing bidding field"):
        full_deal_application_request_from_dict(payload)


def test_matching_deal_and_bidding_hand_are_accepted():
    deal = generate_deal(41)
    auction = Auction(Seat.NORTH)
    payload = _payload(hand=deal.hand(auction.next_seat).serialize())
    payload["deal"] = deal.serialize()
    validation = application_request_to_full_deal_input(
        full_deal_application_request_from_dict(payload)
    )
    assert validation.is_valid


def test_conflicting_deal_and_bidding_hand_return_validation_error():
    deal = generate_deal(41)
    payload = _payload(hand=deal.hand(Seat.EAST).serialize())
    payload["deal"] = deal.serialize()
    validation = application_request_to_full_deal_input(
        full_deal_application_request_from_dict(payload)
    )
    assert not validation.is_valid
    assert validation.errors[0].code is FullDealApplicationErrorCode.VALIDATION_ERROR
    assert validation.errors[0].field == "bidding.hand"


def test_bidding_stage_reaches_existing_router():
    response = analyze_full_deal_application(
        full_deal_application_request_from_dict(_payload()),
        bidding_router=create_standard_sayc_router(),
    )
    assert response.success
    assert response.canonical_result is not None
    assert response.canonical_result.attempted_stages == (AnalysisStage.AUCTION.value,)


def test_bidding_without_auction_stage_is_retained_but_not_executed():
    request = full_deal_application_request_from_dict(
        _payload(requested_stages=())
    )
    response = analyze_full_deal_application(
        request, bidding_router=create_standard_sayc_router()
    )
    assert request.bidding is not None
    assert response.canonical_result is not None
    assert response.canonical_result.attempted_stages == ()


def test_auction_without_bidding_preserves_missing_state_behavior():
    request = full_deal_application_request_from_dict(
        {"requested_stages": ["auction"]}
    )
    response = analyze_full_deal_application(
        request, bidding_router=create_standard_sayc_router()
    )
    assert response.canonical_result is not None
    assert response.canonical_result.attempted_stages == ()
    assert response.canonical_result.skipped_stages[0].reason.value == "insufficient-stage-state"


def test_representative_non_policy_json_and_typed_results_match():
    payload = _payload()
    json_request = full_deal_application_request_from_dict(payload)
    typed_request = FullDealApplicationRequest(
        requested_stages=(AnalysisStage.AUCTION,), bidding=_typed_context(payload)
    )
    json_result = analyze_full_deal_application(
        json_request, bidding_router=create_standard_sayc_router()
    )
    typed_result = analyze_full_deal_application(
        typed_request, bidding_router=create_standard_sayc_router()
    )
    assert json_result.structured_result == typed_result.structured_result


def test_policy_gated_route_preserves_empty_registry_abstention():
    calls = ("1NT", "P", "2D", "P", "2H", "P")
    options = {"jacoby_continuation_strength_policy": "missing"}
    payload = _payload(calls, system_options=options)
    json_request = full_deal_application_request_from_dict(payload)
    typed_request = FullDealApplicationRequest(
        requested_stages=(AnalysisStage.AUCTION,), bidding=_typed_context(payload)
    )
    json_result = analyze_full_deal_application(
        json_request, bidding_router=create_standard_sayc_router()
    )
    typed_result = analyze_full_deal_application(
        typed_request, bidding_router=create_standard_sayc_router()
    )
    assert json_result.structured_result == typed_result.structured_result
    assert json_result.canonical_result is not None
    stage_result = json_result.canonical_result.subsystem_results[0]
    assert stage_result.status is AnalysisStatus.ABSTAIN
    assert stage_result.abstention_code.value == "policy-required"


def test_response_serialization_is_deterministic():
    request = full_deal_application_request_from_dict(_payload(("1NT", "P")))
    first = analyze_full_deal_application(
        request, bidding_router=create_standard_sayc_router()
    )
    second = analyze_full_deal_application(
        request, bidding_router=create_standard_sayc_router()
    )
    assert json.dumps(first.structured_result, sort_keys=True) == json.dumps(
        second.structured_result, sort_keys=True
    )


def test_cli_file_and_stdin_share_bidding_parser(tmp_path):
    payload = _payload()
    request_file = tmp_path / "bidding.json"
    request_file.write_text(json.dumps(payload), encoding="utf-8")
    file_out, file_err = StringIO(), StringIO()
    stdin_out, stdin_err = StringIO(), StringIO()
    file_code = run_cli(
        ("--input", str(request_file), "--format", "json"),
        stdout=file_out,
        stderr=file_err,
    )
    stdin_code = run_cli(
        ("--input", "-", "--format", "json"),
        stdin=StringIO(json.dumps(payload)),
        stdout=stdin_out,
        stderr=stdin_err,
    )
    assert file_code == stdin_code == EXIT_SUCCESS
    assert json.loads(file_out.getvalue()) == json.loads(stdin_out.getvalue())
    assert file_err.getvalue() == stdin_err.getvalue() == ""


def test_standard_router_remains_45_routes():
    assert len(create_standard_sayc_router().routes) == 45
