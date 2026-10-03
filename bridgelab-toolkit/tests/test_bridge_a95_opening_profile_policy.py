from bridge.models import Hand
from bridge.opening_profile_policy import (
    OpeningProfile, OpeningPolicyStatus, evaluate_two_suited_opening,
)


def d(hand, profile, seat=1):
    return evaluate_two_suited_opening(Hand.parse(hand), profile=profile, seat_number=seat)


def test_sayc_above_10_equal_majors_opens_spade():
    x = d("AKJT7.AKJ74.A54.-", OpeningProfile.SAYC)
    assert (x.status, x.call) == (OpeningPolicyStatus.OPEN, "1S")


def test_sayc_above_10_equal_minors_opens_diamond():
    x = d("2.AT.AQT86.KJ973", OpeningProfile.SAYC)
    assert (x.status, x.call) == (OpeningPolicyStatus.OPEN, "1D")


def test_sayc_rule20_at_10_opens():
    x = d("KQJ98.AT876.32.4", OpeningProfile.SAYC)
    assert x.rule20_score >= 20
    assert x.call == "1S"


def test_nisim_above_10_does_not_need_rule20():
    x = d("Q3.K.J7652.KQJ43", OpeningProfile.NISIM_NILY)
    assert x.hcp > 10 and x.call == "1D"


def test_nisim_under_10_spade_minor_is_2s():
    # 8 HCP: KQJ in spades + Q in diamonds.
    x = d("KQJ98.4.QT876.32", OpeningProfile.NISIM_NILY)
    assert x.hcp == 8 and x.call == "2S"


def test_nisim_under_10_heart_minor_is_2h():
    # 8 HCP: KQJ in hearts + Q in diamonds.
    x = d("4.KQJ98.QT876.32", OpeningProfile.NISIM_NILY)
    assert x.hcp == 8 and x.call == "2H"


def test_nisim_under_10_two_minors_is_2nt():
    # 8 HCP: KQJ in diamonds + Q in clubs.
    x = d("43.2.KQJ98.QT876", OpeningProfile.NISIM_NILY)
    assert x.hcp == 8 and x.call == "2NT"


def test_seed1534_shape_qualifies_late_exception():
    x = d("T9843.AKJ32.7.65", OpeningProfile.SAYC, seat=3)
    assert x.call == "1S"


def test_seed4949_shape_qualifies_late_exception():
    x = d("AQ987.QJ974.-.862", OpeningProfile.NISIM_NILY, seat=4)
    assert x.call == "1S"


def test_seed9577_shape_qualifies_late_exception():
    x = d("AK632.JT865.J.T6", OpeningProfile.SAYC, seat=3)
    assert x.call == "1S"


def test_nonqualifying_major_concentration_does_not_get_exception():
    x = d("JT753.K9742.6.AT", OpeningProfile.NISIM_NILY, seat=3)
    assert x.call is None and x.status is OpeningPolicyStatus.PASS


def test_exception_not_available_first_seat():
    x = d("T9843.AKJ32.7.65", OpeningProfile.NISIM_NILY, seat=1)
    assert x.call is None


def test_exception_not_available_second_seat():
    x = d("AQ987.QJ974.-.862", OpeningProfile.SAYC, seat=2)
    assert x.call is None


def test_out_of_scope_shape_is_not_changed():
    x = d("AKQJ.AT98.765.32", OpeningProfile.SAYC)
    assert x.status is OpeningPolicyStatus.OUT_OF_SCOPE


def test_invalid_seat_rejected():
    try:
        d("T9843.AKJ32.7.65", OpeningProfile.SAYC, seat=5)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
