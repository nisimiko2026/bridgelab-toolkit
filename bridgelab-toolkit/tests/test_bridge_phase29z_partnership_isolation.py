"""Phase 29Z: two test-only partnerships cannot inherit each other's choices."""

from dataclasses import FrozenInstanceError, fields
import importlib
import json

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.nisim_nily_six_minor_preempt_policy import assess_six_minor_three_level_preempt
from bridge.opening_policy_six_minor_integration_audit import assess_opening_policy_with_six_minor
from bridge.opening_six_minor_production_adoption_audit import build_six_minor_production_adoption_audit
from bridge.partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    AgreementSourceScope,
    PartnershipProfile,
    ResolvedAgreement,
    ResolvedBiddingProfile,
    resolve_partnership_profile,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile, classify_system_profile


@pytest.fixture
def partnership_b():
    """Synthetic resolver fixture, not a convention card or production profile."""
    return PartnershipProfile(
        profile_id="isolation-partnership-b",
        version="29Z.1",
        base_system=SystemProfile.TWO_OVER_ONE_GF,
        agreements=(
            AgreementSelection(
                "response.major.two_over_one", AgreementResolution.ENABLE, "game_force"
            ),
        ),
    )


@pytest.fixture
def partnership_c():
    """Synthetic different-system control, with no selected treatments."""
    return PartnershipProfile("isolation-partnership-c", "29Z.1", SystemProfile.SAYC, ())


