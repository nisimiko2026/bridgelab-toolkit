import json
from io import StringIO

import pytest

from bridge.auction import Bid, Contract, Doubling, Strain
from bridge.deal_analysis import AnalysisStage, AnalysisStatus
from bridge.deals import generate_deal
from bridge.declarer_play_state import DeclarerPlayInput, PlayedCard, Trick
from bridge.declarer_recommendation import DeclarerTechnique
from bridge.full_deal_application import (
    FullDealApplicationErrorCode,
    FullDealApplicationRequest,
    analyze_full_deal_application,
    application_request_to_full_deal_input,
    full_deal_application_request_from_dict,
)
from bridge.full_deal_cli import EXIT_SUCCESS, run_cli
from bridge.models import Card, Seat


def _payload(*, requested_stages=("declarer-play",)):
    return {
        "requested_stages": list(requested_stages),
        "declarer_play": {
            "contract": "3NT S",
            "declarer_cards": ["KC", "QC", "2S"],
            "dummy_cards": ["AC", "JC", "TC", "9C", "3S"],
            "completed_tricks": [],
            "current_trick": {"leader": "S", "plays": []},
            "vulnerability": "None",
        },
    }


def _parsed(payload=None):
    request = full_deal_application_request_from_dict(payload or _payload())
    assert request.declarer_play is not None
    return request.declarer_play


def _play(seat, card):
    return {"seat": seat, "card": card}


def test_existing_json_without_declarer_play_is_unchanged():
    request = full_deal_application_request_from_dict({"requested_stages": []})
    assert request == FullDealApplicationRequest(requested_stages=())


def test_valid_json_builds_canonical_declarer_input():
    source = _parsed()
    assert isinstance(source, DeclarerPlayInput)
    assert source.contract == Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH)
    assert source.declarer_cards == frozenset(map(Card.parse, ("KC", "QC", "2S")))
    assert source.dummy_cards == frozenset(
        map(Card.parse, ("AC", "JC", "TC", "9C", "3S"))
    )


@pytest.mark.parametrize(
    "contract",
    [
        Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH),
        Contract(Bid(4, Strain.HEARTS), Seat.NORTH, Doubling.DOUBLED),
        Contract(Bid(2, Strain.SPADES), Seat.EAST, Doubling.REDOUBLED),
    ],
)
def test_contract_parse_is_exact_serialize_inverse(contract):
    assert Contract.parse(contract.serialize()) == contract


@pytest.mark.parametrize(
    "value", ["3NT", "3NT south", "3nt S", "3NTXXX S", "8C N", 3]
)
def test_malformed_or_noncanonical_contract_is_rejected(value):
    with pytest.raises((TypeError, ValueError)):
        Contract.parse(value)


def test_declarer_and_opening_leader_are_derived_from_contract():
    source = _parsed()
    assert source.declarer_seat is Seat.SOUTH
    assert source.opening_leader is Seat.WEST


@pytest.mark.parametrize(
    ("plays", "actor"),
    [
        ([], Seat.SOUTH),
        ([_play("S", "2H")], Seat.WEST),
        ([_play("S", "2H"), _play("W", "3H")], Seat.NORTH),
        (
            [_play("S", "2H"), _play("W", "3H"), _play("N", "4H")],
            Seat.EAST,
        ),
    ],
)
def test_current_actor_is_derived_from_current_trick(plays, actor):
    payload = _payload()
    payload["declarer_play"]["current_trick"]["plays"] = plays
    assert _parsed(payload).current_actor is actor


def test_completed_trick_maps_to_canonical_types():
    payload = _payload()
    payload["declarer_play"]["completed_tricks"] = [
        {
            "leader": "W",
            "plays": [
                _play("W", "2H"),
                _play("N", "3H"),
                _play("E", "4H"),
                _play("S", "5H"),
            ],
        }
    ]
    trick = _parsed(payload).completed_tricks[0]
    assert isinstance(trick, Trick)
    assert trick.is_complete
    assert trick.plays[0] == PlayedCard(Seat.WEST, Card.parse("2H"))


@pytest.mark.parametrize("field", ["completed_tricks", "current_trick"])
def test_invalid_trick_order_is_rejected(field):
    payload = _payload()
    trick = {"leader": "W", "plays": [_play("N", "2H")]}
    if field == "completed_tricks":
        trick["plays"] += [
            _play("E", "3H"),
            _play("S", "4H"),
            _play("W", "5H"),
        ]
        payload["declarer_play"][field] = [trick]
    else:
        payload["declarer_play"][field] = trick
    with pytest.raises(ValueError, match="clockwise"):
        full_deal_application_request_from_dict(payload)


