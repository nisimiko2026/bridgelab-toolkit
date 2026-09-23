"""Phase 29T additive tests for Nisim–Nily exact six-card minor preempts."""

from dataclasses import FrozenInstanceError

import pytest

from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_opening_policy import build_nisim_nily_opening_policy
from bridge.nisim_nily_six_minor_preempt_policy import (
    SixMinorDecision,
    SixMinorQuality,
    assess_six_minor_three_level_preempt,
)


def _assess(hand: str, *, seat=Seat.NORTH, vul=Vulnerability.NONE, position=1):
    return assess_six_minor_three_level_preempt(
        Hand.parse(hand), seat=seat, vulnerability=vul, opening_position=position
    )


def test_phase29m_historical_snapshot_remains_unchanged():
    policy = build_nisim_nily_opening_policy()
    assert policy.policy_id == "nisim-nily.opening-policy"
    assert policy.version == "29M.1"


@pytest.mark.parametrize(
    ("hand", "quality"),
    (
        ("7.84.AQJT96.9742", SixMinorQuality.A_PLUS),
        ("7.84.AKJ986.9742", SixMinorQuality.A),
        ("7.84.KQT986.9742", SixMinorQuality.B_PLUS),
        ("7.84.QJT986.9742", SixMinorQuality.B),
        ("7.84.KJT986.9742", SixMinorQuality.C_PLUS),
        ("7.84.KQ9864.9742", SixMinorQuality.C),
        ("7.84.KJ9864.9742", SixMinorQuality.D),
    ),
)
def test_quality_ladder_is_deterministic(hand, quality):
    assert _assess(hand).quality is quality


def test_assessment_is_immutable_and_phase29t_versioned():
    result = _assess("7.84.KQJT96.9742", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3)
    assert result.policy_version == "nisim-nily.six-minor-preempt@29T.1"
    assert result.production_adopted is False
    with pytest.raises(FrozenInstanceError):
        result.preferred_call = "1D"


def test_approved_example_third_seat_favorable_opens_three_diamonds():
    result = _assess(
        "7.84.KQJT96.9742", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3
    )
    assert result.decision is SixMinorDecision.THREE_LEVEL
    assert result.preferred_call == "3D"


def test_rule20_has_priority_and_selects_one_level_minor():
    result = _assess("7.K4.KQJT96.A742")
    assert result.rule20_score >= 20
    assert result.decision is SixMinorDecision.ONE_LEVEL
    assert result.preferred_call == "1D"


def test_equal_vulnerability_first_seat_requires_b_plus_or_better():
    assert _assess("7.84.KQT986.9742").decision is SixMinorDecision.THREE_LEVEL
    assert _assess("7.84.QJT986.9742").decision is SixMinorDecision.NO_THREE_LEVEL


def test_second_seat_unfavorable_requires_a_plus():
    a = _assess("7.84.AKJ986.9742", seat=Seat.EAST, vul=Vulnerability.EW, position=2)
    a_plus = _assess("7.84.AQJT96.9742", seat=Seat.EAST, vul=Vulnerability.EW, position=2)
    assert a.quality is SixMinorQuality.A
    assert a.decision is SixMinorDecision.NO_THREE_LEVEL
    assert a_plus.quality is SixMinorQuality.A_PLUS
    assert a_plus.decision is SixMinorDecision.THREE_LEVEL


def test_third_seat_favorable_allows_good_c_but_not_plain_c():
    good_c = _assess("7.84.KJT986.9742", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3)
    plain_c = _assess("7.84.KQ9864.9742", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3)
    assert good_c.quality is SixMinorQuality.C_PLUS
    assert good_c.decision is SixMinorDecision.THREE_LEVEL
    assert plain_c.quality is SixMinorQuality.C
    assert plain_c.decision is SixMinorDecision.NO_THREE_LEVEL


def test_d_quality_never_opens_three_with_only_six():
    result = _assess("7.84.KJ9864.9742", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3)
    assert result.quality is SixMinorQuality.D
    assert result.decision is SixMinorDecision.NO_THREE_LEVEL


def test_four_card_major_raises_required_quality_one_step():
    result = _assess("8765.2.KJT986.43", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3)
    assert result.quality is SixMinorQuality.C_PLUS
    assert result.has_four_card_major
    assert result.required_score == 2
    assert result.decision is SixMinorDecision.NO_THREE_LEVEL


def test_significant_outside_defence_rejects_six_card_preempt():
    result = _assess("A7.K4.QJT986.742", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3)
    assert result.outside_hcp >= 7
    assert result.decision is SixMinorDecision.NO_THREE_LEVEL


def test_two_aces_reject_six_card_preempt_when_rule20_does_not_take_priority():
    result = _assess("A7.84.JT9864.A42", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3)
    assert result.rule20_score < 20
    assert result.total_aces == 2
    assert result.decision is SixMinorDecision.NO_THREE_LEVEL


def test_club_exception_selects_three_clubs():
    result = _assess("974.842.7.KQJT96", seat=Seat.SOUTH, vul=Vulnerability.EW, position=3)
    assert result.decision is SixMinorDecision.THREE_LEVEL
    assert result.preferred_call == "3C"


def test_fourth_seat_does_not_use_exact_six_card_preempt_exception():
    result = _assess("7.84.KQJT96.9742", seat=Seat.WEST, vul=Vulnerability.NONE, position=4)
    assert result.decision is SixMinorDecision.NO_THREE_LEVEL


def test_six_five_and_seven_card_shapes_stay_outside_exact_exception():
    six_five = _assess("7.8.KQJT96.QJT98")
    seven = _assess("7.84.KQJT976.974")
    assert six_five.decision is SixMinorDecision.NOT_APPLICABLE
    assert seven.decision is SixMinorDecision.NOT_APPLICABLE


def test_invalid_opening_position_is_rejected():
    with pytest.raises(ValueError, match="1..4"):
        _assess("7.84.KQJT96.9742", position=5)
