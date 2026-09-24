"""Phase 30I legacy SystemContext compatibility, without base routing."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.base_system_composition import (
    BaseSystemCompositionDisposition, BaseSystemContinuationRequest,
    compose_profile_opening_with_base,
)
from bridge.base_system_execution_adapter import (
    BaseSystemExecutionCapability, BaseSystemExecutionContext,
    adapt_base_system_continuation,
)
from bridge.bidding_rules import BiddingContext, KnowledgeSource, SystemContext
from bridge.major_response_options import TwoOverOneTreatment, two_over_one_treatment
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.partnership_profiles import (
    AgreementResolution, AgreementSelection, PartnershipProfile,
    resolve_partnership_profile,
)
from bridge.policy_registry import PolicyRegistry
from bridge.profile_compiler import compile_profile_plan
from bridge.profile_opening_adapter import ProfileOpeningDisposition, evaluate_profile_opening_shadow
from bridge.sayc import create_sayc_opening_engine
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.suit_quality_policy import SuitQualityAssessment
from bridge.system_profiles import (
    SystemProfile, classify_system_profile, supports_two_over_one_game_force,
)
from bridge.two_over_one_opener_rebids import create_sayc_two_over_one_opener_rebid_engine
from bridge.two_over_one_responses import create_sayc_two_over_one_response_engine


FAMILY = "opening.three_level.six_minor"
HAND = Hand.parse("7.84.KQJT96.9742")


@pytest.fixture(scope="module")
def handoffs():
    nisim = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
    peer_profile = PartnershipProfile(
        "phase30i-peer", "30I.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    peer = compile_profile_plan(resolve_partnership_profile(peer_profile))
    negative = evaluate_profile_opening_shadow(
        nisim, hand=Hand.parse("7.84.QJT986.9742"), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.NONE,
    )
    peer_assessment = evaluate_profile_opening_shadow(
        peer, hand=HAND, auction=Auction(Seat.EAST), vulnerability=Vulnerability.EW,
    )
    assert negative.disposition is ProfileOpeningDisposition.ABSTAIN
    assert peer_assessment.disposition is ProfileOpeningDisposition.NO_BINDING
    nisim_result = compose_profile_opening_with_base(nisim, negative)
    peer_result = compose_profile_opening_with_base(peer, peer_assessment)
    assert nisim_result.composition_disposition is BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION
    assert peer_result.composition_disposition is BaseSystemCompositionDisposition.BASE_SYSTEM_CONTINUATION
    assert nisim_result.partnership_call is peer_result.partnership_call is None
    return (nisim, nisim_result.base_continuation), (peer, peer_result.base_continuation)


def test_nisim_and_peer_preserve_the_same_base_identity_without_overlay(handoffs):
    (nisim, nisim_request), (peer, peer_request) = handoffs
    before = (nisim.to_json(), peer.to_json(), nisim_request.to_json(), peer_request.to_json())
    nisim_adapted = adapt_base_system_continuation(nisim, nisim_request)
    peer_adapted = adapt_base_system_continuation(peer, peer_request)
    for plan, request, adapted in ((nisim, nisim_request, nisim_adapted),
                                   (peer, peer_request, peer_adapted)):
        assert isinstance(adapted, BaseSystemExecutionContext)
        assert isinstance(adapted.system_context, SystemContext)
        assert (adapted.profile_id, adapted.profile_version, adapted.base_system, adapted.family) == (
            plan.profile_id, plan.profile_version, plan.base_system, request.family)
        assert adapted.system_context.system == "TWO_OVER_ONE_GF"
        assert adapted.system_context.options == (("two_over_one", "game_force"),)
        assert adapted.system_context.option("two_over_one") == "game_force"
        assert classify_system_profile(adapted.system_context) is SystemProfile.TWO_OVER_ONE_GF
        assert two_over_one_treatment(adapted.system_context) is TwoOverOneTreatment.GAME_FORCE
        assert supports_two_over_one_game_force(adapted.system_context)
        assert adapted.production_adopted is False
    assert nisim_adapted.system_context == peer_adapted.system_context
    assert not any(key in dict(nisim_adapted.system_context.options) for key in (
        "forcing_one_notrump", "major_raise_style", "bergen", "multi",
        "puppet", "jacoby", "texas", "drury", "lebensohl"))
    assert before == (nisim.to_json(), peer.to_json(), nisim_request.to_json(), peer_request.to_json())
    assert nisim_adapted.to_json() == adapt_base_system_continuation(nisim, nisim_request).to_json()


def test_sayc_is_plain_sayc_and_unknown_is_rejected():
    profile = PartnershipProfile("phase30i-sayc", "30I.test", SystemProfile.SAYC, ())
    plan = compile_profile_plan(resolve_partnership_profile(profile))
    request = BaseSystemContinuationRequest(plan.profile_id, plan.profile_version,
                                            plan.base_system, FAMILY, "No profile binding.")
    adapted = adapt_base_system_continuation(plan, request)
    assert adapted.system_context == SystemContext("SAYC")
    assert adapted.system_context.options == ()
    assert classify_system_profile(adapted.system_context) is SystemProfile.SAYC
    assert two_over_one_treatment(adapted.system_context) is TwoOverOneTreatment.UNSPECIFIED
    assert not supports_two_over_one_game_force(adapted.system_context)
    with pytest.raises(ValueError):
        BaseSystemContinuationRequest("unknown", "1", SystemProfile.UNKNOWN, FAMILY, "Unsupported")
    with pytest.raises(ValueError):
        replace(adapted, base_system=SystemProfile.UNKNOWN)


@pytest.mark.parametrize("field,value", [
    ("profile_id", "another-profile"),
    ("profile_version", "another-version"),
    ("base_system", SystemProfile.SAYC),
])
def test_plan_request_identity_mismatch_is_rejected(handoffs, field, value):
    plan, request = handoffs[0]
    with pytest.raises(ValueError, match="does not match"):
        adapt_base_system_continuation(plan, replace(request, **{field: value}))


def test_immutable_context_and_deterministic_structured_serialization(handoffs):
    plan, request = handoffs[0]
    adapted = adapt_base_system_continuation(plan, request)
    expected = {
        "profile_id": plan.profile_id,
        "profile_version": plan.profile_version,
        "base_system": "TWO_OVER_ONE_GF",
        "family": FAMILY,
        "system_context": {
            "system": "TWO_OVER_ONE_GF",
            "options": [["two_over_one", "game_force"]],
        },
        "adapter_version": "30I.1",
        "production_adopted": False,
    }
    assert adapted.to_dict() == expected
    assert json.loads(adapted.to_json()) == expected
    assert "SystemContext(" not in adapted.to_json()
    with pytest.raises(FrozenInstanceError):
        adapted.family = "other"
    with pytest.raises(FrozenInstanceError):
        adapted.system_context.system = "SAYC"
    with pytest.raises(ValueError):
        replace(adapted, system_context=SystemContext("SAYC"))
    with pytest.raises(ValueError):
        replace(adapted, production_adopted=True)


POLICY_SOURCE = KnowledgeSource("bidding/systems/2-over-1", "Hands Suitable for a 2/1 Response")


class FixtureQualityPolicy:
    policy_id = "fixture.quality"

    def assess(self, context, suit):
        return SuitQualityAssessment.qualifies(
            self.policy_id, suit, context.evaluation.quality_evidence(suit),
            "fixture qualifies", (POLICY_SOURCE,),
        )


@pytest.fixture(scope="module")
def component_results(handoffs):
    plan, request = handoffs[0]
    adapted = adapt_base_system_continuation(plan, request)
    # Suit quality is explicit test input for the existing response rule. The
    # adapter itself emits only the base-system compatibility option.
    response_options = dict(adapted.system_context.options)
    response_options["suit_quality_policy"] = "fixture.quality"
    response_context = BiddingContext.create(
        hand=Hand.parse("82.KQ3.64.AKQJ97"),
        auction=Auction(Seat.NORTH, ("1S", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(adapted.system_context.system, response_options),
    )
    registry = PolicyRegistry.from_suit_quality_policies([FixtureQualityPolicy()])
    response = create_sayc_two_over_one_response_engine(registry).evaluate(response_context)
    rebid_context = BiddingContext.create(
        hand=Hand.parse("AKQ97.82.KQJ4.32"),
        auction=Auction(Seat.NORTH, ("1S", "P", "2C", "P")),
        vulnerability=Vulnerability.NONE,
        system=adapted.system_context,
    )
    rebid = create_sayc_two_over_one_opener_rebid_engine().evaluate(rebid_context)
    opening_context = BiddingContext.create(
        hand=Hand.parse("AQ84.KJ6.A75.K92"),
        auction=Auction(Seat.NORTH), vulnerability=Vulnerability.NONE,
        system=adapted.system_context,
    )
    two_over_one_opening = create_sayc_opening_engine().evaluate(opening_context)
    sayc_opening = create_sayc_opening_engine().evaluate(replace(
        opening_context, system=SystemContext("SAYC")))
    return adapted, response, rebid, two_over_one_opening, sayc_opening


def test_existing_response_and_rebid_components_execute_with_adapted_identity(component_results):
    adapted, response, rebid, _, _ = component_results
    assert adapted.system_context.system == "TWO_OVER_ONE_GF"
    assert response.has_recommendation
    assert response.recommended_call.serialize() == "2C"
    assert rebid.has_recommendation
    assert rebid.recommended_call.serialize() == "2D"
    acol_context = BiddingContext.create(
        hand=Hand.parse("AKQ97.82.KQJ4.32"),
        auction=Auction(Seat.NORTH, ("1S", "P", "2C", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("Acol", {"two_over_one": "game_force"}),
    )
    assert not create_sayc_two_over_one_opener_rebid_engine().evaluate(acol_context).has_recommendation
    assert classify_system_profile(acol_context.system) is SystemProfile.UNKNOWN


def test_sayc_opening_engine_rejects_adapted_two_over_one_system(component_results):
    adapted, _, _, two_over_one_opening, sayc_opening = component_results
    assert adapted.system_context.system == "TWO_OVER_ONE_GF"
    assert not two_over_one_opening.has_recommendation
    assert sayc_opening.recommended_call.serialize() == "1NT"


def test_capability_reports_observed_results_without_claiming_base_execution(component_results):
    _, response, rebid, two_over_one_opening, _ = component_results
    capability = BaseSystemExecutionCapability(
        two_over_one_response_component_verified=(
            response.has_recommendation and response.recommended_call.serialize() == "2C"),
        two_over_one_rebid_component_verified=(
            rebid.has_recommendation and rebid.recommended_call.serialize() == "2D"),
        legacy_context_adapter_ready=True,
        opening_component_ready=two_over_one_opening.has_recommendation,
    )
    assert capability.legacy_context_adapter_ready
    assert capability.two_over_one_response_component_verified
    assert capability.two_over_one_rebid_component_verified
    assert not capability.opening_component_ready
    assert not capability.generic_base_execution_ready
    assert not capability.production_bidding_changed
    assert not capability.production_adopted
    assert capability.phase == "30I" and capability.version == "30I.1"
    assert json.loads(capability.to_json()) == capability.to_dict()
    with pytest.raises(FrozenInstanceError):
        capability.opening_component_ready = True
    with pytest.raises(ValueError):
        replace(capability, generic_base_execution_ready=True)
    with pytest.raises(ValueError):
        replace(capability, production_adopted=True)


def test_route_context_shapes_and_adapter_import_boundaries():
    before = tuple(route.route_id for route in create_standard_sayc_router().routes)
    source = Path(__file__).resolve().parents[1] / "bridge" / "base_system_execution_adapter.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    after = tuple(route.route_id for route in create_standard_sayc_router().routes)
    assert len(before) == len(after) == 45
    assert before == after
    assert not any(marker in route_id.casefold() for route_id in after
                   for marker in ("nisim", "30i"))
    assert tuple(f.name for f in fields(SystemContext)) == ("system", "options")
    assert tuple(f.name for f in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system")
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not imports.intersection({
        "sayc", "sayc_route_configuration", "engine_router", "bidding_engine",
        "two_over_one_responses", "two_over_one_opener_rebids", "deal_simulator",
    })
    definitions = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not definitions.intersection({
        "create_two_over_one_router", "create_base_system_router", "create_profile_router",
        "create_bidding_router", "EngineRoute", "BiddingEngine", "RuleDecision",
        "BiddingEngineResult", "BaseSystemExecutor", "ProfileRouter",
    })
