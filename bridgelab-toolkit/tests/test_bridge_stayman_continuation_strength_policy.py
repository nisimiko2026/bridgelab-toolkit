import inspect

import pytest

from benchmarks.stayman_gamegoing_audit import StaymanGameGoingAuditFixture
from benchmarks.stayman_continuation_policy_architecture import (
    run_stayman_policy_architecture_validation,
)
from bridge import (
    Auction,
    BiddingContext,
    Hand,
    KnowledgeSource,
    Seat,
    StaymanContinuationStrength,
    StaymanContinuationStrengthAssessment,
    SystemContext,
    Vulnerability,
)
from bridge.policy_registry import (
    STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION,
    PolicyRegistry,
    assess_configured_stayman_continuation_strength,
    configured_stayman_continuation_strength_policy_id,
    resolve_stayman_continuation_strength_policy,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.stayman_continuation_strength_policy import (
    assess_stayman_continuation_strength,
)


SOURCE = KnowledgeSource(
    "bidding/conventions/responses/stayman", "Responder's Continuations"
)


class FixedPolicy:
    def __init__(self, classification):
        self.policy_id = f"fixture.stayman.{classification.value}"
        self.classification = classification

    def assess(self, context):
        if self.classification is StaymanContinuationStrength.UNKNOWN:
            return StaymanContinuationStrengthAssessment(
                self.policy_id, self.classification
            )
        return StaymanContinuationStrengthAssessment(
            self.policy_id,
            self.classification,
            "Explicit test classification.",
            (SOURCE,),
        )


def context(policy_id=None, calls=("1NT", "P", "2C", "P", "2H", "P")):
    options = (
        {}
        if policy_id is None
        else {STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION: policy_id}
    )
    return BiddingContext.create(
        hand=Hand.parse("KJ97.842.63.AQ63"),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", options),
    )


@pytest.mark.parametrize("classification", tuple(StaymanContinuationStrength))
def test_all_narrow_classifications_are_supported(classification):
    policy = FixedPolicy(classification)
    result = assess_stayman_continuation_strength(policy, context())
    assert result.classification is classification
    assert not hasattr(result, "candidate")
    assert not hasattr(result, "recommended_call")


def test_known_classifications_require_explanation_and_source():
    with pytest.raises(ValueError):
        StaymanContinuationStrengthAssessment(
            "fixture", StaymanContinuationStrength.GAME_GOING
        )
    with pytest.raises(ValueError):
        StaymanContinuationStrengthAssessment(
            "fixture", StaymanContinuationStrength.OTHER, "explanation"
        )
    unknown = StaymanContinuationStrengthAssessment(
        "fixture", StaymanContinuationStrength.UNKNOWN
    )
    assert unknown.sources == ()


def test_production_policy_module_has_no_numeric_strength_classifier():
    source = inspect.getsource(
        __import__(
            "bridge.stayman_continuation_strength_policy", fromlist=["unused"]
        )
    ).casefold()
    assert "high_card_points" not in source
    assert "hcp" not in source
    assert "0-7" not in source
    assert "8-9" not in source
    assert "10+" not in source


def test_explicit_registration_resolution_and_assessment():
    policy = FixedPolicy(StaymanContinuationStrength.GAME_GOING)
    registry = PolicyRegistry.from_stayman_continuation_strength_policies((policy,))
    configured = context(policy.policy_id)
    assert configured_stayman_continuation_strength_policy_id(configured.system) == policy.policy_id
    assert resolve_stayman_continuation_strength_policy(configured.system, registry) is policy
    result = assess_configured_stayman_continuation_strength(configured, registry)
    assert result is not None
    assert result.classification is StaymanContinuationStrength.GAME_GOING


def test_missing_and_unregistered_configuration_resolve_none_without_fallback():
    game = FixedPolicy(StaymanContinuationStrength.GAME_GOING)
    other = FixedPolicy(StaymanContinuationStrength.OTHER)
    registry = PolicyRegistry.from_stayman_continuation_strength_policies((game, other))
    assert resolve_stayman_continuation_strength_policy(context().system, registry) is None
    assert assess_configured_stayman_continuation_strength(context(), registry) is None
    assert resolve_stayman_continuation_strength_policy(context("missing").system, registry) is None
    assert assess_configured_stayman_continuation_strength(context("missing"), registry) is None


def test_default_registry_is_empty_and_jacoby_surface_is_unchanged():
    registry = PolicyRegistry()
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.stayman_continuation_strength_policy("missing") is None
    assert registry.jacoby_continuation_strength_policy("missing") is None


def test_policy_architecture_adds_no_route_or_production_call():
    policy = StaymanGameGoingAuditFixture()
    registry = PolicyRegistry.from_stayman_continuation_strength_policies((policy,))
    router = create_standard_sayc_router(registry)
    assert len(router.routes) == 45
    assert router.evaluate(context(policy.policy_id)).recommended_call is None
    assert create_standard_sayc_router().evaluate(context()).recommended_call is None


def test_phase12f_benchmark_reproduction_and_future_target():
    result = run_stayman_policy_architecture_validation()
    assert result.endpoint_counts == {"2D": 104, "2H": 70, "2S": 61}
    assert (result.heart_fit_target, result.spade_fit_target) == (17, 21)
    assert result.total_future_fit_target == 38
    assert result.dual_major_abstentions == 36
    assert result.no_fit_branches_deferred
    assert result.production_routes_before == 42
    assert result.production_routes_after == 45
    assert result.production_bidding_calls_added == 0


def test_phase12f_architecture_benchmark_is_deterministic():
    assert (
        run_stayman_policy_architecture_validation()
        == run_stayman_policy_architecture_validation()
    )