def test_incomplete_completed_trick_and_complete_current_trick_are_rejected():
    payload = _payload()
    payload["declarer_play"]["completed_tricks"] = [
        {"leader": "W", "plays": [_play("W", "2H")]}
    ]
    with pytest.raises(ValueError, match="exactly four"):
        full_deal_application_request_from_dict(payload)
    payload = _payload()
    payload["declarer_play"]["current_trick"] = {
        "leader": "W",
        "plays": [
            _play("W", "2H"),
            _play("N", "3H"),
            _play("E", "4H"),
            _play("S", "5H"),
        ],
    }
    with pytest.raises(ValueError, match="cannot already be complete"):
        full_deal_application_request_from_dict(payload)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("declarer_play",), [], "must be a JSON object"),
        (("declarer_play", "declarer_cards"), "KC", "must be an array"),
        (("declarer_play", "completed_tricks"), {}, "must be an array"),
        (("declarer_play", "current_trick"), [], "must be a JSON object"),
    ],
)
def test_malformed_nested_types_are_rejected(path, value, message):
    payload = _payload()
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(TypeError, match=message):
        full_deal_application_request_from_dict(payload)


@pytest.mark.parametrize(
    "missing",
    ["contract", "declarer_cards", "dummy_cards", "completed_tricks", "current_trick"],
)
def test_required_fields_are_enforced(missing):
    payload = _payload()
    del payload["declarer_play"][missing]
    with pytest.raises(ValueError, match="Missing declarer_play field"):
        full_deal_application_request_from_dict(payload)


@pytest.mark.parametrize(
    ("container", "field"),
    [
        ("declarer_play", "technique"),
        ("declarer_play", "engine"),
        ("declarer_play", "algorithm"),
        ("current_trick", "actor"),
    ],
)
def test_internal_selectors_and_unknown_fields_are_rejected(container, field):
    payload = _payload()
    target = payload["declarer_play"]
    if container == "current_trick":
        target = target["current_trick"]
    target[field] = "internal"
    with pytest.raises(ValueError, match="Unsupported"):
        full_deal_application_request_from_dict(payload)


def test_unknown_play_field_is_rejected():
    payload = _payload()
    payload["declarer_play"]["current_trick"] = {
        "leader": "S",
        "plays": [{"seat": "S", "card": "2H", "owner": "internal"}],
    }
    with pytest.raises(ValueError, match="Unsupported"):
        full_deal_application_request_from_dict(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("declarer_cards", ["1C"]),
        ("vulnerability", "All"),
    ],
)
def test_invalid_card_and_vulnerability_are_rejected(field, value):
    payload = _payload()
    payload["declarer_play"][field] = value
    with pytest.raises(ValueError):
        full_deal_application_request_from_dict(payload)


def test_invalid_trick_seat_is_rejected():
    payload = _payload()
    payload["declarer_play"]["current_trick"]["leader"] = "Q"
    with pytest.raises(ValueError, match="invalid seat"):
        full_deal_application_request_from_dict(payload)


def test_omitted_vulnerability_remains_unsupplied():
    payload = _payload()
    del payload["declarer_play"]["vulnerability"]
    assert _parsed(payload).vulnerability is None


def test_duplicate_card_within_holding_is_rejected_before_set_conversion():
    payload = _payload()
    payload["declarer_play"]["declarer_cards"] = ["KC", "KC"]
    with pytest.raises(ValueError, match="duplicate"):
        full_deal_application_request_from_dict(payload)


def test_overlapping_visible_cards_use_existing_invalid_state_behavior():
    payload = _payload()
    payload["declarer_play"]["dummy_cards"].append("KC")
    response = analyze_full_deal_application(
        full_deal_application_request_from_dict(payload)
    )
    assert response.canonical_result is not None
    result = response.canonical_result.subsystem_results[0]
    assert result.status is AnalysisStatus.NO_DECISION
    assert result.abstention_code.value == "missing-state"


def test_duplicate_played_card_uses_existing_invalid_state_behavior():
    payload = _payload()
    repeated = {
        "leader": "W",
        "plays": [
            _play("W", "2H"),
            _play("N", "3H"),
            _play("E", "4H"),
            _play("S", "5H"),
        ],
    }
    payload["declarer_play"]["completed_tricks"] = [repeated, repeated]
    response = analyze_full_deal_application(
        full_deal_application_request_from_dict(payload)
    )
    result = response.canonical_result.subsystem_results[0]
    assert result.abstention_code.value == "missing-state"


def _deal_payload():
    deal = generate_deal(73)
    payload = _payload()
    payload["deal"] = deal.serialize()
    payload["declarer_play"]["declarer_cards"] = [
        card.serialize() for card in deal.hand(Seat.SOUTH)
    ]
    payload["declarer_play"]["dummy_cards"] = [
        card.serialize() for card in deal.hand(Seat.NORTH)
    ]
    return deal, payload


