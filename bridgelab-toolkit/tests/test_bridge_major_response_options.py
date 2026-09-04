import pytest

from bridge import SystemContext
from bridge.major_response_options import (
    ForcingOneNotrumpTreatment,
    MajorRaiseStyle,
    TwoOverOneTreatment,
    forcing_one_notrump_treatment,
    major_raise_style,
    two_over_one_treatment,
)


def system(options=None):
    return SystemContext.from_mapping("SAYC", options or {})


def test_major_raise_defaults_to_traditional():
    assert major_raise_style(system()) is MajorRaiseStyle.TRADITIONAL


def test_major_raise_traditional():
    assert major_raise_style(system({"major_raise_style": "traditional"})) is MajorRaiseStyle.TRADITIONAL


def test_major_raise_bergen():
    assert major_raise_style(system({"major_raise_style": "bergen"})) is MajorRaiseStyle.BERGEN


def test_major_raise_unknown_is_other():
    assert major_raise_style(system({"major_raise_style": "custom"})) is MajorRaiseStyle.OTHER


def test_forcing_one_nt_unspecified_by_default():
    assert forcing_one_notrump_treatment(system()) is ForcingOneNotrumpTreatment.UNSPECIFIED


def test_forcing_one_nt_boolean_true():
    assert forcing_one_notrump_treatment(system({"forcing_one_notrump": True})) is ForcingOneNotrumpTreatment.FORCING


def test_forcing_one_nt_boolean_false():
    assert forcing_one_notrump_treatment(system({"forcing_one_notrump": False})) is ForcingOneNotrumpTreatment.NONFORCING


def test_forcing_one_nt_string_forcing():
    assert forcing_one_notrump_treatment(system({"forcing_one_notrump": "forcing"})) is ForcingOneNotrumpTreatment.FORCING


def test_forcing_one_nt_string_nonforcing():
    assert forcing_one_notrump_treatment(system({"forcing_one_notrump": "non-forcing"})) is ForcingOneNotrumpTreatment.NONFORCING


def test_forcing_one_nt_unknown_string_stays_unspecified():
    assert forcing_one_notrump_treatment(system({"forcing_one_notrump": "maybe"})) is ForcingOneNotrumpTreatment.UNSPECIFIED


def test_two_over_one_unspecified_by_default():
    assert two_over_one_treatment(system()) is TwoOverOneTreatment.UNSPECIFIED


def test_two_over_one_boolean_true():
    assert two_over_one_treatment(system({"two_over_one": True})) is TwoOverOneTreatment.GAME_FORCE


def test_two_over_one_boolean_false():
    assert two_over_one_treatment(system({"two_over_one": False})) is TwoOverOneTreatment.NATURAL


def test_two_over_one_explicit_game_force():
    assert two_over_one_treatment(system({"two_over_one": "2/1 game force"})) is TwoOverOneTreatment.GAME_FORCE


def test_two_over_one_explicit_natural():
    assert two_over_one_treatment(system({"two_over_one": "natural"})) is TwoOverOneTreatment.NATURAL


def test_two_over_one_unknown_string_stays_unspecified():
    assert two_over_one_treatment(system({"two_over_one": "custom"})) is TwoOverOneTreatment.UNSPECIFIED


@pytest.mark.parametrize(
    "fn",
    [major_raise_style, forcing_one_notrump_treatment, two_over_one_treatment],
)
def test_option_readers_require_system_context(fn):
    with pytest.raises(TypeError):
        fn(None)
