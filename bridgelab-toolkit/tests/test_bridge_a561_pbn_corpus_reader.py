"""A5.6.1 native PBN corpus reader tests."""

import pytest

from bridge.auction import Call
from bridge.corpus_decisions import (
    extract_corpus_bidding_decisions,
)
from bridge.models import Seat, Vulnerability
from bridge.pbn_corpus_reader import (
    read_pbn_text,
)


SAMPLE = """\
% PBN test

[Event "A5.6.1"]
[Board "129"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "W:95.98.T98.AKJ974 AK4.AQ4.AKJ5.QT3 JT8.T7652.Q3.652 Q7632.KJ3.7642.8"]
[Declarer "N"]
[Contract "3NT"]
[Result "12"]
[Auction "N"]
1C Pass 1D 3C
3NT AP
[Play "E"]
C2 C8 CJ CQ
*

[Event "A5.6.1"]
[Board "130"]
[Dealer "E"]
[Vulnerable "NS"]
[Deal "W:QT8.65.AKJT9.T95 A65.T4.Q86.J7632 KJ73.AKJ.72.KQ84 942.Q98732.543.A"]
[Declarer "E"]
[Contract "3NT"]
[Result "10"]
[Auction "E"]
1NT Pass 3C Pass
3D Pass 3NT AP
"""


def records():
    return read_pbn_text(
        SAMPLE,
        source="sample.pbn",
        provider="bridge-deals-db-pbn",
        provider_version="2.0",
    )


def test_reads_two_records():
    assert len(records()) == 2


def test_board_numbers():
    parsed = records()

    assert tuple(
        record.board_number
        for record in parsed
    ) == (
        129,
        130,
    )


def test_dealers():
    parsed = records()

    assert parsed[0].dealer is Seat.NORTH
    assert parsed[1].dealer is Seat.EAST


def test_vulnerability_none():
    assert (
        records()[0].vulnerability
        is Vulnerability.NONE
    )


def test_vulnerability_ns():
    assert (
        records()[1].vulnerability
        is Vulnerability.NS
    )


def test_deal_starting_seat_is_independent_of_dealer():
    record = records()[0]

    # Deal begins W:, while dealer is North.
    assert record.dealer is Seat.NORTH

    assert (
        record.deal.hand(
            Seat.WEST
        ).serialize()
        == "95.98.T98.AKJ974"
    )

    assert (
        record.deal.hand(
            Seat.NORTH
        ).serialize()
        == "AK4.AQ4.AKJ5.QT3"
    )


def test_all_four_hands_are_present():
    record = records()[0]

    assert set(record.deal.mapping) == {
        Seat.NORTH,
        Seat.EAST,
        Seat.SOUTH,
        Seat.WEST,
    }


def test_contract_is_parsed():
    record = records()[0]

    assert record.contract is not None
    assert record.contract.serialize() == "3NT N"


def test_contract_strain_is_notrump():
    record = records()[0]

    assert record.contract is not None

    assert (
        record.contract.serialize()
        == "3NT N"
    )


def test_contract_declarer_is_preserved():
    record = records()[0]

    assert record.contract is not None
    assert record.contract.declarer is Seat.NORTH


def test_result_becomes_tricks():
    assert records()[0].tricks == 12


def test_ap_expands_to_completed_auction():
    auction = records()[0].auction

    assert auction is not None
    assert auction.is_complete


def test_ap_adds_three_passes_after_contract():
    auction = records()[0].auction

    assert auction is not None

    assert tuple(
        call.serialize()
        for call in auction.calls[-3:]
    ) == (
        "P",
        "P",
        "P",
    )


def test_play_cards_are_not_auction_calls():
    auction = records()[0].auction

    assert auction is not None

    assert tuple(
        call.serialize()
        for call in auction.calls
    ) == (
        "1C",
        "P",
        "1D",
        "3C",
        "3NT",
        "P",
        "P",
        "P",
    )


def test_second_auction_is_parsed():
    auction = records()[1].auction

    assert auction is not None
    assert auction.is_complete

    assert tuple(
        call.serialize()
        for call in auction.calls
    ) == (
        "1NT",
        "P",
        "3C",
        "P",
        "3D",
        "P",
        "3NT",
        "P",
        "P",
        "P",
    )


def test_provenance_provider():
    record = records()[0]

    assert (
        record.provenance.provider
        == "bridge-deals-db-pbn"
    )


def test_provenance_source():
    assert (
        records()[0].provenance.source
        == "sample.pbn"
    )


def test_provenance_version():
    record = records()[0]

    assert (
        record.provenance.provider_version
        == "2.0"
    )


def test_provenance_notation():
    assert (
        records()[0].provenance.notation
        == "PBN"
    )


def test_provenance_transformation():
    assert (
        "parsed-native-pbn"
        in records()[0].provenance.transformations
    )


def test_record_id_uses_board_number():
    assert (
        records()[0].provenance.record_id
        == "129"
    )


def test_systems_remain_unknown():
    record = records()[0]

    assert record.ns_system is None
    assert record.ew_system is None


def test_decisions_can_be_extracted():
    record = records()[0]

    decisions = (
        extract_corpus_bidding_decisions(
            record
        )
    )

    assert len(decisions) == 8

    assert (
        decisions[0].observed_call
        == Call.parse("1C")
    )


