"""A6.3 duplicate bridge outcome scoring tests."""

import pytest

from bridge.auction import Contract
from bridge.corpus import Vulnerability
from bridge.outcome_scoring import score_contract_outcome


@pytest.mark.parametrize(
    ("contract_text", "tricks", "vulnerability", "expected"),
    (
        ("4H N", 10, Vulnerability.NONE, 420),
        ("4H N", 10, Vulnerability.NS, 620),
        ("3NT S", 9, Vulnerability.NONE, 400),
        ("3NT S", 9, Vulnerability.NS, 600),
        ("2S E", 8, Vulnerability.NONE, 110),
        ("2S E", 9, Vulnerability.NONE, 140),
        ("3C W", 9, Vulnerability.NONE, 110),
        ("5D N", 11, Vulnerability.NONE, 400),
        ("5D N", 11, Vulnerability.NS, 600),
        ("6NT N", 12, Vulnerability.NONE, 990),
        ("6NT N", 12, Vulnerability.NS, 1440),
        ("7S S", 13, Vulnerability.NONE, 1510),
        ("7S S", 13, Vulnerability.NS, 2210),
        ("4SX E", 10, Vulnerability.NONE, 590),
        ("4SX E", 11, Vulnerability.NONE, 690),
        ("4SX E", 11, Vulnerability.EW, 990),
        ("2HXX N", 8, Vulnerability.NONE, 640),
    ),
)
def test_made_contract_reference_scores(
    contract_text,
    tricks,
    vulnerability,
    expected,
) -> None:
    outcome = score_contract_outcome(
        Contract.parse(contract_text),
        tricks,
        vulnerability,
    )
    assert outcome.declarer_score == expected


@pytest.mark.parametrize(
    ("contract_text", "tricks", "vulnerability", "expected"),
    (
        ("4H N", 9, Vulnerability.NONE, -50),
        ("4H N", 9, Vulnerability.NS, -100),
        ("4SX N", 9, Vulnerability.NONE, -100),
        ("4SX N", 8, Vulnerability.NONE, -300),
        ("4SX N", 7, Vulnerability.NONE, -500),
        ("4SX N", 6, Vulnerability.NONE, -800),
        ("4SX N", 9, Vulnerability.NS, -200),
        ("4SX N", 8, Vulnerability.NS, -500),
        ("4SX N", 7, Vulnerability.NS, -800),
        ("4SXX N", 8, Vulnerability.NONE, -600),
        ("4SXX N", 8, Vulnerability.NS, -1000),
    ),
)
def test_defeated_contract_reference_scores(
    contract_text,
    tricks,
    vulnerability,
    expected,
) -> None:
    outcome = score_contract_outcome(
        Contract.parse(contract_text),
        tricks,
        vulnerability,
    )
    assert outcome.declarer_score == expected
    assert not outcome.made


def test_outcome_exposes_target_delta_and_vulnerability() -> None:
    outcome = score_contract_outcome(
        Contract.parse("4H N"),
        11,
        Vulnerability.NS,
    )
    assert outcome.target_tricks == 10
    assert outcome.trick_delta == 1
    assert outcome.made
    assert outcome.declarer_vulnerable


def test_vulnerability_is_relative_to_declarer_side() -> None:
    ns = score_contract_outcome(
        Contract.parse("4S N"), 10, Vulnerability.NS
    )
    ew = score_contract_outcome(
        Contract.parse("4S E"), 10, Vulnerability.NS
    )
    assert ns.declarer_vulnerable
    assert not ew.declarer_vulnerable
    assert ns.declarer_score == 620
    assert ew.declarer_score == 420


def test_ns_score_has_fixed_table_orientation() -> None:
    north = score_contract_outcome(
        Contract.parse("4S N"), 10, Vulnerability.NONE
    )
    east = score_contract_outcome(
        Contract.parse("4S E"), 10, Vulnerability.NONE
    )
    assert north.ns_score == 420
    assert east.ns_score == -420


def test_ns_score_reverses_negative_ew_declarer_score() -> None:
    outcome = score_contract_outcome(
        Contract.parse("4SX E"), 9, Vulnerability.NONE
    )
    assert outcome.declarer_score == -100
    assert outcome.ns_score == 100


@pytest.mark.parametrize("bad_tricks", (-1, 14, 7.5, True))
def test_invalid_trick_count_is_rejected(bad_tricks) -> None:
    with pytest.raises(ValueError, match="declarer_tricks"):
        score_contract_outcome(
            Contract.parse("3NT N"),
            bad_tricks,
            Vulnerability.NONE,
        )


def test_invalid_contract_type_is_rejected() -> None:
    with pytest.raises(TypeError, match="contract must be Contract"):
        score_contract_outcome(  # type: ignore[arg-type]
            object(), 9, Vulnerability.NONE
        )


def test_invalid_vulnerability_type_is_rejected() -> None:
    with pytest.raises(TypeError, match="vulnerability"):
        score_contract_outcome(  # type: ignore[arg-type]
            Contract.parse("3NT N"), 9, "NONE"
        )