def test_matching_deal_ownership_is_accepted():
    _, payload = _deal_payload()
    validation = application_request_to_full_deal_input(
        full_deal_application_request_from_dict(payload)
    )
    assert validation.is_valid


def test_deal_holding_conflict_is_validation_error():
    deal, payload = _deal_payload()
    payload["declarer_play"]["declarer_cards"][0] = next(
        iter(deal.hand(Seat.EAST))
    ).serialize()
    validation = application_request_to_full_deal_input(
        full_deal_application_request_from_dict(payload)
    )
    assert validation.errors[0].code is FullDealApplicationErrorCode.VALIDATION_ERROR
    assert validation.errors[0].field == "declarer_play"


def test_deal_play_history_conflict_is_validation_error():
    deal, payload = _deal_payload()
    payload["declarer_play"]["declarer_cards"] = []
    payload["declarer_play"]["dummy_cards"] = []
    payload["declarer_play"]["completed_tricks"] = [
        {
            "leader": "W",
            "plays": [
                _play("W", next(iter(deal.hand(Seat.NORTH))).serialize()),
                _play("N", next(iter(deal.hand(Seat.EAST))).serialize()),
                _play("E", next(iter(deal.hand(Seat.SOUTH))).serialize()),
                _play("S", next(iter(deal.hand(Seat.WEST))).serialize()),
            ],
        }
    ]
    validation = application_request_to_full_deal_input(
        full_deal_application_request_from_dict(payload)
    )
    assert validation.errors[0].code is FullDealApplicationErrorCode.VALIDATION_ERROR


def test_deal_visible_holding_cannot_also_contain_played_card():
    deal, payload = _deal_payload()
    played = next(iter(deal.hand(Seat.SOUTH))).serialize()
    payload["declarer_play"]["current_trick"] = {
        "leader": "S",
        "plays": [_play("S", played)],
    }
    validation = application_request_to_full_deal_input(
        full_deal_application_request_from_dict(payload)
    )
    assert validation.errors[0].code is FullDealApplicationErrorCode.VALIDATION_ERROR
    assert validation.errors[0].field == "declarer_play"


def test_stage_requested_executes_existing_simple_unblock():
    response = analyze_full_deal_application(
        full_deal_application_request_from_dict(_payload())
    )
    result = response.canonical_result.subsystem_results[0]
    assert result.status is AnalysisStatus.RECOMMENDATION
    assert result.action.card == Card.parse("KC")
    assert result.debug_metadata == (("technique", "simple-unblock-king"), ("card", "KC"))


def test_supplied_without_stage_is_retained_but_not_executed():
    request = full_deal_application_request_from_dict(
        _payload(requested_stages=())
    )
    response = analyze_full_deal_application(request)
    assert request.declarer_play is not None
    assert response.canonical_result.attempted_stages == ()


def test_stage_without_input_preserves_insufficient_state_and_neither_is_unchanged():
    requested = analyze_full_deal_application(
        full_deal_application_request_from_dict(
            {"requested_stages": ["declarer-play"]}
        )
    )
    neither = analyze_full_deal_application(
        full_deal_application_request_from_dict({"requested_stages": []})
    )
    assert requested.canonical_result.skipped_stages[0].reason.value == "insufficient-stage-state"
    assert neither.canonical_result.attempted_stages == ()


def test_json_and_equivalent_typed_results_match():
    payload = _payload()
    parsed = _parsed(payload)
    json_result = analyze_full_deal_application(
        full_deal_application_request_from_dict(payload)
    )
    typed_result = analyze_full_deal_application(
        FullDealApplicationRequest(
            requested_stages=(AnalysisStage.DECLARER_PLAY,),
            declarer_play=parsed,
        )
    )
    assert json_result.structured_result == typed_result.structured_result


def test_non_applicable_state_preserves_no_decision():
    payload = _payload()
    payload["declarer_play"]["contract"] = "4H S"
    response = analyze_full_deal_application(
        full_deal_application_request_from_dict(payload)
    )
    result = response.canonical_result.subsystem_results[0]
    assert result.status is AnalysisStatus.NO_DECISION
    assert result.abstention_code.value == "technique-not-applicable"


def test_response_serialization_is_deterministic():
    request = full_deal_application_request_from_dict(_payload())
    first = analyze_full_deal_application(request).structured_result
    second = analyze_full_deal_application(request).structured_result
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_cli_file_and_stdin_use_shared_declarer_parser(tmp_path):
    payload = _payload()
    request_file = tmp_path / "declarer.json"
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


def test_production_declarer_inventory_remains_one_without_public_registry():
    assert tuple(DeclarerTechnique) == (DeclarerTechnique.SIMPLE_UNBLOCK_KING,)
    payload = _payload()["declarer_play"]
    assert not {"technique", "engine", "algorithm"} & set(payload)
