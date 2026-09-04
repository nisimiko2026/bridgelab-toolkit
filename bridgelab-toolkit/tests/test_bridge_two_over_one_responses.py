import pytest

from bridge import (
    Auction, BiddingContext, Hand, KnowledgeSource, PolicyRegistry, Seat, Suit,
    SuitQualityAssessment, SuitQualityStatus, SystemContext, Vulnerability,
)
from bridge.two_over_one_responses import create_sayc_two_over_one_response_engine


POLICY_SOURCE = KnowledgeSource("bidding/systems/2-over-1", "Hands Suitable for a 2/1 Response")


class FixtureQualityPolicy:
    policy_id = "fixture.quality"

    def __init__(self, status=SuitQualityStatus.QUALIFIES):
        self.status = status

    def assess(self, context, suit):
        evidence = context.evaluation.quality_evidence(suit)
        if self.status is SuitQualityStatus.UNKNOWN:
            return SuitQualityAssessment.unknown(self.policy_id, suit, evidence)
        if self.status is SuitQualityStatus.DOES_NOT_QUALIFY:
            return SuitQualityAssessment.does_not_qualify(
                self.policy_id, suit, evidence, "fixture rejects", (POLICY_SOURCE,)
            )
        return SuitQualityAssessment.qualifies(
            self.policy_id, suit, evidence, "fixture qualifies", (POLICY_SOURCE,)
        )


def registry(status=SuitQualityStatus.QUALIFIES):
    return PolicyRegistry.from_suit_quality_policies([FixtureQualityPolicy(status)])


def context(opening, hand, *, two_over_one="game_force", quality="fixture.quality", system="SAYC", calls=None):
    options = {"two_over_one": two_over_one}
    if quality is not None:
        options["suit_quality_policy"] = quality
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls or (opening, "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system, options),
    )


@pytest.mark.parametrize(
    "opening, hand, expected",
    [
        ("1H", "KQ3.82.64.AKQJ97", "2C"),
        ("1H", "KQ3.82.AKQJ97.64", "2D"),
        ("1S", "82.KQ3.64.AKQJ97", "2C"),
        ("1S", "82.KQ3.AKQJ97.64", "2D"),
    ],
)
def test_four_controlled_two_over_one_responses(opening, hand, expected):
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context(opening, hand)
    )
    assert result.recommended_call.serialize() == expected
    assert "fixture.quality" in result.recommended.explanation


def test_requires_explicit_game_force_treatment():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1H", "KQ3.82.64.AKQJ97", two_over_one="natural")
    )
    assert not result.has_recommendation


def test_requires_configured_quality_policy():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1H", "KQ3.82.64.AKQJ97", quality=None)
    )
    assert not result.has_recommendation


def test_unknown_quality_abstains():
    result = create_sayc_two_over_one_response_engine(
        registry(SuitQualityStatus.UNKNOWN)
    ).evaluate(context("1H", "KQ3.82.64.AKQJ97"))
    assert not result.has_recommendation


def test_rejected_quality_abstains():
    result = create_sayc_two_over_one_response_engine(
        registry(SuitQualityStatus.DOES_NOT_QUALIFY)
    ).evaluate(context("1H", "KQ3.82.64.AKQJ97"))
    assert not result.has_recommendation


def test_below_12_hcp_abstains_even_if_policy_qualifies():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1H", "Q83.82.64.KQJ987")
    )
    assert not result.has_recommendation


def test_three_card_support_blocks_minor_response():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1H", "KQ3.J82.6.AKQJ97")
    )
    assert not result.has_recommendation


def test_four_spades_after_one_heart_has_priority():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1H", "KQ83.82.6.AKQJ97")
    )
    assert not result.has_recommendation


def test_selected_minor_must_have_five_cards():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1S", "82.AKQ.KQJ9.AQJ3")
    )
    assert not result.has_recommendation


def test_equal_five_card_minors_are_left_unresolved():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1S", "82.A.AT987.KQJ98")
    )
    assert not result.has_recommendation


def test_longer_minor_wins():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1S", "82.AK.AKQJ98.Q98")
    )
    assert result.recommended_call.serialize() == "2D"


def test_non_sayc_abstains():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1S", "82.KQ3.64.AKQJ97", system="Acol")
    )
    assert not result.has_recommendation


def test_interference_abstains():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1S", "82.KQ3.64.AKQJ97", calls=("1S", "2H"))
    )
    assert not result.has_recommendation


def test_source_trace_includes_quality_policy_source():
    result = create_sayc_two_over_one_response_engine(registry()).evaluate(
        context("1H", "KQ3.82.64.AKQJ97")
    )
    assert result.recommended is not None
    headings = {source.heading for source in result.recommended.sources}
    assert "Two-over-One Game Force" in headings
    assert "Hands Suitable for a 2/1 Response" in headings


def test_registry_type_validation():
    with pytest.raises(TypeError):
        create_sayc_two_over_one_response_engine(None)