@pytest.fixture
def base_agreements():
    # Minimal shared TWO_OVER_ONE_GF input. IDs are fixture labels only; this
    # tuple is not a complete or authoritative base-system convention card.
    return (
        ResolvedAgreement("opening.2d", "fixture_base_2d", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2h", "fixture_base_2h", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2s", "fixture_base_2s", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2nt", "fixture_base_2nt", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("response.major.raises", "fixture_base_raise", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("response.major.two_over_one", "game_force", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
    )


@pytest.fixture
def base_capabilities():
    return ("fixture_base_capability_b", "fixture_base_capability_a")


def _resolve_pair(partnership_b, base_agreements, base_capabilities):
    return (
        resolve_partnership_profile(
            NISIM_NILY_PROFILE,
            base_agreements=base_agreements,
            base_capabilities=base_capabilities,
        ),
        resolve_partnership_profile(
            partnership_b,
            base_agreements=base_agreements,
            base_capabilities=base_capabilities,
        ),
    )


def test_same_system_distinct_partnerships_and_treatment_inventory(
    partnership_b, base_agreements, base_capabilities
):
    nisim, other = _resolve_pair(partnership_b, base_agreements, base_capabilities)
    assert NISIM_NILY_PROFILE.base_system is partnership_b.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert NISIM_NILY_PROFILE.profile_id != partnership_b.profile_id
    assert isinstance(nisim, ResolvedBiddingProfile)
    assert isinstance(other, ResolvedBiddingProfile)
    assert nisim != other
    assert nisim.base_system is other.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert nisim.profile_id == "nisim-nily"
    assert other.profile_id == "isolation-partnership-b"
    assert {agreement.family: agreement.treatment_id for agreement in nisim.agreements} == {
        "opening.2d": "multi_2d",
        "opening.2h": "nisim_nily_5h_5minor",
        "opening.2s": "nisim_nily_5s_5minor",
        "opening.2nt": "nisim_nily_5c_5d",
        "opening.three_level.six_minor": "nisim_nily_six_minor_preempt",
        "response.major.1nt": "forcing",
        "response.major.raises": "bergen",
        "response.major.two_over_one": "game_force",
    }
    assert {agreement.family: agreement.treatment_id for agreement in other.agreements} == {
        "opening.2d": "fixture_base_2d",
        "opening.2h": "fixture_base_2h",
        "opening.2s": "fixture_base_2s",
        "opening.2nt": "fixture_base_2nt",
        "response.major.raises": "fixture_base_raise",
        "response.major.two_over_one": "game_force",
    }


def test_no_nisim_nily_treatment_leaks_to_second_partnership(
    partnership_b, base_agreements, base_capabilities
):
    nisim, other = _resolve_pair(partnership_b, base_agreements, base_capabilities)
    forbidden = {
        "multi_2d", "nisim_nily_5h_5minor", "nisim_nily_5s_5minor",
        "nisim_nily_5c_5d", "nisim_nily_six_minor_preempt", "bergen", "forcing",
    }
    assert forbidden <= {agreement.treatment_id for agreement in nisim.agreements}
    assert forbidden.isdisjoint({agreement.treatment_id for agreement in other.agreements})
    assert other.agreement("opening.2d").treatment_id == "fixture_base_2d"
    assert other.agreement("response.major.raises").treatment_id == "fixture_base_raise"
    assert other.agreement("response.major.1nt") is None
    assert other.agreement("opening.three_level.six_minor") is None
    assert all(agreement.source_scope is AgreementSourceScope.SYSTEM
               for agreement in other.agreements if agreement.family != "response.major.two_over_one")


def test_replacement_is_local_order_independent_and_does_not_mutate_inputs(
    partnership_b, base_agreements, base_capabilities
):
    original_base = tuple(agreement.to_dict() for agreement in base_agreements)
    original_nisim = NISIM_NILY_PROFILE.to_json()
    original_b = partnership_b.to_json()
    original_capabilities = base_capabilities

    nisim_first, b_second = _resolve_pair(partnership_b, base_agreements, base_capabilities)
    b_first = resolve_partnership_profile(
        partnership_b, base_agreements=base_agreements, base_capabilities=base_capabilities
    )
    nisim_second = resolve_partnership_profile(
        NISIM_NILY_PROFILE, base_agreements=base_agreements,
        base_capabilities=base_capabilities,
    )
    assert nisim_first == nisim_second
    assert b_first == b_second
    assert nisim_first.to_json() == nisim_second.to_json()
    assert b_first.to_json() == b_second.to_json()
    assert nisim_first.to_dict() == nisim_second.to_dict()
    assert b_first.to_dict() == b_second.to_dict()
    assert b_first.agreement("opening.2d").treatment_id == "fixture_base_2d"
    assert base_agreements[0].treatment_id == "fixture_base_2d"
    assert tuple(agreement.to_dict() for agreement in base_agreements) == original_base
    assert NISIM_NILY_PROFILE.to_json() == original_nisim
    assert partnership_b.to_json() == original_b
    assert base_capabilities == original_capabilities


def test_effective_values_and_capabilities_are_immutable_and_isolated(
    partnership_b, base_agreements, base_capabilities
):
    nisim, other = _resolve_pair(partnership_b, base_agreements, base_capabilities)
    assert isinstance(nisim.agreements, tuple)
    assert isinstance(other.agreements, tuple)
    assert nisim.agreements != other.agreements
    assert nisim.capabilities == other.capabilities == tuple(sorted(base_capabilities))
    assert nisim.capabilities == resolve_partnership_profile(
        NISIM_NILY_PROFILE, base_agreements=base_agreements,
        base_capabilities=base_capabilities,
    ).capabilities
    assert resolve_partnership_profile(partnership_b, base_agreements=base_agreements).capabilities == ()
    for value in (nisim, other):
        with pytest.raises(FrozenInstanceError):
            value.profile_id = "mutated"
    for value in (nisim.agreement("opening.2d"), other.agreement("opening.2d")):
        with pytest.raises(FrozenInstanceError):
            value.family = "mutated"
    detached = json.loads(nisim.to_json())
    detached["agreements"].clear()
    detached["capabilities"].append("leak")
    assert nisim.agreement("opening.2d").treatment_id == "multi_2d"
    assert other.agreement("opening.2d").treatment_id == "fixture_base_2d"
    assert "leak" not in nisim.capabilities + other.capabilities


def test_third_test_only_partnership_has_different_system_without_leakage(
    partnership_b, partnership_c, base_agreements, base_capabilities
):
    nisim, other = _resolve_pair(partnership_b, base_agreements, base_capabilities)
    third = resolve_partnership_profile(partnership_c)
    assert (nisim.base_system, other.base_system, third.base_system) == (
        SystemProfile.TWO_OVER_ONE_GF, SystemProfile.TWO_OVER_ONE_GF, SystemProfile.SAYC
    )
    assert third.profile_id == "isolation-partnership-c"
    assert third.agreements == ()
    assert third.capabilities == ()
    assert third.agreement("opening.2d") is None
    assert third.agreement("response.major.raises") is None


def test_profile_import_does_not_change_system_identity_contexts_or_routes(
    partnership_b, base_agreements, base_capabilities
):
    router_before = create_standard_sayc_router()
    inventory_before = tuple(route.route_id for route in router_before.routes)
    system_fields_before = tuple(field.name for field in fields(SystemContext))
    bidding_fields_before = tuple(field.name for field in fields(BiddingContext))
    system_defaults_before = SystemContext("TWO_OVER_ONE_GF")
    sayc_context = BiddingContext.create(
        hand=Hand.parse("7.84.KQJT96.9742"), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW, system=SystemContext("SAYC"),
    )
    decision_before = router_before.evaluate(sayc_context)

    imported = importlib.reload(importlib.import_module("bridge.nisim_nily_partnership_profile"))
    assert imported.NISIM_NILY_PROFILE == NISIM_NILY_PROFILE
    _resolve_pair(partnership_b, base_agreements, base_capabilities)

    router_after = create_standard_sayc_router()
    inventory_after = tuple(route.route_id for route in router_after.routes)
    assert len(inventory_before) == len(inventory_after) == 45
    assert inventory_after == inventory_before
    assert not any("nisim" in route_id.casefold() or "isolation-partnership-b" in route_id.casefold()
                   for route_id in inventory_after)
    assert router_after.evaluate(sayc_context) == decision_before
    assert tuple(field.name for field in fields(SystemContext)) == system_fields_before == (
        "system", "options"
    )
    assert tuple(field.name for field in fields(BiddingContext)) == bidding_fields_before == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )
    assert SystemContext("TWO_OVER_ONE_GF") == system_defaults_before
    assert SystemContext("TWO_OVER_ONE_GF").options == ()
    assert classify_system_profile(SystemContext("TWO_OVER_ONE_GF")) is SystemProfile.TWO_OVER_ONE_GF
    assert classify_system_profile(SystemContext("nisim-nily")) is SystemProfile.UNKNOWN
    assert classify_system_profile(SystemContext("isolation-partnership-b")) is SystemProfile.UNKNOWN
    assert {member.value for member in SystemProfile} == {"SAYC", "TWO_OVER_ONE_GF", "UNKNOWN"}


def test_historical_audits_still_report_no_production_adoption():
    hand = Hand.parse("7.84.KQJT96.9742")
    six_minor = assess_six_minor_three_level_preempt(
        hand, seat=Seat.SOUTH, vulnerability=Vulnerability.EW, opening_position=3
    )
    integrated = assess_opening_policy_with_six_minor(
        hand, auction=Auction(Seat.NORTH, ("P", "P")), vulnerability=Vulnerability.EW
    )
    adoption_audit = build_six_minor_production_adoption_audit()
    assert six_minor.production_adopted is False
    assert integrated.production_adopted is False
    assert adoption_audit.production_changed is False
    assert adoption_audit.ready_for_production is False
