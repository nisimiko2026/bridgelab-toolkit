"""A5.3 corpus bidding decision extraction tests."""

import pytest

from bridge.auction import Auction, Call
from bridge.corpus import (
    CanonicalBoardRecord,
    SourceProvenance,
)
from bridge.corpus_decisions import (
    CorpusBiddingDecision,
    extract_corpus_bidding_decisions,
)
from bridge.deals import generate_deal
from bridge.models import Seat, Vulnerability


def make_record(
    *,
    calls: tuple[str, ...],
    dealer: Seat = Seat.NORTH,
    ns_system: str | None = None,
    ew_system: str | None = None,
) -> CanonicalBoardRecord:
    return CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider="expert-corpus",
            source="a53-test",
            record_id="board-53",
        ),
        dealer=dealer,
        vulnerability=Vulnerability.NS,
        deal=generate_deal(53),
        auction=Auction(
            dealer,
            calls,
        ),
        ns_system=ns_system,
        ew_system=ew_system,
    )


def test_extracts_one_decision_per_observed_call():
    record = make_record(
        calls=(
            "1C",
            "P",
            "1H",
            "P",
            "2H",
            "P",
            "P",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert len(decisions) == 8

    assert tuple(
        decision.observed_call.serialize()
        for decision in decisions
    ) == (
        "1C",
        "P",
        "1H",
        "P",
        "2H",
        "P",
        "P",
        "P",
    )


def test_seats_follow_actual_auction_rotation():
    record = make_record(
        calls=(
            "1C",
            "P",
            "1H",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert tuple(
        decision.seat
        for decision in decisions
    ) == (
        Seat.NORTH,
        Seat.EAST,
        Seat.SOUTH,
        Seat.WEST,
    )


def test_non_north_dealer_rotation_is_preserved():
    record = make_record(
        dealer=Seat.EAST,
        calls=(
            "P",
            "1C",
            "P",
            "1H",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert tuple(
        decision.seat
        for decision in decisions
    ) == (
        Seat.EAST,
        Seat.SOUTH,
        Seat.WEST,
        Seat.NORTH,
    )


def test_each_decision_contains_correct_hand():
    record = make_record(
        calls=(
            "1C",
            "P",
            "1H",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    for decision in decisions:
        assert (
            decision.hand
            == record.deal.hand(decision.seat)
        )


def test_each_auction_is_prefix_before_observed_call():
    record = make_record(
        calls=(
            "1C",
            "P",
            "1H",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert tuple(
        decision.auction.serialize()
        for decision in decisions
    ) == (
        "",
        "1C",
        "1C P",
        "1C P 1H",
    )


def test_prefix_snapshots_do_not_mutate_after_extraction():
    record = make_record(
        calls=(
            "1C",
            "P",
            "1H",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert decisions[0].auction.serialize() == ""
    assert decisions[1].auction.serialize() == "1C"
    assert decisions[2].auction.serialize() == "1C P"
    assert decisions[3].auction.serialize() == "1C P 1H"


def test_call_index_is_preserved():
    record = make_record(
        calls=(
            "1C",
            "P",
            "1H",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert tuple(
        decision.call_index
        for decision in decisions
    ) == (
        0,
        1,
        2,
        3,
    )


def test_provenance_is_preserved():
    record = make_record(
        calls=(
            "1C",
            "P",
            "P",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert all(
        decision.provenance is record.provenance
        for decision in decisions
    )

    assert (
        decisions[0].provenance.record_id
        == "board-53"
    )


def test_vulnerability_is_preserved():
    record = make_record(
        calls=(
            "P",
            "P",
            "P",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert all(
        decision.vulnerability
        is Vulnerability.NS
        for decision in decisions
    )


def test_system_metadata_follows_partnership():
    record = make_record(
        calls=(
            "1C",
            "P",
            "1H",
            "P",
        ),
        ns_system="2/1",
        ew_system="SAYC",
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert tuple(
        decision.system_id
        for decision in decisions
    ) == (
        "2/1",
        "SAYC",
        "2/1",
        "SAYC",
    )


def test_unknown_system_remains_unknown():
    record = make_record(
        calls=(
            "1C",
            "P",
            "P",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert all(
        decision.system_id is None
        for decision in decisions
    )


def test_observed_call_is_legal_for_each_prefix():
    record = make_record(
        calls=(
            "1S",
            "X",
            "XX",
            "2C",
            "P",
            "P",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert all(
        decision.auction.is_legal(
            decision.observed_call
        )
        for decision in decisions
    )


def test_passed_out_board_extracts_four_decisions():
    record = make_record(
        calls=(
            "P",
            "P",
            "P",
            "P",
        ),
    )

    decisions = extract_corpus_bidding_decisions(
        record
    )

    assert len(decisions) == 4
    assert all(
        decision.observed_call == Call.pass_()
        for decision in decisions
    )


def test_record_without_deal_is_rejected():
    record = CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider="test",
            source="test",
        ),
        dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
        auction=Auction(
            Seat.NORTH,
            ("P", "P", "P", "P"),
        ),
    )

    with pytest.raises(
        ValueError,
        match="record must contain a deal",
    ):
        extract_corpus_bidding_decisions(record)


def test_record_without_auction_is_rejected():
    record = CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider="test",
            source="test",
        ),
        dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
        deal=generate_deal(1),
    )

    with pytest.raises(
        ValueError,
        match="record must contain an auction",
    ):
        extract_corpus_bidding_decisions(record)


def test_invalid_record_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="record must be CanonicalBoardRecord",
    ):
        extract_corpus_bidding_decisions(object())


def test_decision_rejects_wrong_prefix_seat():
    record = make_record(
        calls=(
            "1C",
            "P",
            "P",
            "P",
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "auction next seat conflicts "
            "with decision seat"
        ),
    ):
        CorpusBiddingDecision(
            provenance=record.provenance,
            call_index=0,
            seat=Seat.EAST,
            hand=record.deal.hand(Seat.EAST),
            auction=Auction(Seat.NORTH),
            observed_call=Call.parse("1C"),
            vulnerability=record.vulnerability,
        )


def test_decision_rejects_illegal_observed_call():
    record = make_record(
        calls=(
            "1C",
            "P",
            "P",
            "P",
        ),
    )

    prefix = Auction(
        Seat.NORTH,
        ("1S",),
    )

    with pytest.raises(
        ValueError,
        match=(
            "observed call is illegal "
            "for auction prefix"
        ),
    ):
        CorpusBiddingDecision(
            provenance=record.provenance,
            call_index=1,
            seat=Seat.EAST,
            hand=record.deal.hand(Seat.EAST),
            auction=prefix,
            observed_call=Call.parse("1C"),
            vulnerability=record.vulnerability,
        )
