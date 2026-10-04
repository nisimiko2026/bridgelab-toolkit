"""B2.4B5 opt-in Nisim-Nily major-raise continuations.

The approved continuation API remains separate from production routing.
Qualitative judgments require explicit RaiseEvidence.
"""

import pytest

from bridge.auction import Auction, Call
from bridge.models import Hand, Seat, Suit, Vulnerability
from bridge.nisim_nily_major_raise_continuations import (
    APPROVAL,
    RaiseCriterion,
    RaiseEvidence,
    RaiseIntent,
    assess_major_raise_opener,
)
from bridge.nisim_nily_partnership_profile import (
    NISIM_NILY_BERGEN_PROFILE,
    NISIM_NILY_MAJOR_RAISE_PROFILE,
)
from bridge.opener_rebid import (
    OpenerRebidDisposition,
    assess_opener_rebid,
)
from bridge.sayc_route_configuration import create_standard_sayc_router


PROFILE = NISIM_NILY_MAJOR_RAISE_PROFILE


def hand(text):
    return Hand.parse(text)


def auction(*calls):
    return Auction(Seat.NORTH, calls)


def sourced_evidence(
    intent,
    cards,
    calls,
    *,
    criteria=frozenset(),
    call=None,
    explanation="explicit approved direction",
):
    h = hand(cards)
    a = auction(*calls)

    return RaiseEvidence(
        intent=intent,
        hand=h,
        auction=a,
        explanation=explanation,
        sources=(APPROVAL,),
        criteria=criteria,
        call=call,
    )


def assess_opener(
    cards,
    calls,
    *,
    intent=None,
    trials=(),
    profile=PROFILE,
):
    return assess_major_raise_opener(
        hand(cards),
        auction=auction(*calls),
        vulnerability=Vulnerability.NONE,
        profile=profile,
        intent=intent,
        trials=trials,
    )


def selected(result):
    if result.recommended_call is None:
        return None
    return result.recommended_call.serialize()


def test_profile_is_explicit_opt_in_over_finalized_bergen():
    assert PROFILE.version == "B2.4B5"
    assert PROFILE.base_system is NISIM_NILY_BERGEN_PROFILE.base_system

    bergen_b3 = next(
        agreement
        for agreement in NISIM_NILY_BERGEN_PROFILE.agreements
        if agreement.family == "response.major.raises"
    )

    bergen_b5 = next(
        agreement
        for agreement in PROFILE.agreements
        if agreement.family == "response.major.raises"
    )

    continuation = next(
        agreement
        for agreement in PROFILE.agreements
        if agreement.family == "opener.major.raises"
    )

    assert bergen_b5 == bergen_b3

    assert (
        continuation.treatment_id
        == "nisim_nily_major_raise_continuations"
    )

    assert continuation.option("competition") == "UNCONTESTED_ONLY"
    assert continuation.option("shortness_after_hearts") == "2S"
    assert continuation.option("shortness_after_spades") == "2NT"


@pytest.mark.parametrize(
    "opening,cards,expected",
    [
        (
            "1H",
            "AK2.AKQJ53.7.K87",
            "2S",
        ),
        (
            "1S",
            "AKQJ53.AK2.7.K87",
            "2NT",
        ),
    ],
)
def test_shortness_trial_uses_approved_artificial_call(
    opening,
    cards,
    expected,
):
    calls = (
        opening,
        "P",
        "2" + opening[-1],
        "P",
    )

    intent = sourced_evidence(
        RaiseIntent.SHORTNESS_TRIAL,
        cards,
        calls,
        criteria=frozenset(
            {
                RaiseCriterion.SUITABLE_TRIAL,
            }
        ),
    )

    result = assess_opener(
        cards,
        calls,
        intent=intent,
    )

    assert selected(result) == expected
    assert result.meaning is not None
    assert result.meaning.kind == "shortness_trial"
    assert result.meaning.artificial is True
    assert result.production_adopted is False


def test_missing_qualitative_direction_abstains():
    cards = "AKQJ53.AK2.76.K7"
    calls = (
        "1S",
        "P",
        "2S",
        "P",
    )

    result = assess_opener(
        cards,
        calls,
    )

    assert selected(result) is None
    assert result.selected is None
    assert result.meaning is None
    assert result.blockers
    assert result.production_adopted is False


