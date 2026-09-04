import pytest

from bridge import (
    Auction,
    BiddingContext,
    Hand,
    KnowledgeSource,
    PlayingStrengthAssessment,
    PlayingStrengthStatus,
    PolicyRegistry,
    Seat,
    SystemContext,
    Vulnerability,
)
from bridge.policy_registry import (
    PLAYING_STRENGTH_POLICY_OPTION,
    assess_configured_playing_strength,
    configured_playing_strength_policy_id,
    resolve_playing_strength_policy,
)

SOURCE = KnowledgeSource("bidding/systems/sayc", "Natural Overcalls")


class FixturePolicy:
    def __init__(self, policy_id="fixture", status=PlayingStrengthStatus.QUALIFIES):
        self.policy_id = policy_id
        self.status = status

    def assess(self, ctx):
        if self.status is PlayingStrengthStatus.UNKNOWN:
            return PlayingStrengthAssessment.unknown(self.policy_id)
        if self.status is PlayingStrengthStatus.QUALIFIES:
            return PlayingStrengthAssessment.qualifies(
                self.policy_id, "fixture qualifies", (SOURCE,)
            )
        return PlayingStrengthAssessment.does_not_qualify(
            self.policy_id, "fixture rejects", (SOURCE,)
        )


def context(policy=None):
    options = {} if policy is None else {PLAYING_STRENGTH_POLICY_OPTION: policy}
    return BiddingContext.create(
        hand=Hand.parse("AKQ97.J82.64.532"),
        auction=Auction(Seat.NORTH, ("1D",)),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", options),
    )


def test_registry_orders_ids():
    r = PolicyRegistry.from_playing_strength_policies(
        [FixturePolicy("zeta"), FixturePolicy("Alpha")]
    )
    assert r.playing_strength_policy_ids == ("Alpha", "zeta")


def test_registry_rejects_duplicate_ids_case_insensitive():
    with pytest.raises(ValueError):
        PolicyRegistry.from_playing_strength_policies(
            [FixturePolicy("One"), FixturePolicy("one")]
        )


def test_lookup_is_case_insensitive():
    p = FixturePolicy("Partnership.Strength")
    r = PolicyRegistry.from_playing_strength_policies([p])
    assert r.playing_strength_policy("partnership.strength") is p


def test_configured_id_and_resolver():
    p = FixturePolicy("fixture")
    r = PolicyRegistry.from_playing_strength_policies([p])
    assert configured_playing_strength_policy_id(context("fixture").system) == "fixture"
    assert resolve_playing_strength_policy(context("fixture").system, r) is p


def test_missing_configuration_or_registry_returns_none():
    p = FixturePolicy("fixture")
    r = PolicyRegistry.from_playing_strength_policies([p])
    assert assess_configured_playing_strength(context(), r) is None
    assert assess_configured_playing_strength(context("fixture"), PolicyRegistry()) is None


def test_configured_assessment_runs_policy():
    p = FixturePolicy("fixture", PlayingStrengthStatus.QUALIFIES)
    r = PolicyRegistry.from_playing_strength_policies([p])
    result = assess_configured_playing_strength(context("fixture"), r)
    assert result is not None
    assert result.status is PlayingStrengthStatus.QUALIFIES


def test_from_policies_combines_all_three_policy_roles():
    p = FixturePolicy("strength")
    r = PolicyRegistry.from_policies(playing_strength_policies=[p])
    assert r.playing_strength_policy_ids == ("strength",)


def test_no_default_policy_is_inferred():
    assert configured_playing_strength_policy_id(context().system) is None
    assert PolicyRegistry().playing_strength_policy_ids == ()
