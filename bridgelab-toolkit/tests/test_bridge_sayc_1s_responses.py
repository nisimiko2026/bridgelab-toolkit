from bridge import Auction, BiddingContext, Call, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc_1s_responses import create_sayc_one_spade_response_engine


def ctx(hand: str, *, options=None, system="SAYC", calls=("1S", "P")):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, options or {}),
    )


def test_pass_0_to_5():
    assert create_sayc_one_spade_response_engine().evaluate(
        ctx("J842.976.854.Q92")
    ).recommended_call == Call.pass_()


def test_simple_raise_with_three_spades():
    assert create_sayc_one_spade_response_engine().evaluate(
        ctx("Q84.K76.A54.9432")
    ).recommended_call == Call.parse("2S")


def test_simple_raise_with_four_spades():
    assert create_sayc_one_spade_response_engine().evaluate(
        ctx("Q842.K76.A54.932")
    ).recommended_call == Call.parse("2S")


def test_limit_raise_with_four_spades():
    assert create_sayc_one_spade_response_engine().evaluate(
        ctx("KJ84.Q76.A54.932")
    ).recommended_call == Call.parse("3S")


def test_limit_raise_rejects_only_three_spades():
    assert not create_sayc_one_spade_response_engine().evaluate(
        ctx("KJ8.Q764.A54.932")
    ).has_recommendation


def test_no_higher_ranking_major_response_is_added():
    result = create_sayc_one_spade_response_engine().evaluate(
        ctx("KJ8.Q764.A54.932")
    )
    assert all(
        decision.candidate != Call.parse("2H")
        for decision in result.decisions
        if decision.candidate is not None
    )


def test_bergen_configuration_disables_simple_raise():
    assert not create_sayc_one_spade_response_engine().evaluate(
        ctx("Q84.K76.A54.9432", options={"major_raise_style": "bergen"})
    ).has_recommendation


def test_bergen_configuration_disables_limit_raise():
    assert not create_sayc_one_spade_response_engine().evaluate(
        ctx("KJ84.Q76.A54.932", options={"major_raise_style": "bergen"})
    ).has_recommendation


def test_explicit_traditional_allows_limit_raise():
    assert create_sayc_one_spade_response_engine().evaluate(
        ctx("KJ84.Q76.A54.932", options={"major_raise_style": "traditional"})
    ).recommended_call == Call.parse("3S")


def test_one_nt_is_not_implemented():
    assert not create_sayc_one_spade_response_engine().evaluate(
        ctx("KQ.82.J764.Q9432")
    ).has_recommendation


def test_non_sayc_rejected():
    assert not create_sayc_one_spade_response_engine().evaluate(
        ctx("Q84.K76.A54.9432", system="Acol")
    ).has_recommendation


def test_wrong_auction_rejected():
    assert not create_sayc_one_spade_response_engine().evaluate(
        ctx("Q84.K76.A54.9432", calls=("1H", "P"))
    ).has_recommendation


def test_opponent_interference_rejected():
    assert not create_sayc_one_spade_response_engine().evaluate(
        ctx("Q84.K76.A54.9432", calls=("1S", "2C"))
    ).has_recommendation
