from bridge import Auction, BiddingContext, Call, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc_major_one_notrump import create_sayc_major_one_notrump_response_engine


def ctx(opening, hand, *, treatment=None, system="SAYC", calls=None):
    options = {}
    if treatment is not None:
        options["forcing_one_notrump"] = treatment
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls or (opening, "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, options),
    )


def test_1h_forcing_1nt():
    result = create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.82.J764.Q932", treatment="forcing")
    )
    assert result.recommended_call == Call.parse("1NT")
    assert "forcing" in result.recommended.explanation


def test_1h_nonforcing_1nt():
    result = create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.82.J764.Q932", treatment="nonforcing")
    )
    assert result.recommended_call == Call.parse("1NT")
    assert "nonforcing" in result.recommended.explanation


def test_1s_forcing_1nt():
    result = create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1S", "KQ.J82.8764.Q932", treatment=True)
    )
    assert result.recommended_call == Call.parse("1NT")


def test_1s_nonforcing_1nt():
    result = create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1S", "KQ.J82.8764.Q932", treatment=False)
    )
    assert result.recommended_call == Call.parse("1NT")


def test_unspecified_treatment_abstains():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.82.J764.Q932")
    ).has_recommendation


def test_1h_four_spades_blocks_1nt():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ83.82.J764.Q93", treatment="forcing")
    ).has_recommendation


def test_1h_three_heart_support_blocks_1nt():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.J82.8764.Q32", treatment="forcing")
    ).has_recommendation


def test_1s_three_spade_support_blocks_1nt():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1S", "KQ3.J82.8764.Q32", treatment="forcing")
    ).has_recommendation


def test_below_6_hcp_abstains():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "J93.82.J764.Q932", treatment="forcing")
    ).has_recommendation


def test_above_9_hcp_abstains():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.82.A764.Q932", treatment="forcing")
    ).has_recommendation


def test_unbalanced_hand_abstains():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.8.J7642.Q932", treatment="forcing")
    ).has_recommendation


def test_non_sayc_abstains():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.82.J764.Q932", treatment="forcing", system="Acol")
    ).has_recommendation


def test_wrong_auction_abstains():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.82.J764.Q932", treatment="forcing", calls=("1D","P"))
    ).has_recommendation


def test_interference_abstains():
    assert not create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1S", "KQ.J82.8764.Q932", treatment="forcing", calls=("1S","2C"))
    ).has_recommendation


def test_source_trace_present():
    result = create_sayc_major_one_notrump_response_engine().evaluate(
        ctx("1H", "KQ3.82.J764.Q932", treatment="forcing")
    )
    assert result.recommended.sources
    assert any(source.heading == "1NT" for source in result.recommended.sources)
    assert any(source.heading == "SAYC" for source in result.recommended.sources)
