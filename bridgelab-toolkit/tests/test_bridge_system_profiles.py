import pytest

from bridge import SystemContext
from bridge.system_profiles import (
    SystemProfile,
    classify_system_profile,
    supports_two_over_one_game_force,
)


@pytest.mark.parametrize(
    "name",
    [
        "SAYC",
        "sayc",
        "Standard American Yellow Card",
    ],
)
def test_sayc_names_classify_as_sayc(name):
    system = SystemContext.from_mapping(name, {})
    assert classify_system_profile(system) is SystemProfile.SAYC


@pytest.mark.parametrize(
    "name",
    [
        "TWO_OVER_ONE_GF",
        "two_over_one_gf",
    ],
)
def test_two_over_one_names_classify_as_two_over_one_game_force(name):
    system = SystemContext.from_mapping(name, {})
    assert classify_system_profile(system) is SystemProfile.TWO_OVER_ONE_GF


def test_unknown_system_is_not_silently_classified():
    system = SystemContext.from_mapping("Acol", {})
    assert classify_system_profile(system) is SystemProfile.UNKNOWN


def test_sayc_requires_explicit_game_force_treatment():
    configured = SystemContext.from_mapping(
        "SAYC",
        {"two_over_one": "game_force"},
    )
    unspecified = SystemContext.from_mapping("SAYC", {})
    natural = SystemContext.from_mapping(
        "SAYC",
        {"two_over_one": "natural"},
    )

    assert supports_two_over_one_game_force(configured)
    assert not supports_two_over_one_game_force(unspecified)
    assert not supports_two_over_one_game_force(natural)


def test_two_over_one_profile_requires_explicit_game_force_treatment():
    configured = SystemContext.from_mapping(
        "TWO_OVER_ONE_GF",
        {"two_over_one": "game_force"},
    )
    unspecified = SystemContext.from_mapping("TWO_OVER_ONE_GF", {})
    natural = SystemContext.from_mapping(
        "TWO_OVER_ONE_GF",
        {"two_over_one": "natural"},
    )

    assert supports_two_over_one_game_force(configured)
    assert not supports_two_over_one_game_force(unspecified)
    assert not supports_two_over_one_game_force(natural)


def test_unrelated_system_never_gains_two_over_one_eligibility():
    system = SystemContext.from_mapping(
        "Acol",
        {"two_over_one": "game_force"},
    )
    assert not supports_two_over_one_game_force(system)


def test_profile_classification_requires_system_context():
    with pytest.raises(TypeError):
        classify_system_profile(None)


def test_two_over_one_eligibility_requires_system_context():
    with pytest.raises(TypeError):
        supports_two_over_one_game_force(None)
