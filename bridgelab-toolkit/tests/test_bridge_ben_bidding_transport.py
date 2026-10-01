"""A3.2 BEN-specific external bidding transport."""

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_providers import ProviderStatus
from bridge.ben_bidding_transport import (
    BenTransportConfig,
    build_ben_bid_params,
    parse_ben_bid_response,
)
from bridge.models import Hand, Seat, Vulnerability


def context(
    *,
    dealer=Seat.NORTH,
    calls=("1C", "P", "1NT"),
    vulnerability=Vulnerability.NONE,
):
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(dealer, calls),
        vulnerability=vulnerability,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


def test_config_defaults_to_local_ben_api():
    config = BenTransportConfig()

    assert config.base_url == "http://127.0.0.1:8085"
    assert config.timeout_seconds == 10.0
    assert config.details is True
    assert config.tournament is None


def test_request_serializes_bridge_state_for_ben():
    params = build_ben_bid_params(context())

    assert params["hand"] == "AKQJ5.K82.976.A7"
    assert params["seat"] == "W"
    assert params["dealer"] == "N"
    assert params["vul"] == ""
    assert params["ctx"] == "1C-P-1N"
    assert params["details"] == "true"


def test_absolute_vulnerability_mapping():
    expected = {
        Vulnerability.NONE: "",
        Vulnerability.NS: "NS",
        Vulnerability.EW: "EW",
        Vulnerability.BOTH: "Both",
    }

    for vulnerability, encoded in expected.items():
        params = build_ben_bid_params(
            context(vulnerability=vulnerability)
        )
        assert params["vul"] == encoded


def test_pass_double_redouble_and_notrump_encoding():
    ctx = context(
        calls=("1NT", "X", "XX", "P"),
    )

    params = build_ben_bid_params(ctx)

    assert params["ctx"] == "1N-X-XX-P"


def test_tournament_is_optional():
    params = build_ben_bid_params(
        context(),
        tournament="mp",
    )

    assert params["tournament"] == "mp"


def test_invalid_tournament_is_rejected():
    try:
        build_ben_bid_params(
            context(),
            tournament="rubber",
        )
    except ValueError as exc:
        assert "tournament" in str(exc)
    else:
        raise AssertionError("invalid tournament was accepted")


def test_success_response_normalizes_bid_and_candidates():
    observation = parse_ben_bid_response(
        {
            "bid": "3N",
            "who": "NN",
            "quality": "Good",
            "candidates": [
                {"call": "3N", "insta_score": 0.8},
                {"call": "4S", "insta_score": 0.1},
                {"call": "Db", "insta_score": 0.05},
            ],
        }
    )

    assert observation.status is ProviderStatus.SUCCESS
    assert observation.recommendation == "3NT"
    assert observation.alternatives == ("4S", "X")
    assert observation.model_id == "NN"
    assert "who=NN" in observation.notes
    assert "quality=Good" in observation.notes


def test_pass_response_is_normalized():
    observation = parse_ben_bid_response(
        {"bid": "PASS"}
    )

    assert observation.status is ProviderStatus.SUCCESS
    assert observation.recommendation == "P"


def test_ben_error_becomes_failed_observation():
    observation = parse_ben_bid_response(
        {"error": "Invalid hand format"}
    )

    assert observation.status is ProviderStatus.FAILED
    assert observation.recommendation is None
    assert "Invalid hand format" in observation.notes


def test_missing_bid_becomes_abstain():
    observation = parse_ben_bid_response(
        {"who": "NN"}
    )

    assert observation.status is ProviderStatus.ABSTAIN
    assert observation.recommendation is None


def test_invalid_bid_encoding_becomes_failed():
    observation = parse_ben_bid_response(
        {"bid": "NOT-A-BID"}
    )

    assert observation.status is ProviderStatus.FAILED
    assert observation.recommendation is None


def test_malformed_candidates_do_not_break_valid_recommendation():
    observation = parse_ben_bid_response(
        {
            "bid": "2H",
            "candidates": [
                None,
                {},
                {"call": "BAD"},
                {"call": "2H"},
                {"call": "2S"},
                {"call": "2S"},
            ],
        }
    )

    assert observation.status is ProviderStatus.SUCCESS
    assert observation.recommendation == "2H"
    assert observation.alternatives == ("2S",)
