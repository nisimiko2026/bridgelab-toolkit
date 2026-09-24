"""Phase 30B: one exact shadow binding, with production and profile isolation."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.nisim_nily_six_minor_preempt_policy import (
    SixMinorDecision,
    SixMinorPreemptAssessment,
    assess_six_minor_three_level_preempt,
)
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
from bridge.profile_compiler import (
    CompilationAction,
    CompiledAgreementDirective,
    compile_profile_plan,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.treatment_bindings import (
    NISIM_NILY_SIX_MINOR_BINDING,
    TreatmentImplementationBinding,
    TreatmentImplementationKind,
    bind_compiled_directive,
    evaluate_bound_treatment,
    get_treatment_binding,
)


FAMILY = "opening.three_level.six_minor"
TREATMENT = "nisim_nily_six_minor_preempt"


@pytest.fixture
def base_agreements():
    # Deliberately small resolver fixture, not an authoritative 2/1 card.
    return (
        ResolvedAgreement("opening.2d", "natural_weak_two", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("response.major.raises", "traditional", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
        ResolvedAgreement("response.major.two_over_one", "game_force", AgreementResolution.ENABLE,
                          AgreementSourceScope.SYSTEM),
    )


@pytest.fixture
def chain(base_agreements):
    resolved = resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements)
    plan = compile_profile_plan(resolved, base_agreements=base_agreements)
    return resolved, plan, plan.directive(FAMILY)


def _directive(action, base=None, effective=TREATMENT, family=FAMILY, parameters=()):
    return CompiledAgreementDirective(
        family=family,
        action=action,
        base_treatment_id=base,
        effective_treatment_id=effective,
        effective_parameters=parameters,
        effective_source_scope=None if effective is None else AgreementSourceScope.PARTNERSHIP,
        effective_resolution=None if effective is None else AgreementResolution.ENABLE,
    )


def test_binding_metadata_is_typed_frozen_and_versioned_from_phase29t():
    binding = NISIM_NILY_SIX_MINOR_BINDING
    assert tuple(member.value for member in TreatmentImplementationKind) == ("POLICY_ASSESSOR",)
    assert isinstance(binding, TreatmentImplementationBinding)
    assert binding.family == FAMILY
    assert binding.treatment_id == TREATMENT
    assert binding.implementation_id == "nisim-nily.six-minor-preempt"
    assert binding.implementation_kind is TreatmentImplementationKind.POLICY_ASSESSOR
    assert binding.implementation_version == SixMinorPreemptAssessment.__dataclass_fields__["policy_version"].default
    assert binding.implementation_version == "nisim-nily.six-minor-preempt@29T.1"
    assert binding.production_adopted is False
    with pytest.raises(FrozenInstanceError):
        binding.treatment_id = "other"
    with pytest.raises(ValueError, match="cannot be adopted"):
        replace(binding, production_adopted=True)


@pytest.mark.parametrize("field,value", [
    ("family", " "), ("treatment_id", ""), ("implementation_id", "  "),
    ("implementation_version", None), ("implementation_kind", "POLICY_ASSESSOR"),
])
def test_binding_rejects_invalid_metadata(field, value):
    with pytest.raises((ValueError, TypeError)):
        replace(NISIM_NILY_SIX_MINOR_BINDING, **{field: value})


def test_serialization_contains_stable_metadata_only():
    binding = NISIM_NILY_SIX_MINOR_BINDING
    assert binding.to_json() == binding.to_json()
    assert json.loads(binding.to_json()) == binding.to_dict()
    assert binding.to_json() == json.dumps(binding.to_dict(), ensure_ascii=False,
                                            sort_keys=True, separators=(",", ":"))
    assert binding.to_dict() == {
        "family": FAMILY,
        "treatment_id": TREATMENT,
        "implementation_id": "nisim-nily.six-minor-preempt",
        "implementation_kind": "POLICY_ASSESSOR",
        "implementation_version": "nisim-nily.six-minor-preempt@29T.1",
        "production_adopted": False,
    }


@pytest.mark.parametrize("family,treatment,expected", [
    (FAMILY, TREATMENT, True),
    (FAMILY.upper(), TREATMENT, True),
    ("opening.2d", TREATMENT, False),
    (FAMILY, "multi_2d", False),
    (FAMILY, "nisim_nily_six_minor", False),
    (FAMILY, "nisim_nily_six_minor_preempt_extra", False),
    (FAMILY, TREATMENT.upper(), False),
    (" ", TREATMENT, False),
    (FAMILY, " ", False),
])
def test_exact_lookup_has_no_aliases_or_fallback(family, treatment, expected):
    result = get_treatment_binding(family=family, treatment_id=treatment)
    assert (result is NISIM_NILY_SIX_MINOR_BINDING) is expected


def test_lookup_and_binding_do_not_depend_on_profile_identity(chain):
    _, plan, directive = chain
    assert not hasattr(directive, "profile_id")
    assert bind_compiled_directive(directive) is NISIM_NILY_SIX_MINOR_BINDING
    assert get_treatment_binding(family=directive.family,
                                 treatment_id=directive.effective_treatment_id) is NISIM_NILY_SIX_MINOR_BINDING
    # Only the family/effective treatment pair is passed to lookup; plan identity
    # and the TWO_OVER_ONE_GF system are not arguments to either binding API.
    assert plan.profile_id == "nisim-nily"


def test_compiled_directive_actions_bind_effective_treatments_only(chain):
    _, _, added = chain
    assert added.action is CompilationAction.ADD
    assert added.effective_treatment_id == TREATMENT
    assert bind_compiled_directive(added) is NISIM_NILY_SIX_MINOR_BINDING
    kept = _directive(CompilationAction.KEEP, base=TREATMENT)
    replaced = _directive(CompilationAction.REPLACE, base="other_treatment")
    removed = _directive(CompilationAction.REMOVE, base=TREATMENT, effective=None)
    unrelated = _directive(CompilationAction.REPLACE, base="old", effective="other")
    assert bind_compiled_directive(kept) is NISIM_NILY_SIX_MINOR_BINDING
    assert bind_compiled_directive(replaced) is NISIM_NILY_SIX_MINOR_BINDING
    assert bind_compiled_directive(removed) is None
    assert bind_compiled_directive(unrelated) is None
    assert bind_compiled_directive(_directive(CompilationAction.ADD, family="other.family")) is None
    # The pilot policy has no parameter input; never silently discard one.
    assert bind_compiled_directive(_directive(
        CompilationAction.ADD, parameters=(("unsupported", "value"),)
    )) is None


def test_profile_resolve_compile_bind_chain_is_pure(chain, base_agreements):
    resolved, plan, directive = chain
    profile_before = NISIM_NILY_PROFILE.to_json()
    resolved_before = resolved.to_json()
    plan_before = plan.to_json()
    directive_before = directive.to_dict()
    base_before = tuple(agreement.to_dict() for agreement in base_agreements)
    binding = bind_compiled_directive(directive)
    assert binding is NISIM_NILY_SIX_MINOR_BINDING
    assert binding.production_adopted is False
    assert NISIM_NILY_PROFILE.to_json() == profile_before
    assert resolved.to_json() == resolved_before
    assert plan.to_json() == plan_before == compile_profile_plan(
        resolved, base_agreements=tuple(reversed(base_agreements))
    ).to_json()
    assert directive.to_dict() == directive_before
    assert tuple(agreement.to_dict() for agreement in base_agreements) == base_before


def test_second_partnership_same_system_does_not_activate_available_binding(base_agreements):
    other = PartnershipProfile("isolation-partnership-b", "30B.test", SystemProfile.TWO_OVER_ONE_GF, (
        AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE, "game_force"),
    ))
    resolved = resolve_partnership_profile(other, base_agreements=base_agreements)
    plan = compile_profile_plan(resolved, base_agreements=base_agreements)
    assert get_treatment_binding(family=FAMILY, treatment_id=TREATMENT) is NISIM_NILY_SIX_MINOR_BINDING
    assert resolved.agreement(FAMILY) is None
    assert plan.directive(FAMILY) is None
    assert all(bind_compiled_directive(directive) is None for directive in plan.directives)
    assert plan.profile_id == "isolation-partnership-b"


@pytest.mark.parametrize("hand_text,seat,vulnerability,position,decision,call", [
    ("7.84.KQJT96.9742", Seat.SOUTH, Vulnerability.EW, 3, SixMinorDecision.THREE_LEVEL, "3D"),
    ("7.K4.KQJT96.A742", Seat.NORTH, Vulnerability.NONE, 1, SixMinorDecision.ONE_LEVEL, "1D"),
    ("7.84.KJ9864.9742", Seat.SOUTH, Vulnerability.EW, 3, SixMinorDecision.NO_THREE_LEVEL, None),
    ("7.84.KQJT976.974", Seat.NORTH, Vulnerability.NONE, 1, SixMinorDecision.NOT_APPLICABLE, None),
])
def test_direct_and_bound_phase29t_assessments_are_identical(
    hand_text, seat, vulnerability, position, decision, call, chain
):
    _, plan, directive = chain
    hand = Hand.parse(hand_text)
    hand_before = hand.serialize()
    binding = bind_compiled_directive(directive)
    profile_before = NISIM_NILY_PROFILE.to_json()
    plan_before = plan.to_json()
    directive_before = directive.to_dict()
    binding_before = binding.to_json()
    kwargs = {"hand": hand, "seat": seat, "vulnerability": vulnerability, "opening_position": position}
    direct = assess_six_minor_three_level_preempt(**kwargs)
    bound = evaluate_bound_treatment(binding, **kwargs)
    assert isinstance(bound, SixMinorPreemptAssessment)
    assert bound == direct
    assert bound.decision is decision
    assert bound.preferred_call == call
    assert bound.production_adopted is False
    assert evaluate_bound_treatment(binding, **kwargs) == bound
    assert hand.serialize() == hand_before
    assert binding.to_json() == binding_before
    assert directive.to_dict() == directive_before
    assert plan.to_json() == plan_before
    assert NISIM_NILY_PROFILE.to_json() == profile_before


def test_unsupported_binding_is_rejected_before_assessor_call(monkeypatch):
    def forbidden(**kwargs):
        raise AssertionError("unsupported binding invoked Phase 29T")

    monkeypatch.setattr("bridge.treatment_bindings.assess_six_minor_three_level_preempt", forbidden)
    changed = replace(NISIM_NILY_SIX_MINOR_BINDING, implementation_version="other-version")
    with pytest.raises(ValueError, match="unsupported"):
        evaluate_bound_treatment(changed, hand=Hand.parse("7.84.KQJT96.9742"),
                                 seat=Seat.SOUTH, vulnerability=Vulnerability.EW,
                                 opening_position=3)
    with pytest.raises(TypeError, match="TreatmentImplementationBinding"):
        evaluate_bound_treatment(None, hand=Hand.parse("7.84.KQJT96.9742"),
                                 seat=Seat.SOUTH, vulnerability=Vulnerability.EW,
                                 opening_position=3)


def test_binding_module_has_no_router_engine_or_dynamic_registry():
    import bridge.treatment_bindings as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    imports = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    assert not any("router" in name or "engine" in name or "registry" in name
                   for name in imports if name)
    assert "importlib" not in imports
    assert "EngineRoute(" not in source
    assert "BiddingEngine(" not in source
    assert "BiddingEngineResult(" not in source
    assert "RuleDecision(" not in source
    assert not any(callable(getattr(NISIM_NILY_SIX_MINOR_BINDING, field.name))
                   for field in fields(NISIM_NILY_SIX_MINOR_BINDING))


def test_shadow_binding_does_not_change_production_route_inventory_or_audits(chain):
    before = create_standard_sayc_router()
    before_ids = tuple(route.route_id for route in before.routes)
    context = BiddingContext.create(
        hand=Hand.parse("7.84.KQJT96.9742"), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW, system=SystemContext("SAYC"),
    )
    decision_before = before.evaluate(context)
    binding = bind_compiled_directive(chain[2])
    evaluate_bound_treatment(binding, hand=context.hand, seat=Seat.SOUTH,
                             vulnerability=Vulnerability.EW, opening_position=3)
    after = create_standard_sayc_router()
    after_ids = tuple(route.route_id for route in after.routes)
    assert len(before_ids) == len(after_ids) == 45
    assert before_ids == after_ids
    assert not any("nisim" in route_id.casefold() or "30b" in route_id.casefold()
                   for route_id in after_ids)
    assert after.evaluate(context) == decision_before
    assert decision_before.recommended_call.serialize() == "2D"
    assert tuple(field.name for field in fields(SystemContext)) == ("system", "options")
    assert tuple(field.name for field in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )
    historical_hand = Hand.parse("7.84.KQJT96.9742")
    assert assess_six_minor_three_level_preempt(
        historical_hand, seat=Seat.SOUTH, vulnerability=Vulnerability.EW,
        opening_position=3,
    ).production_adopted is False
    assert assess_opening_policy_with_six_minor(
        historical_hand, auction=Auction(Seat.NORTH, ("P", "P")),
        vulnerability=Vulnerability.EW,
    ).production_adopted is False
    audit = build_six_minor_production_adoption_audit()
    assert audit.production_changed is False
    assert audit.ready_for_production is False