def test_decision_seat_matches_dealer():
    decisions = (
        extract_corpus_bidding_decisions(
            records()[0]
        )
    )

    assert decisions[0].seat is Seat.NORTH


def test_decision_hand_matches_acting_seat():
    record = records()[0]

    decision = (
        extract_corpus_bidding_decisions(
            record
        )[0]
    )

    assert (
        decision.hand
        == record.deal.hand(Seat.NORTH)
    )


def test_decision_system_remains_unknown():
    decision = (
        extract_corpus_bidding_decisions(
            records()[0]
        )[0]
    )

    assert decision.system_id is None


def test_all_vulnerability_maps_to_both():
    text = """\
[Event "All vulnerability"]
[Board "1"]
[Dealer "W"]
[Vulnerable "All"]
[Deal "W:7.KQ9763.KQ7.A74 AT96.AJ5.2.KT532 K854.42.JT983.J6 QJ32.T8.A654.Q98"]
[Auction "W"]
1H Pass Pass X
2H 3S AP
"""

    record = read_pbn_text(
        text,
        source="all.pbn",
    )[0]

    assert (
        record.vulnerability
        is Vulnerability.BOTH
    )


def test_passed_out_ap_from_empty_auction():
    # Reuse a known-valid complete deal.  The Deal
    # starting seat is independent of the auction dealer.
    text = """\
[Event "Passed out"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "W:95.98.T98.AKJ974 AK4.AQ4.AKJ5.QT3 JT8.T7652.Q3.652 Q7632.KJ3.7642.8"]
[Auction "N"]
AP
"""

    record = read_pbn_text(
        text,
        source="passed.pbn",
    )[0]

    assert record.auction is not None
    assert record.auction.is_complete

    assert len(
        record.auction.calls
    ) == 4

    assert all(
        call == Call.parse("P")
        for call in record.auction.calls
    )


def test_passed_out_record_has_no_contract():
    text = """\
[Event "Passed out"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "W:95.98.T98.AKJ974 AK4.AQ4.AKJ5.QT3 JT8.T7652.Q3.652 Q7632.KJ3.7642.8"]
[Auction "N"]
AP
"""

    record = read_pbn_text(
        text,
        source="passed.pbn",
    )[0]

    assert record.contract is None


def test_all_four_vulnerability_values():
    base = """\
[Event "Vulnerability"]
[Board "1"]
[Dealer "N"]
[Vulnerable "{vulnerability}"]
[Deal "W:95.98.T98.AKJ974 AK4.AQ4.AKJ5.QT3 JT8.T7652.Q3.652 Q7632.KJ3.7642.8"]
[Auction "N"]
AP
"""

    expected = {
        "None": Vulnerability.NONE,
        "NS": Vulnerability.NS,
        "EW": Vulnerability.EW,
        "All": Vulnerability.BOTH,
    }

    for pbn_value, canonical in expected.items():
        record = read_pbn_text(
            base.format(
                vulnerability=pbn_value
            ),
            source="vulnerability.pbn",
        )[0]

        assert (
            record.vulnerability
            is canonical
        )


def test_invalid_vulnerability_rejected():
    text = SAMPLE.replace(
        '[Vulnerable "None"]',
        '[Vulnerable "Maybe"]',
        1,
    )

    with pytest.raises(
        ValueError,
        match="unsupported PBN vulnerability",
    ):
        read_pbn_text(
            text,
            source="bad.pbn",
        )


def test_missing_four_hands_rejected():
    text = SAMPLE.replace(
        "95.98.T98.AKJ974 "
        "AK4.AQ4.AKJ5.QT3 "
        "JT8.T7652.Q3.652 "
        "Q7632.KJ3.7642.8",
        "95.98.T98.AKJ974 "
        "AK4.AQ4.AKJ5.QT3",
        1,
    )

    with pytest.raises(
        ValueError,
        match="must contain four hands",
    ):
        read_pbn_text(
            text,
            source="bad-deal.pbn",
        )


def test_contract_without_declarer_rejected():
    text = SAMPLE.replace(
        '[Declarer "N"]\n',
        "",
        1,
    )

    with pytest.raises(
        ValueError,
        match="PBN contract requires Declarer",
    ):
        read_pbn_text(
            text,
            source="missing-declarer.pbn",
        )


def test_source_must_not_be_blank():
    with pytest.raises(
        ValueError,
        match="source must be a non-blank string",
    ):
        read_pbn_text(
            SAMPLE,
            source=" ",
        )


def test_provider_must_not_be_blank():
    with pytest.raises(
        ValueError,
        match="provider must be a non-blank string",
    ):
        read_pbn_text(
            SAMPLE,
            source="sample.pbn",
            provider=" ",
        )


def test_provider_version_must_not_be_blank():
    with pytest.raises(
        ValueError,
        match=(
            "provider_version must be None "
            "or a non-blank string"
        ),
    ):
        read_pbn_text(
            SAMPLE,
            source="sample.pbn",
            provider_version=" ",
        )


def test_non_string_text_rejected():
    with pytest.raises(
        TypeError,
        match="text must be a string",
    ):
        read_pbn_text(
            123,
            source="sample.pbn",
        )
