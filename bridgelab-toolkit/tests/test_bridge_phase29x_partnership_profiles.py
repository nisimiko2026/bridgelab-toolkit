"""Architecture-only profile resolution and production isolation checks."""

import json
from dataclasses import FrozenInstanceError, fields, replace

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.opening_six_minor_production_adoption_audit import build_six_minor_production_adoption_audit
from bridge.partnership_profiles import (
    AgreementResolution as Resolution,
    AgreementSelection,
    AgreementSourceScope as Scope,
    PartnershipProfile,
    ResolvedAgreement,
    ResolvedBiddingProfile,
    resolve_partnership_profile,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile


@pytest.fixture
def base():
    return (
        ResolvedAgreement("opening.2d", "natural_weak_two", Resolution.ENABLE, Scope.SYSTEM,
                          (("strength", "weak"),)),
        ResolvedAgreement("response.major.two_over_one", "game_force", Resolution.ENABLE, Scope.SYSTEM),
    )


@pytest.fixture
def nisim_nily():
    replacements = (
        ("opening.2d", "multi_2d"),
        ("opening.2h", "nisim_nily_5h_5minor"),
        ("opening.2s", "nisim_nily_5s_5minor"),
        ("opening.2nt", "nisim_nily_5c_5d"),
    )
    enables = (
        ("opening.three_level.six_minor", "nisim_nily_six_minor_preempt"),
        ("response.major.1nt", "forcing"),
        ("response.major.two_over_one", "game_force"),
        ("response.major.raises", "bergen"),
    )
    return PartnershipProfile(
        "nisim-nily", "1", SystemProfile.TWO_OVER_ONE_GF,
        tuple(AgreementSelection(family, Resolution.REPLACE, treatment) for family, treatment in replacements)
        + tuple(AgreementSelection(family, Resolution.ENABLE, treatment) for family, treatment in enables),
        sources=("test-only:phase29x",),
    )


def test_resolution_enum_is_exact():
    assert {member.name: member.value for member in Resolution} == {
        name: name for name in ("INHERIT", "ENABLE", "DISABLE", "REPLACE")
    }


@pytest.mark.parametrize("resolution,treatment", [
    (Resolution.ENABLE, None), (Resolution.ENABLE, " "),
    (Resolution.REPLACE, None), (Resolution.REPLACE, ""),
    (Resolution.INHERIT, "natural"), (Resolution.DISABLE, "natural"),
])
def test_selection_rejects_invalid_treatment(resolution, treatment):
    with pytest.raises((ValueError, TypeError)):
        AgreementSelection("opening.2d", resolution, treatment)


@pytest.mark.parametrize("family", ["", " \t", None, 3])
def test_selection_rejects_invalid_family(family):
    with pytest.raises((ValueError, TypeError)):
        AgreementSelection(family, Resolution.INHERIT)


def test_selection_rejects_untyped_resolution():
    with pytest.raises(TypeError, match="resolution"):
        AgreementSelection("opening.2d", "ENABLE", "multi_2d")


def test_parameter_normalization_lookup_and_order():
    selection = AgreementSelection(" Opening.2D ", Resolution.ENABLE, " multi_2d ",
                                   ((" Zeta ", " two "), ("ALPHA", "one")))
    assert selection.family == "opening.2d"
    assert selection.treatment_id == "multi_2d"
    assert selection.parameters == (("alpha", "one"), ("zeta", "two"))
    assert selection.option(" ALPHA ") == "one"
    assert selection.option("absent") is None
    assert selection.option("absent", "fallback") == "fallback"


@pytest.mark.parametrize("parameters", [
    (("Key", "1"), (" key ", "2")), ((" ", "1"),),
    (("k", 5),), ((5, "v"),), (("k",),), (("k", "v", "extra"),),
    (["k", "v"],), [("k", "v")], {"k": "v"},
])
def test_parameters_reject_duplicates_blank_keys_and_mutable_or_untyped_values(parameters):
    with pytest.raises((ValueError, TypeError)):
        AgreementSelection("f", Resolution.ENABLE, "t", parameters)


@pytest.mark.parametrize("field,value", [
    ("profile_id", " "), ("version", ""), ("profile_id", None),
    ("base_system", SystemProfile.UNKNOWN), ("base_system", "TWO_OVER_ONE_GF"),
    ("sources", (" ",)), ("sources", (7,)), ("sources", ["source"]),
    ("agreements", []), ("agreements", ("not a selection",)),
])
def test_profile_validation(nisim_nily, field, value):
    with pytest.raises((ValueError, TypeError)):
        replace(nisim_nily, **{field: value})


def test_duplicate_selection_families_rejected(nisim_nily):
    with pytest.raises(ValueError, match="duplicate agreement family"):
        replace(nisim_nily, agreements=(AgreementSelection("opening.2d", Resolution.INHERIT),
                                       AgreementSelection(" OPENING.2D ", Resolution.DISABLE)))


def test_profile_normalization_and_order(nisim_nily):
    profile = replace(nisim_nily, profile_id=" nisim-nily ", version=" 1 ",
                      agreements=tuple(reversed(nisim_nily.agreements)),
                      sources=(" z ", "a", "a"))
    assert profile.profile_id == "nisim-nily"
    assert profile.version == "1"
    assert profile.agreements == nisim_nily.agreements
    assert profile.sources == ("a", "z")


def test_all_domain_values_are_frozen_and_hashable(nisim_nily, base):
    resolved = resolve_partnership_profile(nisim_nily, base_agreements=base)
    for value, field in ((nisim_nily, "version"), (nisim_nily.agreements[0], "family"),
                         (resolved, "version"), (resolved.agreements[0], "family")):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, "changed")
        hash(value)


