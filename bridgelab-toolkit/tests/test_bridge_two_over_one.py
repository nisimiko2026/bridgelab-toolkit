import pytest

from bridge import Auction, Seat, SystemContext
from bridge.two_over_one import assess_two_over_one_game_force


def system(value=None):
    options = {} if value is None else {"two_over_one": value}
    return SystemContext.from_mapping("SAYC", options)


@pytest.mark.parametrize(
    "calls",
    [
        ("1H", "P", "2C"),
        ("1H", "P", "2D"),
        ("1S", "P", "2C"),
        ("1S", "P", "2D"),
    ],
)
def test_four_canonical_sequences_are_game_forcing(calls):
    result = assess_two_over_one_game_force(
        Auction(Seat.NORTH, calls),
        system("game_force"),
    )
    assert result.is_game_force
    assert result.sources


def test_1s_2h_is_not_silently_added():
    result = assess_two_over_one_game_force(
        Auction(Seat.NORTH, ("1S", "P", "2H")),
        system("game_force"),
    )
    assert not result.is_game_force


def test_minor_opening_does_not_create_2_over_1_game_force():
    result = assess_two_over_one_game_force(
        Auction(Seat.NORTH, ("1C", "P", "2D")),
        system("game_force"),
    )
    assert not result.is_game_force


def test_unspecified_treatment_is_not_game_force():
    result = assess_two_over_one_game_force(
        Auction(Seat.NORTH, ("1H", "P", "2C")),
        system(),
    )
    assert not result.is_game_force


def test_natural_treatment_is_not_game_force():
    result = assess_two_over_one_game_force(
        Auction(Seat.NORTH, ("1H", "P", "2C")),
        system("natural"),
    )
    assert not result.is_game_force


def test_boolean_true_selects_game_force():
    assert assess_two_over_one_game_force(
        Auction(Seat.NORTH, ("1S", "P", "2D")),
        system(True),
    ).is_game_force


def test_opponent_interference_is_not_exact_2_over_1():
    result = assess_two_over_one_game_force(
        Auction(Seat.NORTH, ("1H", "1S", "2C")),
        system("game_force"),
    )
    assert not result.is_game_force


def test_one_level_response_is_not_2_over_1():
    result = assess_two_over_one_game_force(
        Auction(Seat.NORTH, ("1H", "P", "1S")),
        system("game_force"),
    )
    assert not result.is_game_force


def test_two_nt_is_not_automatic_2_over_1_game_force():
    result = assess_two_over_one_game_force(
        Auction(Seat.NORTH, ("1S", "P", "2NT")),
        system("game_force"),
    )
    assert not result.is_game_force


def test_requires_auction_type():
    with pytest.raises(TypeError):
        assess_two_over_one_game_force(None, system("game_force"))


def test_requires_system_context():
    with pytest.raises(TypeError):
        assess_two_over_one_game_force(
            Auction(Seat.NORTH, ("1H", "P", "2C")),
            None,
        )
