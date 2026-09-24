"""Phase 30A semantic plan validation without production route binding."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
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
    ResolvedBiddingProfile,
    resolve_partnership_profile,
)
from bridge.profile_compiler import (
    CompilationAction,
    CompiledAgreementDirective,
    CompiledProfilePlan,
    compile_profile_plan,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile


@pytest.fixture
def base_agreements():
    # Small comparison fixture; it does not claim to define the complete 2/1 system.
    return (
        ResolvedAgreement("opening.2d", "natural_weak_two", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2h", "natural_weak_two", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2s", "natural_weak_two", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.2nt", "natural_2nt", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("response.major.two_over_one", "game_force", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("response.major.raises", "traditional", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("opening.1nt", "standard_15_17", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
    )


@pytest.fixture
def compiled(base_agreements):
    resolved = resolve_partnership_profile(
        NISIM_NILY_PROFILE,
        base_agreements=base_agreements,
        base_capabilities=("explicit_base_capability",),
    )
    return compile_profile_plan(resolved, base_agreements=base_agreements)


def _directive(action, base=None, effective=None, base_parameters=(), effective_parameters=(),
               scope=AgreementSourceScope.PARTNERSHIP, resolution=AgreementResolution.ENABLE):
    return CompiledAgreementDirective(
        "test.family", action, base, effective,
        base_parameters, effective_parameters,
        scope if effective is not None else None,
        resolution if effective is not None else None,
    )


def test_compilation_actions_are_exact_and_distinct_from_resolution():
    assert {item.value for item in CompilationAction} == {"KEEP", "ADD", "REMOVE", "REPLACE"}
    assert all(not isinstance(item, AgreementResolution) for item in CompilationAction)


@pytest.mark.parametrize("action,base,effective", [
    (CompilationAction.KEEP, None, "t"),
    (CompilationAction.KEEP, "a", "b"),
    (CompilationAction.ADD, "a", "b"),
    (CompilationAction.ADD, None, None),
    (CompilationAction.REMOVE, None, None),
    (CompilationAction.REMOVE, "a", "b"),
    (CompilationAction.REPLACE, None, "b"),
    (CompilationAction.REPLACE, "a", None),
    (CompilationAction.REPLACE, "a", "a"),
])
def test_directive_rejects_inconsistent_action(action, base, effective):
    with pytest.raises(ValueError, match="invalid"):
        _directive(action, base, effective)


@pytest.mark.parametrize("family", ("", "  ", None))
def test_directive_rejects_blank_or_untyped_family(family):
    with pytest.raises((ValueError, TypeError)):
        replace(_directive(CompilationAction.ADD, effective="t"), family=family)


def test_directive_rejects_untyped_action_or_provenance():
    good = _directive(CompilationAction.ADD, effective="t")
    with pytest.raises(TypeError):
        replace(good, action="ADD")
    with pytest.raises(TypeError):
        replace(good, effective_source_scope="PARTNERSHIP")
    with pytest.raises(TypeError):
        replace(good, effective_resolution="ENABLE")
    with pytest.raises(ValueError):
        replace(good, effective_treatment_id=None)


def test_parameters_are_canonical_immutable_and_part_of_signature():
    directive = _directive(
        CompilationAction.KEEP, "same", "same",
        (("B", " 2 "), ("a", "1")), (("A", "1"), ("b", "2")),
    )
    assert directive.base_parameters == directive.effective_parameters == (("a", "1"), ("b", "2"))
    assert directive.family == "test.family"
    with pytest.raises(FrozenInstanceError):
        directive.action = CompilationAction.REPLACE
    changed = _directive(CompilationAction.REPLACE, "same", "same",
                         (("range", "old"),), (("range", "new"),))
    assert changed.action is CompilationAction.REPLACE
    with pytest.raises(ValueError):
        _directive(CompilationAction.KEEP, "same", "same",
                   (("range", "old"),), (("range", "new"),))


@pytest.mark.parametrize("directive,kwargs", [
    (_directive(CompilationAction.ADD, effective="new"),
     {"base_parameters": (("a", "1"),)}),
    (_directive(CompilationAction.REMOVE, base="old"),
     {"effective_parameters": (("a", "1"),)}),
    (_directive(CompilationAction.REMOVE, base="old"),
     {"base_parameters": (("A", "1"), ("a", "2"))}),
    (_directive(CompilationAction.REMOVE, base="old"),
     {"base_parameters": [("a", "1")]}),
])
def test_directive_rejects_absent_or_invalid_parameter_data(directive, kwargs):
    with pytest.raises((ValueError, TypeError)):
        replace(directive, **kwargs)


def test_nisim_nily_compilation_inventory_and_provenance(compiled):
    assert compiled.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert compiled.profile_id == "nisim-nily"
    assert compiled.profile_version == NISIM_NILY_PROFILE.version
    assert compiled.compiler_version == "30A.1"
    assert compiled.production_adopted is False
    assert compiled.capabilities == ("explicit_base_capability",)
    assert compiled.sources == NISIM_NILY_PROFILE.sources
    assert {item.family: item.action for item in compiled.directives} == {
        "opening.1nt": CompilationAction.KEEP,
        "opening.2d": CompilationAction.REPLACE,
        "opening.2h": CompilationAction.REPLACE,
        "opening.2s": CompilationAction.REPLACE,
        "opening.2nt": CompilationAction.REPLACE,
        "opening.three_level.six_minor": CompilationAction.ADD,
        "response.major.1nt": CompilationAction.ADD,
        "response.major.raises": CompilationAction.REPLACE,
        "response.major.two_over_one": CompilationAction.KEEP,
    }
    assert compiled.directive(" OPENING.2D ").base_treatment_id == "natural_weak_two"
    assert compiled.directive("opening.2d").effective_treatment_id == "multi_2d"
    assert compiled.directive("response.major.raises").effective_treatment_id == "bergen"
    assert compiled.directive("response.major.two_over_one").effective_treatment_id == "game_force"
    assert compiled.directive("opening.1nt").effective_source_scope is AgreementSourceScope.SYSTEM
    assert compiled.directive("response.major.two_over_one").effective_resolution is AgreementResolution.ENABLE
    assert compiled.directive("missing") is None


def test_remove_is_derived_from_synthetic_disable():
    base = (ResolvedAgreement("test.family.enabled", "base_treatment",
                              AgreementResolution.ENABLE, AgreementSourceScope.SYSTEM),)
    profile = PartnershipProfile("test-only-remove", "1", SystemProfile.SAYC, (
        AgreementSelection("test.family.enabled", AgreementResolution.DISABLE),
    ))
    resolved = resolve_partnership_profile(profile, base_agreements=base)
    assert resolved.agreement("test.family.enabled") is None
    plan = compile_profile_plan(resolved, base_agreements=base)
    directive = plan.directive("test.family.enabled")
    assert directive.action is CompilationAction.REMOVE
    assert directive.base_treatment_id == "base_treatment"
    assert directive.effective_treatment_id is None
    assert directive.effective_source_scope is None
    assert directive.effective_resolution is None


def test_parameter_only_change_replaces_but_provenance_only_change_keeps():
    base = (ResolvedAgreement("test.range", "opaque", AgreementResolution.INHERIT,
                              AgreementSourceScope.SYSTEM, (("value", "old"),)),)
    changed = PartnershipProfile("test-parameter", "1", SystemProfile.SAYC, (
        AgreementSelection("test.range", AgreementResolution.ENABLE, "opaque", (("value", "new"),)),
    ))
    same = PartnershipProfile("test-provenance", "1", SystemProfile.SAYC, (
        AgreementSelection("test.range", AgreementResolution.REPLACE, "opaque", (("value", "old"),)),
    ))
    changed_plan = compile_profile_plan(resolve_partnership_profile(changed, base_agreements=base),
                                        base_agreements=base)
    same_plan = compile_profile_plan(resolve_partnership_profile(same, base_agreements=base),
                                     base_agreements=base)
    assert changed_plan.directive("test.range").action is CompilationAction.REPLACE
    assert changed_plan.directive("test.range").base_treatment_id == "opaque"
    assert changed_plan.directive("test.range").effective_treatment_id == "opaque"
    assert same_plan.directive("test.range").action is CompilationAction.KEEP
    assert same_plan.directive("test.range").effective_source_scope is AgreementSourceScope.PARTNERSHIP
    assert same_plan.directive("test.range").effective_resolution is AgreementResolution.REPLACE


def test_compiler_rejects_duplicate_base_families_case_insensitively(base_agreements):
    resolved = resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements)
    duplicate = ResolvedAgreement(" OPENING.2D ", "another", AgreementResolution.ENABLE,
                                  AgreementSourceScope.SYSTEM)
    with pytest.raises(ValueError, match="duplicate base"):
        compile_profile_plan(resolved, base_agreements=base_agreements + (duplicate,))


@pytest.mark.parametrize("bad_base", [
    [], ("not an agreement",),
    (ResolvedAgreement("test.family", None, AgreementResolution.INHERIT,
                       AgreementSourceScope.SYSTEM),),
])
def test_compiler_rejects_ambiguous_base_inputs(bad_base):
    resolved = resolve_partnership_profile(PartnershipProfile("test", "1", SystemProfile.SAYC, ()))
    with pytest.raises((TypeError, ValueError)):
        compile_profile_plan(resolved, base_agreements=bad_base)


def test_compiler_rejects_missing_effective_treatment():
    resolved = ResolvedBiddingProfile(
        "test", "1", SystemProfile.SAYC,
        (ResolvedAgreement("test.family", None, AgreementResolution.INHERIT,
                           AgreementSourceScope.SYSTEM),),
    )
    with pytest.raises(ValueError, match="effective agreement lacks treatment"):
        compile_profile_plan(resolved)


def test_compiler_determinism_order_and_nonmutation(base_agreements):
    profile_before = NISIM_NILY_PROFILE.to_json()
    base_before = tuple(agreement.to_dict() for agreement in base_agreements)
    resolved = resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements,
                                           base_capabilities=("base_b", "base_a"))
    resolved_before = resolved.to_json()
    first = compile_profile_plan(resolved, base_agreements=base_agreements)
    second = compile_profile_plan(resolved, base_agreements=tuple(reversed(base_agreements)))
    third = compile_profile_plan(resolved, base_agreements=base_agreements)
    assert first == second == third
    assert first.to_json() == second.to_json() == third.to_json()
    assert first.to_dict() == second.to_dict() == third.to_dict()
    assert first.capabilities == resolved.capabilities == ("base_a", "base_b")
    assert NISIM_NILY_PROFILE.to_json() == profile_before
    assert tuple(agreement.to_dict() for agreement in base_agreements) == base_before
    assert resolved.to_json() == resolved_before


def test_plan_validation_frozen_lookup_and_serialization(compiled):
    assert tuple(item.family for item in compiled.directives) == tuple(sorted(
        item.family for item in compiled.directives
    ))
    assert json.loads(compiled.to_json()) == compiled.to_dict()
    assert compiled.to_json() == json.dumps(compiled.to_dict(), ensure_ascii=False,
                                            sort_keys=True, separators=(",", ":"))
    assert compiled.directive("RESPONSE.MAJOR.1NT").action is CompilationAction.ADD
    with pytest.raises(FrozenInstanceError):
        compiled.production_adopted = True
    with pytest.raises(ValueError, match="duplicate directive"):
        replace(compiled, directives=compiled.directives + (compiled.directives[0],))
    with pytest.raises(ValueError, match="cannot be adopted"):
        replace(compiled, production_adopted=True)
    detached = compiled.to_dict()
    detached["directives"].clear()
    detached["capabilities"].append("unexpected")
    assert len(compiled.directives) == 9
    assert compiled.capabilities == ("explicit_base_capability",)


def test_compiled_output_has_only_data_and_compiler_imports_no_router(compiled):
    import bridge.profile_compiler as module

    imports = set()
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    assert not any("router" in name or "engine" in name for name in imports if name)
    assert not any("registry" in name for name in imports if name)
    assert all(not callable(getattr(directive, field.name))
               for directive in compiled.directives for field in fields(directive))
    assert all(not callable(getattr(compiled, field.name)) for field in fields(compiled))
    serialized = compiled.to_json()
    assert "EngineRoute" not in serialized
    assert "matcher" not in serialized
    assert "engine" not in serialized.casefold()
    assert "router" not in serialized.casefold()


def test_compilation_leaves_router_contexts_and_policy_audits_unchanged(base_agreements):
    before = create_standard_sayc_router()
    ids_before = tuple(route.route_id for route in before.routes)
    context = BiddingContext.create(
        hand=Hand.parse("7.84.KQJT96.9742"), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW, system=SystemContext("SAYC"),
    )
    decision_before = before.evaluate(context)
    resolved = resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements)
    plan = compile_profile_plan(resolved, base_agreements=base_agreements)
    after = create_standard_sayc_router()
    ids_after = tuple(route.route_id for route in after.routes)
    assert len(ids_before) == len(ids_after) == 45
    assert ids_after == ids_before
    assert not any("nisim" in name.casefold() or "30a" in name.casefold() for name in ids_after)
    assert after.evaluate(context) == decision_before
    assert decision_before.recommended_call.serialize() == "2D"
    assert plan.production_adopted is False
    assert tuple(field.name for field in fields(SystemContext)) == ("system", "options")
    assert tuple(field.name for field in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )
    hand = Hand.parse("7.84.KQJT96.9742")
    assert assess_six_minor_three_level_preempt(
        hand, seat=Seat.SOUTH, vulnerability=Vulnerability.EW, opening_position=3
    ).production_adopted is False
    assert assess_opening_policy_with_six_minor(
        hand, auction=Auction(Seat.NORTH, ("P", "P")), vulnerability=Vulnerability.EW
    ).production_adopted is False
    audit = build_six_minor_production_adoption_audit()
    assert audit.production_changed is False
    assert audit.ready_for_production is False


def test_second_partnership_still_receives_no_nisim_nily_treatments(base_agreements):
    other = PartnershipProfile("isolation-partnership-b", "30A.test", SystemProfile.TWO_OVER_ONE_GF, (
        AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE, "game_force"),
    ))
    resolved = resolve_partnership_profile(other, base_agreements=base_agreements)
    plan = compile_profile_plan(resolved, base_agreements=base_agreements)
    assert plan.profile_id == other.profile_id
    assert plan.directive("opening.2d").action is CompilationAction.KEEP
    assert plan.directive("opening.2d").effective_treatment_id == "natural_weak_two"
    assert plan.directive("response.major.raises").effective_treatment_id == "traditional"
    assert plan.directive("response.major.1nt") is None
    assert plan.directive("opening.three_level.six_minor") is None
    forbidden = {"multi_2d", "nisim_nily_5h_5minor", "nisim_nily_5s_5minor",
                 "nisim_nily_5c_5d", "nisim_nily_six_minor_preempt", "bergen", "forcing"}
    assert forbidden.isdisjoint(item.effective_treatment_id for item in plan.directives)