def test_help_suit_trial_requires_explicit_call_and_evidence():
    cards = "AKQJ53.AK2.76.K7"
    calls = (
        "1S",
        "P",
        "2S",
        "P",
    )

    intent = sourced_evidence(
        RaiseIntent.HELP_SUIT_TRIAL,
        cards,
        calls,
        criteria=frozenset(
            {
                RaiseCriterion.SUITABLE_TRIAL,
            }
        ),
        call=Call.parse("3H"),
    )

    result = assess_opener(
        cards,
        calls,
        intent=intent,
    )

    assert selected(result) == "3H"
    assert result.meaning is not None
    assert result.meaning.kind == "help_suit_trial"
    assert result.meaning.trial_suit is Suit.HEARTS
    assert result.production_adopted is False


def test_multiple_suitable_trials_abstain_without_suit_choice():
    cards = "AKQJ53.AK2.76.K7"
    calls = (
        "1S",
        "P",
        "2S",
        "P",
    )

    heart = sourced_evidence(
        RaiseIntent.HELP_SUIT_TRIAL,
        cards,
        calls,
        criteria=frozenset(
            {
                RaiseCriterion.SUITABLE_TRIAL,
            }
        ),
        call=Call.parse("3H"),
    )

    diamond = sourced_evidence(
        RaiseIntent.HELP_SUIT_TRIAL,
        cards,
        calls,
        criteria=frozenset(
            {
                RaiseCriterion.SUITABLE_TRIAL,
            }
        ),
        call=Call.parse("3D"),
    )

    result = assess_opener(
        cards,
        calls,
        trials=(
            heart,
            diamond,
        ),
    )

    assert selected(result) is None
    assert result.selected is None
    assert result.meaning is None

    assert any(
        "Multiple suitable trials" in blocker
        for blocker in result.blockers
    )


def test_direct_weak_raise_pass_requires_explicit_not_very_strong_evidence():
    cards = "AQ853.K82.976.A7"
    calls = (
        "1S",
        "P",
        "3S",
        "P",
    )

    intent = sourced_evidence(
        RaiseIntent.PASS,
        cards,
        calls,
        criteria=frozenset(
            {
                RaiseCriterion.NOT_VERY_STRONG,
            }
        ),
    )

    result = assess_opener(
        cards,
        calls,
        intent=intent,
    )

    assert selected(result) == "P"
    assert result.meaning is not None
    assert result.meaning.kind == "weak_raise_pass"
    assert result.meaning.signoff is True
    assert result.production_adopted is False


def test_bergen_minimum_signoff_requires_explicit_minimum_evidence():
    cards = "AQ853.K82.976.A7"
    calls = (
        "1S",
        "P",
        "3C",
        "P",
    )

    intent = sourced_evidence(
        RaiseIntent.MINIMUM_SIGNOFF,
        cards,
        calls,
        criteria=frozenset(
            {
                RaiseCriterion.MINIMUM,
            }
        ),
    )

    result = assess_opener(
        cards,
        calls,
        intent=intent,
    )

    assert selected(result) == "3S"
    assert result.meaning is not None
    assert result.meaning.kind == "minimum_signoff"
    assert result.meaning.signoff is True
    assert result.production_adopted is False


def test_evidence_for_different_auction_is_rejected():
    cards = "AKQJ53.AK2.76.K7"

    intent = sourced_evidence(
        RaiseIntent.PASS,
        cards,
        (
            "1S",
            "P",
            "3S",
            "P",
        ),
        criteria=frozenset(
            {
                RaiseCriterion.NOT_VERY_STRONG,
            }
        ),
    )

    with pytest.raises(
        ValueError,
        match="different hand or auction",
    ):
        assess_opener(
            cards,
            (
                "1S",
                "P",
                "2S",
                "P",
            ),
            intent=intent,
        )


def test_finalized_b3_profile_alone_cannot_activate_b5():
    cards = "AKQJ53.AK2.76.K7"
    calls = (
        "1S",
        "P",
        "2S",
        "P",
    )

    result = assess_opener(
        cards,
        calls,
        profile=NISIM_NILY_BERGEN_PROFILE,
    )

    assert selected(result) is None
    assert result.selected is None

    assert any(
        "B2.4B5" in blocker
        for blocker in result.blockers
    )


def test_production_opener_rebid_remains_unwired():
    cards = hand("AKQJ53.AK2.76.K7")

    result = assess_opener_rebid(
        cards,
        auction=auction(
            "1S",
            "P",
            "2S",
            "P",
        ),
        vulnerability=Vulnerability.NONE,
        profile=PROFILE,
    )

    assert result.disposition is OpenerRebidDisposition.ABSTAIN
    assert result.selected is None
    assert result.production_adopted is False


def test_standard_router_inventory_remains_45():
    routes = create_standard_sayc_router().routes

    assert len(routes) == 47

    assert not any(
        "bergen" in route.route_id.casefold()
        for route in routes
    )
