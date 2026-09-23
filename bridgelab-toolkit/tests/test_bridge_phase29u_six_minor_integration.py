"""Phase 29U tests for additive six-card-minor integration."""
from dataclasses import FrozenInstanceError

import pytest

from bridge.auction import Auction
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_six_minor_preempt_policy import SixMinorDecision
from bridge.opening_policy_consolidation_audit import (
    Classification,
    assess_opening_policy,
)
from bridge.opening_policy_six_minor_integration_audit import (
    assess_opening_policy_with_six_minor,
)


def _auction(position: int) -> Auction:
    if position not in (1, 2, 3, 4):
        raise ValueError("position must be 1..4")
    return Auction(Seat.NORTH, ("P",) * (position - 1))


def _assess(hand: str, *, position=1, vul=Vulnerability.NONE):
    return assess_opening_policy_with_six_minor(
        Hand.parse(hand),
        auction=_auction(position),
        vulnerability=vul,
    )


def test_phase29s_historical_assessment_is_not_modified():
    hand = Hand.parse("7.84.KQJT96.9742")
    auction = _auction(3)
    before = assess_opening_policy(hand, auction=auction, vulnerability=Vulnerability.EW)
    result = assess_opening_policy_with_six_minor(
        hand, auction=auction, vulnerability=Vulnerability.EW
    )
    after = assess_opening_policy(hand, auction=auction, vulnerability=Vulnerability.EW)
    assert before == after == result.base
    assert result.base.production_adopted is False


def test_approved_third_seat_favorable_six_diamond_becomes_3d():
    result = _assess("7.84.KQJT96.9742", position=3, vul=Vulnerability.EW)
    assert result.base.classification is Classification.UNRESOLVED
    assert result.six_minor.decision is SixMinorDecision.THREE_LEVEL
    assert result.classification is Classification.PARTNERSHIP_TREATMENT_SUPPORTED
    assert result.supported_call == "3D"
    assert result.unresolved_blockers == ()


def test_approved_third_seat_favorable_six_club_becomes_3c():
    result = _assess("974.842.7.KQJT96", position=3, vul=Vulnerability.EW)
    assert result.six_minor.decision is SixMinorDecision.THREE_LEVEL
    assert result.classification is Classification.PARTNERSHIP_TREATMENT_SUPPORTED
    assert result.supported_call == "3C"


def test_rule20_priority_refines_to_one_diamond():
    result = _assess("7.K4.KQJT96.A742")
    assert result.six_minor.decision is SixMinorDecision.ONE_LEVEL
    assert result.classification is Classification.OPENING_SUPPORTED
    assert result.supported_call == "1D"


def test_rule20_priority_refines_to_one_club():
    result = _assess("7.K4.A742.KQJT96")
    assert result.six_minor.decision is SixMinorDecision.ONE_LEVEL
    assert result.classification is Classification.OPENING_SUPPORTED
    assert result.supported_call == "1C"


def test_no_three_level_does_not_invent_pass():
    result = _assess("7.84.KJ9864.9742", position=3, vul=Vulnerability.EW)
    assert result.six_minor.decision is SixMinorDecision.NO_THREE_LEVEL
    assert result.classification is result.base.classification
    assert result.supported_call == result.base.supported_call
    assert result.unresolved_blockers == result.base.unresolved_blockers
    assert result.supported_call != "P"


def test_fourth_seat_rejection_preserves_phase29s():
    result = _assess("7.84.KQJT96.9742", position=4)
    assert result.six_minor.decision is SixMinorDecision.NO_THREE_LEVEL
    assert result.classification is result.base.classification
    assert result.supported_call == result.base.supported_call


def test_seven_card_minor_is_not_applicable_and_preserves_29s():
    result = _assess("7.84.KQJT976.974")
    assert result.six_minor.decision is SixMinorDecision.NOT_APPLICABLE
    assert not result.integration_applied
    assert result.classification is result.base.classification
    assert result.supported_call == result.base.supported_call


def test_six_five_shape_is_not_applicable_and_preserves_29s():
    result = _assess("7.8.KQJT96.QJT98")
    assert result.six_minor.decision is SixMinorDecision.NOT_APPLICABLE
    assert not result.integration_applied
    assert result.classification is result.base.classification


def test_result_is_immutable_versioned_and_not_production_adopted():
    result = _assess("7.84.KQJT96.9742", position=3, vul=Vulnerability.EW)
    assert result.policy_version == "nisim-nily.opening-policy-six-minor@29U.1"
    assert result.production_adopted is False
    with pytest.raises(FrozenInstanceError):
        result.supported_call = "1D"


def test_serialization_is_deterministic():
    first = _assess("7.84.KQJT96.9742", position=3, vul=Vulnerability.EW)
    second = _assess("7.84.KQJT96.9742", position=3, vul=Vulnerability.EW)
    assert first.to_json() == second.to_json()
    assert first.to_dict()["supported_call"] == "3D"


def test_invalid_types_are_rejected():
    with pytest.raises(TypeError, match="Auction"):
        assess_opening_policy_with_six_minor(
            Hand.parse("7.84.KQJT96.9742"),
            auction=None,
            vulnerability=Vulnerability.NONE,
        )
    with pytest.raises(TypeError, match="Vulnerability"):
        assess_opening_policy_with_six_minor(
            Hand.parse("7.84.KQJT96.9742"),
            auction=_auction(1),
            vulnerability=None,
        )
