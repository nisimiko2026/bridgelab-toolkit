import inspect

import pytest

from benchmarks.stayman_gamegoing_audit import StaymanGameGoingAuditFixture
from bridge import Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability
from bridge.policy_registry import (
    STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION,
    PolicyRegistry,
)
from bridge.sayc_1nt_stayman_continuations import (
    create_sayc_one_notrump_stayman_major_fit_game_continuation_engine,
)
from bridge.stayman_continuation_strength_policy import (
    StaymanContinuationStrength,
    StaymanContinuationStrengthAssessment,
)


class FixedPolicy:
    def __init__(self, classification):
        self.policy_id = f"fixture.stayman.{classification.value}"
        self.classification = classification

    def assess(self, context):
        if self.classification is StaymanContinuationStrength.UNKNOWN:
            return StaymanContinuationStrengthAssessment(self.policy_id, self.classification)
        fixture = StaymanGameGoingAuditFixture(self.policy_id)
        result = fixture.assess(context)
        if self.classification is StaymanContinuationStrength.GAME_GOING:
            return result
        return StaymanContinuationStrengthAssessment(
            self.policy_id,
            self.classification,
            result.explanation,
            result.sources,
        )


def context(hand, opener_response, policy_id=None):
    options = (
        {}
        if policy_id is None
        else {STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION: policy_id}
    )
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(
            Seat.NORTH, ("1NT", "P", "2C", "P", opener_response, "P")
        ),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", options),
    )


def evaluate(hand, opener_response, classification=None, registered=True):
    if classification is None:
        registry, policy_id = PolicyRegistry(), None
    else:
        policy = FixedPolicy(classification)
        registry = (
            PolicyRegistry.from_stayman_continuation_strength_policies((policy,))
            if registered
            else PolicyRegistry()
        )
        policy_id = policy.policy_id
    engine = create_sayc_one_notrump_stayman_major_fit_game_continuation_engine(
        registry
    )
    return engine.evaluate(context(hand, opener_response, policy_id)).recommended_call


def serialized(*args, **kwargs):
    call = evaluate(*args, **kwargs)
    return None if call is None else call.serialize()


def test_missing_and_unresolvable_policy_abstain():
    assert serialized("432.AKQJ.T98.765", "2H") is None
    assert serialized(
        "432.AKQJ.T98.765",
        "2H",
        StaymanContinuationStrength.GAME_GOING,
        registered=False,
    ) is None


@pytest.mark.parametrize(
    "classification",
    (StaymanContinuationStrength.UNKNOWN, StaymanContinuationStrength.OTHER),
)
def test_non_gamegoing_classifications_abstain(classification):
    assert serialized("432.AKQJ.T98.765", "2H", classification) is None


@pytest.mark.parametrize("hand", ("432.AKQJ.T98.765", "32.AKQJT.987.654"))
def test_gamegoing_heart_fit_bids_four_hearts(hand):
    assert serialized(hand, "2H", StaymanContinuationStrength.GAME_GOING) == "4H"


@pytest.mark.parametrize("hand", ("AKQJT.432.T98.76", "AKQJT.32.987.654"))
def test_gamegoing_other_major_does_not_replace_heart_fit(hand):
    assert serialized(hand, "2H", StaymanContinuationStrength.GAME_GOING) is None


@pytest.mark.parametrize("hand", ("AKQJ.432.T98.765", "AKQJT.32.987.654"))
def test_gamegoing_spade_fit_bids_four_spades(hand):
    assert serialized(hand, "2S", StaymanContinuationStrength.GAME_GOING) == "4S"


@pytest.mark.parametrize("hand", ("432.AKQJT.T98.76", "32.AKQJT.987.654"))
def test_gamegoing_other_major_does_not_replace_spade_fit(hand):
    assert serialized(hand, "2S", StaymanContinuationStrength.GAME_GOING) is None


def test_rule_contains_no_strength_or_hcp_classifier():
    module = __import__("bridge.sayc_1nt_stayman_continuations", fromlist=["unused"])
    source = inspect.getsource(module).casefold()
    assert "high_card_points" not in source
    assert "hcp" not in source
    assert "total_points" not in source