def test_fixture_identity_and_all_eight_explicit_treatments(nisim_nily, base):
    assert nisim_nily.profile_id == "nisim-nily"
    assert nisim_nily.version == "1"
    assert nisim_nily.base_system is SystemProfile.TWO_OVER_ONE_GF
    resolved = resolve_partnership_profile(nisim_nily, base_agreements=base)
    assert {a.family: a.treatment_id for a in resolved.agreements} == {
        "opening.2d": "multi_2d", "opening.2h": "nisim_nily_5h_5minor",
        "opening.2s": "nisim_nily_5s_5minor", "opening.2nt": "nisim_nily_5c_5d",
        "opening.three_level.six_minor": "nisim_nily_six_minor_preempt",
        "response.major.1nt": "forcing", "response.major.two_over_one": "game_force",
        "response.major.raises": "bergen",
    }
    assert all(a.source_scope is Scope.PARTNERSHIP for a in resolved.agreements)
    assert resolved.agreement("opening.2d").resolution is Resolution.REPLACE


def test_resolution_is_pure_and_partnerships_are_independent(nisim_nily, base):
    original_profile = nisim_nily.to_json()
    original_base = tuple(a.to_dict() for a in base)
    other = PartnershipProfile("another-pair", "1", SystemProfile.TWO_OVER_ONE_GF, ())
    before = resolve_partnership_profile(other, base_agreements=base)
    resolve_partnership_profile(nisim_nily, base_agreements=base)
    after = resolve_partnership_profile(other, base_agreements=base)
    assert before == after
    assert after.agreement("opening.2d").treatment_id == "natural_weak_two"
    assert after.agreement("opening.2d").source_scope is Scope.SYSTEM
    assert after.agreement("opening.2h") is None
    assert after.agreement("response.major.raises") is None
    assert nisim_nily.to_json() == original_profile
    assert tuple(a.to_dict() for a in base) == original_base


def test_inherit_keeps_complete_base_and_missing_family_absent(base):
    profile = PartnershipProfile("pair", "1", SystemProfile.TWO_OVER_ONE_GF, (
        AgreementSelection("opening.2d", Resolution.INHERIT),
        AgreementSelection("missing", Resolution.INHERIT),
    ))
    resolved = resolve_partnership_profile(profile, base_agreements=base)
    assert resolved.agreement("opening.2d") == base[0]
    assert resolved.agreement("opening.2d").option("STRENGTH") == "weak"
    assert resolved.agreement("missing") is None
    assert resolved.agreement("response.major.two_over_one") == base[1]


def test_disable_removes_existing_and_missing_family(base):
    profile = PartnershipProfile("pair", "1", SystemProfile.TWO_OVER_ONE_GF, (
        AgreementSelection("opening.2d", Resolution.DISABLE),
        AgreementSelection("missing", Resolution.DISABLE),
    ))
    resolved = resolve_partnership_profile(profile, base_agreements=base)
    assert resolved.agreement("opening.2d") is None
    assert resolved.agreements == (base[1],)


@pytest.mark.parametrize("resolution", [Resolution.ENABLE, Resolution.REPLACE])
@pytest.mark.parametrize("family", ["opening.2d", "new.family"])
def test_enable_replace_set_complete_treatment_and_parameters(base, resolution, family):
    profile = PartnershipProfile("pair", "1", SystemProfile.TWO_OVER_ONE_GF, (
        AgreementSelection(family, resolution, "explicit", (("MODE", "fixture"),)),
    ))
    resolved = resolve_partnership_profile(profile, base_agreements=base)
    agreement = resolved.agreement(family)
    assert agreement == ResolvedAgreement(family, "explicit", resolution, Scope.PARTNERSHIP,
                                          (("mode", "fixture"),))
    assert agreement.option("strength") is None


def test_no_base_defaults_or_automatic_capabilities(nisim_nily):
    empty = PartnershipProfile("empty", "1", SystemProfile.SAYC, ())
    assert resolve_partnership_profile(empty).agreements == ()
    assert resolve_partnership_profile(nisim_nily).capabilities == ()
    result = resolve_partnership_profile(empty, base_capabilities=(" z ", "a", "a"))
    assert result.capabilities == ("a", "z")


