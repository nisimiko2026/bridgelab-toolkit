import inspect

import pytest

from benchmarks.stayman_dual_major_policy_architecture import (
    FixedStaymanDualMajorResponsePolicy,
    SOURCE,
)
from bridge import (
    Auction,
    BiddingContext,
    Hand,
    Seat,
    StaymanDualMajorResponse,
    StaymanDualMajorResponseAssessment,
    SystemContext,
    Vulnerability,
    assess_stayman_dual_major_response,
)
from bridge.policy_registry import (
    STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION,
    PolicyRegistry,
    assess_configured_stayman_dual_major_response,
    configured_stayman_dual_major_response_policy_id,
    resolve_stayman_dual_major_response_policy,
)


def context(policy_id=None):
    options = (
        {}
        if policy_id is None
        else {STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION: policy_id}
    )
    return BiddingContext.create(
        hand=Hand.parse("KJ97.AQ63.842.63"),
        auction=Auction(Seat.NORTH, ("1NT", "P", "2C", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", options),
    )


@pytest.mark.parametrize("response", tuple(StaymanDualMajorResponse))
def test_all_theory_neutral_response_choices_are_valid(response):
    policy = FixedStaymanDualMajorResponsePolicy(response)
    result = assess_stayman_dual_major_response(policy, context())
    assert result.response is response
    assert not hasattr(result, "candidate")
    assert not hasattr(result, "recommended_call")
    assert not hasattr(result, "call")


def test_known_choices_require_explanation_and_source_but_unknown_does_not():
    with pytest.raises(ValueError):
        StaymanDualMajorResponseAssessment(
            "fixture", StaymanDualMajorResponse.HEARTS
        )
    with pytest.raises(ValueError):
        StaymanDualMajorResponseAssessment(
            "fixture", StaymanDualMajorResponse.SPADES, "explanation"
        )
    known = StaymanDualMajorResponseAssessment(
        "fixture", StaymanDualMajorResponse.HEARTS, "explicit choice", (SOURCE,)
    )
    unknown = StaymanDualMajorResponseAssessment(
        "fixture", StaymanDualMajorResponse.UNKNOWN
    )
    assert known.sources == (SOURCE,)
    assert unknown.sources == ()


def test_policy_module_has_no_call_translation_or_numeric_hcp_boundary():
    source = inspect.getsource(
        __import__("bridge.stayman_dual_major_response_policy", fromlist=["unused"])
    ).casefold()
    assert "high_card_points" not in source
    assert "hcp" not in source
    assert "call.parse" not in source
    assert '"2h"' not in source
    assert '"2s"' not in source


def test_explicit_registration_configuration_resolution_and_assessment():
    policy = FixedStaymanDualMajorResponsePolicy(StaymanDualMajorResponse.HEARTS)
    registry = PolicyRegistry.from_stayman_dual_major_response_policies((policy,))
    configured = context(policy.policy_id)
    assert registry.stayman_dual_major_response_policy_ids == (policy.policy_id,)
    assert (
        configured_stayman_dual_major_response_policy_id(configured.system)
        == policy.policy_id
    )
    assert resolve_stayman_dual_major_response_policy(configured.system, registry) is policy
    result = assess_configured_stayman_dual_major_response(configured, registry)
    assert result is not None
    assert result.response is StaymanDualMajorResponse.HEARTS


def test_missing_and_unknown_configuration_resolve_none_without_fallback():
    policy = FixedStaymanDualMajorResponsePolicy(StaymanDualMajorResponse.SPADES)
    registry = PolicyRegistry.from_stayman_dual_major_response_policies((policy,))
    assert resolve_stayman_dual_major_response_policy(context().system, registry) is None
    assert assess_configured_stayman_dual_major_response(context(), registry) is None
    assert resolve_stayman_dual_major_response_policy(context("missing").system, registry) is None
    assert assess_configured_stayman_dual_major_response(context("missing"), registry) is None


def test_default_registry_has_no_policy_and_prior_policy_families_are_unchanged():
    registry = PolicyRegistry()
    assert registry.stayman_dual_major_response_policy_ids == ()
    assert registry.stayman_dual_major_response_policy("missing") is None
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.stayman_continuation_strength_policy("missing") is None
    assert registry.jacoby_continuation_strength_policy("missing") is None
