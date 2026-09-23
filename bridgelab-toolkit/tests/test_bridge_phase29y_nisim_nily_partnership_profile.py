"""Canonical profile data and its isolation from production routing."""

from dataclasses import FrozenInstanceError, fields
import importlib
import json
from pathlib import Path

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
    resolve_partnership_profile,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile


EXPECTED = {
    "opening.2d": (AgreementResolution.REPLACE, "multi_2d"),
    "opening.2h": (AgreementResolution.REPLACE, "nisim_nily_5h_5minor"),
    "opening.2s": (AgreementResolution.REPLACE, "nisim_nily_5s_5minor"),
    "opening.2nt": (AgreementResolution.REPLACE, "nisim_nily_5c_5d"),
    "opening.three_level.six_minor": (AgreementResolution.ENABLE, "nisim_nily_six_minor_preempt"),
    "response.major.1nt": (AgreementResolution.ENABLE, "forcing"),
    "response.major.raises": (AgreementResolution.ENABLE, "bergen"),
    "response.major.two_over_one": (AgreementResolution.ENABLE, "game_force"),
}


@pytest.fixture
def base_agreements():
    # Deliberately small resolver fixture, not a complete 2/1 system definition.
    return (
        ResolvedAgreement("opening.2d", "fixture_natural_2d", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2h", "fixture_natural_2h", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2s", "fixture_natural_2s", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2nt", "fixture_natural_2nt", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.1c", "fixture_unrelated_clubs", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
    )


def _context():
    return BiddingContext.create(
        hand=Hand.parse("7.84.KQJT96.9742"),
        auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )


def test_canonical_identity_version_provenance_and_immutability():
    profile = NISIM_NILY_PROFILE
    assert isinstance(profile, PartnershipProfile)
    assert profile.profile_id == "nisim-nily"
    assert profile.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert profile.version == "29Y.1"
    assert "bidding/convention-cards/cc-nily-nisim" in profile.sources
    with pytest.raises(FrozenInstanceError):
        profile.profile_id = "another-pair"
    with pytest.raises(FrozenInstanceError):
        profile.agreements[0].treatment_id = "other"


@pytest.mark.parametrize("family,expected", sorted(EXPECTED.items()))
def test_exact_approved_agreement(family, expected):
    profile = NISIM_NILY_PROFILE
    assert {selection.family for selection in profile.agreements} == set(EXPECTED)
    selection = next(selection for selection in profile.agreements if selection.family == family)
    assert isinstance(selection, AgreementSelection)
    assert (selection.resolution, selection.treatment_id) == expected
    assert selection.parameters == ()


def test_profile_serialization_is_stable_and_contains_only_metadata():
    profile = NISIM_NILY_PROFILE
    first = profile.to_json()
    assert first == profile.to_json()
    assert json.loads(first) == profile.to_dict()
    assert json.loads(first)["base_system"] == "TWO_OVER_ONE_GF"
    assert len(json.loads(first)["agreements"]) == 8
    assert "production" not in first
    assert not any(name in first.casefold() for name in (
        "stayman", "jacoby", "transfers", "smolen", "rkcb", "drury",
        "lebensohl", "landy", "ghestem", "negative_double", "lead", "signal",
    ))


@pytest.mark.parametrize("family", ("opening.2d", "opening.2h", "opening.2s", "opening.2nt"))
def test_resolution_replaces_four_base_openings(family, base_agreements):
    original = next(agreement for agreement in base_agreements if agreement.family == family)
    resolved = resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements)
    effective = resolved.agreement(family)
    assert effective.treatment_id == EXPECTED[family][1] != original.treatment_id
    assert effective.resolution is AgreementResolution.REPLACE
    assert effective.source_scope is AgreementSourceScope.PARTNERSHIP


def test_resolution_adds_six_minor_and_preserves_unrelated_base(base_agreements):
    resolved = resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements)
    added = resolved.agreement("opening.three_level.six_minor")
    assert added.treatment_id == "nisim_nily_six_minor_preempt"
    assert added.resolution is AgreementResolution.ENABLE
    assert added.source_scope is AgreementSourceScope.PARTNERSHIP
    assert resolved.agreement("opening.1c") == next(
        agreement for agreement in base_agreements if agreement.family == "opening.1c"
    )
    assert resolved.agreement("opening.1c").source_scope is AgreementSourceScope.SYSTEM
    assert resolved.capabilities == ()


def test_repeated_resolution_is_deterministic_and_does_not_mutate_profile(base_agreements):
    before = NISIM_NILY_PROFILE.to_json()
    first = resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements,
                                        base_capabilities=("base_capability",))
    second = resolve_partnership_profile(NISIM_NILY_PROFILE,
                                         base_agreements=tuple(reversed(base_agreements)),
                                         base_capabilities=("base_capability",))
    assert first == second
    assert first.to_json() == second.to_json()
    assert first.capabilities == ("base_capability",)
    assert NISIM_NILY_PROFILE.to_json() == before


def test_other_partnership_with_same_base_stays_independent(base_agreements):
    other = PartnershipProfile("other-pair", "1", SystemProfile.TWO_OVER_ONE_GF, ())
    before = resolve_partnership_profile(other, base_agreements=base_agreements)
    resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements)
    after = resolve_partnership_profile(other, base_agreements=base_agreements)
    assert before == after
    assert after.agreement("opening.2d").treatment_id == "fixture_natural_2d"
    assert after.agreement("opening.2d").source_scope is AgreementSourceScope.SYSTEM
    for family in ("opening.three_level.six_minor", "response.major.1nt", "response.major.raises"):
        assert after.agreement(family) is None


def test_import_does_not_read_card_or_build_router(monkeypatch):
    # bridge.__init__ loads the standard router on package import. This guards
    # this specific module's execution, after that pre-existing package setup.
    module = importlib.import_module("bridge.nisim_nily_partnership_profile")
    original_open = Path.open
    original_read_text = Path.read_text

    def guarded_open(path, *args, **kwargs):
        if path.suffix.casefold() == ".md":
            raise AssertionError("profile import opened Markdown")
        return original_open(path, *args, **kwargs)

    def guarded_read_text(path, *args, **kwargs):
        if path.suffix.casefold() == ".md":
            raise AssertionError("profile import read Markdown")
        return original_read_text(path, *args, **kwargs)

    def forbidden_router(*args, **kwargs):
        raise AssertionError("profile import built a router")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    monkeypatch.setattr("bridge.sayc_route_configuration.create_standard_sayc_router", forbidden_router)
    imported = importlib.reload(module)
    assert imported.NISIM_NILY_PROFILE == NISIM_NILY_PROFILE


def test_import_and_resolution_leave_production_behavior_and_context_shapes_unchanged():
    router_before = create_standard_sayc_router()
    context = _context()
    result_before = router_before.evaluate(context)
    route_ids_before = tuple(route.route_id for route in router_before.routes)
    importlib.import_module("bridge.nisim_nily_partnership_profile")
    resolve_partnership_profile(NISIM_NILY_PROFILE)
    router_after = create_standard_sayc_router()
    assert len(router_before.routes) == len(router_after.routes) == 45
    assert tuple(route.route_id for route in router_after.routes) == route_ids_before
    assert not any("nisim" in route_id.casefold() for route_id in route_ids_before)
    assert router_after.evaluate(context) == result_before
    assert result_before.recommended_call.serialize() == "2D"
    assert tuple(field.name for field in fields(SystemContext)) == ("system", "options")
    assert tuple(field.name for field in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )


def test_historical_policy_and_audits_still_report_no_adoption():
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