def test_duplicate_base_families_rejected(nisim_nily, base):
    duplicate = ResolvedAgreement(" OPENING.2D ", "other", Resolution.ENABLE, Scope.SYSTEM)
    with pytest.raises(ValueError, match="duplicate agreement family"):
        resolve_partnership_profile(nisim_nily, base_agreements=base + (duplicate,))


@pytest.mark.parametrize("kwargs", [
    {"base_agreements": []}, {"base_agreements": ("bad",)},
    {"base_capabilities": ["mutable"]}, {"base_capabilities": ("",)},
    {"base_capabilities": (1,)},
])
def test_resolver_rejects_invalid_inputs(nisim_nily, kwargs):
    with pytest.raises((ValueError, TypeError)):
        resolve_partnership_profile(nisim_nily, **kwargs)


def test_resolver_requires_typed_profile():
    with pytest.raises(TypeError, match="PartnershipProfile"):
        resolve_partnership_profile(None)


@pytest.mark.parametrize("field,value", [
    ("family", ""), ("treatment_id", " "), ("resolution", "ENABLE"),
    ("source_scope", "SYSTEM"), ("parameters", (("K", "1"), ("k", "2"))),
])
def test_resolved_agreement_validation(base, field, value):
    with pytest.raises((ValueError, TypeError)):
        replace(base[0], **{field: value})


def test_resolved_profile_validation(nisim_nily, base):
    resolved = resolve_partnership_profile(nisim_nily, base_agreements=base)
    for kwargs in ({"agreements": base + (base[0],)}, {"agreements": list(base)},
                   {"base_system": SystemProfile.UNKNOWN}, {"sources": (" ",)},
                   {"agreements": nisim_nily.agreements}, {"capabilities": (" ",)}):
        with pytest.raises((ValueError, TypeError)):
            replace(resolved, **kwargs)


def test_lookup_and_serialization_are_deterministic_detached_values(nisim_nily, base):
    one = resolve_partnership_profile(nisim_nily, base_agreements=base, base_capabilities=("z", "a"))
    two = resolve_partnership_profile(replace(nisim_nily, agreements=tuple(reversed(nisim_nily.agreements))),
                                      base_agreements=tuple(reversed(base)), base_capabilities=("a", "z"))
    assert one == two
    assert one.to_json() == two.to_json()
    assert one.agreement(" OPENING.2D ") == one.agreement("opening.2d")
    assert one.agreement("absent") is None
    for value in (nisim_nily, one):
        data = value.to_dict()
        assert json.loads(value.to_json()) == data
        assert value.to_json() == json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        assert data["base_system"] == "TWO_OVER_ONE_GF"
        original = value.to_json()
        data["sources"].append("changed")
        data["agreements"][0]["parameters"].append(["changed", "value"])
        assert value.to_json() == original


def test_resolution_leaves_production_routes_contexts_and_behavior_unchanged(nisim_nily, base):
    before = create_standard_sayc_router()
    contexts = tuple(BiddingContext.create(
        hand=Hand.parse(hand), auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.EW, system=system,
    ) for hand, calls in (("7.84.KQJT96.9742", ()),
                           ("7.84.KQJT96.9742", ("P", "P")),
                           ("AKQ.JT9.AQ2.KJ32", ()),
                           ("AKJ32.QT9.K32.87", ("1H", "P")))
        for system in (SystemContext("SAYC"),
                       SystemContext.from_mapping("SAYC", {"partnership_profile": "nisim-nily"}),
                       SystemContext.from_mapping("TWO_OVER_ONE_GF", {"two_over_one": "game_force"})))
    expected = tuple(before.evaluate(context) for context in contexts)
    route_ids = tuple(route.route_id for route in before.routes)
    system_fields = fields(SystemContext)
    bidding_fields = fields(BiddingContext)
    resolve_partnership_profile(nisim_nily, base_agreements=base)
    after = create_standard_sayc_router()
    assert len(before.routes) == len(after.routes) == 45
    assert tuple(route.route_id for route in after.routes) == route_ids
    assert not any("nisim" in name.casefold() for name in route_ids)
    assert tuple(before.evaluate(context) for context in contexts) == expected
    assert tuple(after.evaluate(context) for context in contexts) == expected
    assert expected[0].recommended_call.serialize() == "2D"
    assert expected[3].recommended_call is None
    assert fields(SystemContext) == system_fields
    assert fields(BiddingContext) == bidding_fields
    assert tuple(f.name for f in system_fields) == ("system", "options")
    assert tuple(f.name for f in bidding_fields) == ("hand", "evaluation", "auction", "seat", "vulnerability", "system")
    audit = build_six_minor_production_adoption_audit()
    assert audit.production_changed is False
    assert audit.ready_for_production is False
    assert audit.route_count == 45
