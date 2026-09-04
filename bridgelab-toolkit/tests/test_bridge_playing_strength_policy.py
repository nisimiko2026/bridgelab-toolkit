import pytest

from bridge import (
    Auction,
    BiddingContext,
    Hand,
    KnowledgeSource,
    PlayingStrengthAssessment,
    PlayingStrengthStatus,
    Seat,
    SystemContext,
    Vulnerability,
    assess_playing_strength,
)

SOURCE = KnowledgeSource("bidding/systems/sayc", "Natural Overcalls")


def context():
    return BiddingContext.create(
        hand=Hand.parse("AKQ97.J82.64.532"),
        auction=Auction(Seat.NORTH, ("1D",)),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("SAYC"),
    )


class FixturePolicy:
    policy_id = "fixture.playing-strength"

    def __init__(self, status=PlayingStrengthStatus.QUALIFIES):
        self.status = status

    def assess(self, ctx):
        if self.status is PlayingStrengthStatus.UNKNOWN:
            return PlayingStrengthAssessment.unknown(self.policy_id)
        if self.status is PlayingStrengthStatus.QUALIFIES:
            return PlayingStrengthAssessment.qualifies(
                self.policy_id, "Fixture qualifies.", (SOURCE,)
            )
        return PlayingStrengthAssessment.does_not_qualify(
            self.policy_id, "Fixture rejects.", (SOURCE,)
        )


def test_qualifies_assessment():
    result = assess_playing_strength(FixturePolicy(), context())
    assert result.status is PlayingStrengthStatus.QUALIFIES
    assert result.qualifies_strength is True
    assert result.is_known


def test_does_not_qualify_assessment():
    result = assess_playing_strength(
        FixturePolicy(PlayingStrengthStatus.DOES_NOT_QUALIFY), context()
    )
    assert result.qualifies_strength is False


def test_unknown_assessment():
    result = assess_playing_strength(
        FixturePolicy(PlayingStrengthStatus.UNKNOWN), context()
    )
    assert result.qualifies_strength is None
    assert not result.is_known


def test_known_outcome_requires_explanation():
    with pytest.raises(ValueError):
        PlayingStrengthAssessment.qualifies("x", "", (SOURCE,))


def test_known_outcome_requires_source():
    with pytest.raises(ValueError):
        PlayingStrengthAssessment.qualifies("x", "yes", ())


def test_unknown_can_be_unsourced():
    result = PlayingStrengthAssessment.unknown("x")
    assert result.status is PlayingStrengthStatus.UNKNOWN


def test_runner_rejects_wrong_policy_id():
    class BadPolicy(FixturePolicy):
        def assess(self, ctx):
            return PlayingStrengthAssessment.qualifies(
                "different", "bad", (SOURCE,)
            )
    with pytest.raises(ValueError):
        assess_playing_strength(BadPolicy(), context())


def test_runner_rejects_wrong_return_type():
    class BadReturn:
        policy_id = "bad"
        def assess(self, ctx):
            return True
    with pytest.raises(TypeError):
        assess_playing_strength(BadReturn(), context())


def test_blank_policy_id_rejected():
    class Blank:
        policy_id = " "
        def assess(self, ctx):
            raise AssertionError
    with pytest.raises(ValueError):
        assess_playing_strength(Blank(), context())


def test_context_type_validation():
    with pytest.raises(TypeError):
        assess_playing_strength(FixturePolicy(), None)


def test_no_production_playing_strength_formula_shipped():
    import bridge.playing_strength_policy as module
    production_classes = [
        name for name in vars(module)
        if name.endswith("Policy") and name != "PlayingStrengthPolicy"
    ]
    assert production_classes == []
