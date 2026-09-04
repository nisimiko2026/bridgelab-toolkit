import pytest

from bridge import Strain, is_canonical_two_over_one_pair


@pytest.mark.parametrize(
    "opening,response",
    [
        (Strain.HEARTS, Strain.CLUBS),
        (Strain.HEARTS, Strain.DIAMONDS),
        (Strain.SPADES, Strain.CLUBS),
        (Strain.SPADES, Strain.DIAMONDS),
    ],
)
def test_exact_four_canonical_pairs(opening, response):
    assert is_canonical_two_over_one_pair(opening, response)


def test_one_spade_two_hearts_is_not_in_canonical_automatic_gf_set():
    assert not is_canonical_two_over_one_pair(Strain.SPADES, Strain.HEARTS)


def test_one_heart_one_spade_is_not_two_over_one():
    assert not is_canonical_two_over_one_pair(Strain.HEARTS, Strain.SPADES)


def test_minor_opening_pair_is_not_two_over_one():
    assert not is_canonical_two_over_one_pair(Strain.CLUBS, Strain.DIAMONDS)


def test_notrump_response_is_not_two_over_one():
    assert not is_canonical_two_over_one_pair(Strain.SPADES, Strain.NOTRUMP)


def test_type_validation():
    with pytest.raises(TypeError):
        is_canonical_two_over_one_pair(None, Strain.CLUBS)
