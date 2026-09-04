from bridge import Auction, BiddingContext, Call, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc_1h_responses import create_sayc_one_heart_response_engine


def ctx(hand: str, *, options=None, system="SAYC", calls=("1H", "P")):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, options or {}),
    )


def test_pass_0_to_5():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("J842.976.854.Q92")
    )
    assert result.recommended_call == Call.pass_()


def test_simple_raise_with_6_to_9_and_three_hearts():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q842.K76.A54.932")
    )
    assert result.recommended_call == Call.parse("2H")


def test_simple_raise_with_four_hearts():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q82.K764.A54.932")
    )
    assert result.recommended_call == Call.parse("2H")


def test_limit_raise_with_10_to_12_and_four_hearts():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q82.KJ74.A54.932")
    )
    assert result.recommended_call == Call.parse("3H")


def test_limit_raise_rejects_only_three_hearts():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q842.KJ7.A54.932")
    )
    assert not result.has_recommendation


def test_one_spade_with_four_spades_and_no_three_card_heart_support():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("KJ82.Q7.854.Q932")
    )
    assert result.recommended_call == Call.parse("1S")


def test_support_has_priority_over_one_spade():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("KJ82.Q76.854.932")
    )
    assert result.recommended_call == Call.parse("2H")


def test_bergen_configuration_disables_traditional_simple_raise():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q842.K76.A54.932", options={"major_raise_style": "bergen"})
    )
    assert not result.has_recommendation


def test_bergen_configuration_disables_traditional_limit_raise():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q82.KJ74.A54.932", options={"major_raise_style": "bergen"})
    )
    assert not result.has_recommendation


def test_explicit_traditional_configuration_allows_limit_raise():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q82.KJ74.A54.932", options={"major_raise_style": "traditional"})
    )
    assert result.recommended_call == Call.parse("3H")


def test_one_nt_is_not_implemented_because_forcing_treatment_is_optional():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("KQ3.82.J764.Q932")
    )
    assert not result.has_recommendation


def test_non_sayc_rejected():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q842.K76.A54.932", system="Acol")
    )
    assert not result.has_recommendation


def test_wrong_auction_rejected():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q842.K76.A54.932", calls=("1S", "P"))
    )
    assert not result.has_recommendation


def test_opponent_interference_rejected():
    result = create_sayc_one_heart_response_engine().evaluate(
        ctx("Q842.K76.A54.932", calls=("1H", "1S"))
    )
    assert not result.has_recommendation
