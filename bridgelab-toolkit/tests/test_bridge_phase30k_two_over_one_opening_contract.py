"""Phase 30K typed 2/1 base-opening source contract, without execution."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.partnership_profiles import resolve_partnership_profile
from bridge.profile_compiler import compile_profile_plan
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.two_over_one_opening_contract import (
    OpeningContractEvidence as E,
    TwoOverOneOpeningContract, TwoOverOneOpeningFamilyContract,
    TwoOverOneOpeningContractCapability, build_two_over_one_opening_contract,
    capability_for_two_over_one_opening_contract,
)
from bridge.two_over_one_opening_execution_boundary import (
    OpeningExecutionBoundaryState,
    audit_two_over_one_opening_execution_boundary,
)


FAMILIES = {"opening.1c", "opening.1d", "opening.1h", "opening.1s", "opening.1nt"}
BINDINGS = {
    "one_level_strength_policy", "minor_length_policy", "minor_selection_precedence",
    "equal_minor_precedence", "five_five_major_precedence", "one_notrump_range",
    "one_notrump_five_card_major_policy", "one_notrump_shape_policy",
    "suit_vs_notrump_precedence", "strong_hand_precedence",
}


@pytest.fixture(scope="module")
def contract():
    return build_two_over_one_opening_contract()


def test_evidence_enum_scope_immutability_and_determinism(contract):
    assert tuple(item.value for item in E) == (
        "EXPLICIT", "TYPICAL", "APPROXIMATE", "VARIABLE", "UNSPECIFIED")
    assert isinstance(contract, TwoOverOneOpeningContract)
    assert contract.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert len(contract.families) == 5
    assert {family.family for family in contract.families} == FAMILIES
    assert tuple(family.family for family in contract.families) == tuple(sorted(FAMILIES))
    assert all(isinstance(family, TwoOverOneOpeningFamilyContract) for family in contract.families)
    assert all(family.source_article == "bidding/systems/2-over-1"
               and family.source_headings for family in contract.families)
    assert all(not family.executable and not family.production_adopted for family in contract.families)
    assert json.loads(contract.to_json()) == contract.to_dict()
    assert contract.to_json() == build_two_over_one_opening_contract().to_json()
    assert all(json.loads(family.to_json()) == family.to_dict() for family in contract.families)
    with pytest.raises(FrozenInstanceError):
        contract.ready_for_execution = True
    with pytest.raises(FrozenInstanceError):
        contract.families[0].minimum_length = 1
    with pytest.raises(ValueError, match="exactly the five"):
        replace(contract, families=contract.families[:-1])
    with pytest.raises(ValueError, match="declarative"):
        replace(contract.families[0], executable=True)


def test_natural_minor_contracts_preserve_typical_lengths(contract):
    club = contract.family("opening.1c")
    diamond = contract.family("opening.1d")
    for family, minimum in ((club, 3), (diamond, 4)):
        assert family.natural is True
        assert family.natural_evidence is E.EXPLICIT
        assert family.minimum_length == minimum
        assert family.minimum_length_evidence is E.TYPICAL
        assert family.minimum_length_evidence is not E.EXPLICIT
        assert family.hcp_min is family.hcp_max is None
        assert family.strength_evidence is E.UNSPECIFIED
        assert not family.executable
        assert {"minor_length_policy", "minor_selection_precedence",
                "equal_minor_precedence"} <= set(family.required_bindings)
    assert club.source_headings == tuple(sorted(("System Requirements", "Opening Requirements / 1♣")))
    assert diamond.source_headings == tuple(sorted(("System Requirements", "Opening Requirements / 1♦")))


@pytest.mark.parametrize("family", ("opening.1h", "opening.1s"))
def test_major_contracts_record_explicit_length_and_approximate_strength(contract, family):
    major = contract.family(family)
    assert major.natural is True and major.natural_evidence is E.EXPLICIT
    assert major.minimum_length == 5
    assert major.minimum_length_evidence is E.EXPLICIT
    assert (major.hcp_min, major.hcp_max) == (12, 21)
    assert major.strength_evidence is E.APPROXIMATE
    assert not major.executable
    assert {"one_level_strength_policy", "five_five_major_precedence",
            "suit_vs_notrump_precedence", "strong_hand_precedence"} <= set(major.required_bindings)


def test_notrump_candidates_are_variable_not_a_selected_universal_range(contract):
    nt = contract.family("opening.1nt")
    assert nt.balanced_required is True
    assert nt.balanced_evidence is E.TYPICAL
    assert nt.candidate_notrump_ranges == ((15, 17), (14, 16), (16, 18))
    assert nt.strength_evidence is E.VARIABLE
    assert nt.hcp_min is nt.hcp_max is None
    assert nt.minimum_length is None
    assert nt.natural is None and nt.natural_evidence is E.UNSPECIFIED
    assert not nt.executable
    assert {"one_notrump_range", "one_notrump_five_card_major_policy",
            "one_notrump_shape_policy", "suit_vs_notrump_precedence"} <= set(nt.required_bindings)
    with pytest.raises(ValueError, match="not a selected universal"):
        replace(nt, hcp_min=15, hcp_max=17)
    with pytest.raises(ValueError, match="VARIABLE"):
        replace(nt, strength_evidence=E.EXPLICIT)


def test_unresolved_bindings_and_recommendation_are_derived(contract):
    assert set(contract.required_bindings) == BINDINGS
    assert contract.required_bindings == tuple(sorted(
        {binding for family in contract.families for binding in family.required_bindings}))
    assert contract.all_required_bindings_resolved is (not contract.required_bindings)
    assert contract.all_required_bindings_resolved is False
    assert contract.ready_for_execution is (
        contract.all_required_bindings_resolved and all(f.executable for f in contract.families))
    assert contract.ready_for_execution is False
    assert contract.recommended_next_phase == "30L_NISIM_NILY_OPENING_CONTRACT_BINDING"
    assert not contract.production_bidding_changed and not contract.production_adopted
    assert contract.contract_version == "30K.1"


def test_capability_reports_typed_source_contract_without_execution(contract):
    capability = capability_for_two_over_one_opening_contract(contract)
    assert isinstance(capability, TwoOverOneOpeningContractCapability)
    assert capability.base_contract_defined
    assert capability.source_evidence_typed
    assert capability.required_bindings_explicit
    assert capability.partnership_binding_ready
    assert not capability.all_required_bindings_resolved
    assert not capability.opening_execution_ready
    assert not capability.production_bidding_changed and not capability.production_adopted
    assert capability.version == "30K.1"
    assert json.loads(capability.to_json()) == capability.to_dict()
    with pytest.raises(FrozenInstanceError):
        capability.opening_execution_ready = True
    with pytest.raises(ValueError, match="production activation"):
        replace(capability, production_adopted=True)


def test_canonical_article_supports_typed_claims():
    source = Path(__file__).resolve().parents[2] / "knowledge" / "bidding" / "systems" / "2-over-1.md"
    article = source.read_text(encoding="utf-8")
    for excerpt in (
        "# System Requirements", "# Opening Requirements", "## 1♣", "## 1♦",
        "## 1♥", "## 1♠", "## 1NT", "Natural.", "Usually:",
        "Approximately:", "12-21 HCP", "15-17 balanced", "14-16", "16-18",
        "unless 4-4 in minors", "# Partnership Agreements",
    ):
        assert excerpt in article


def test_phase30j_historical_findings_remain_source_partial(contract):
    plan = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
    before = audit_two_over_one_opening_execution_boundary(plan).to_json()
    for family in contract.families:
        assert audit_two_over_one_opening_execution_boundary(plan).boundary(
            family.family).state is OpeningExecutionBoundaryState.BASE_SOURCE_PARTIAL
    assert audit_two_over_one_opening_execution_boundary(plan).to_json() == before


def test_routes_contexts_and_generic_import_boundary():
    before = tuple(route.route_id for route in create_standard_sayc_router().routes)
    source = Path(__file__).resolve().parents[1] / "bridge" / "two_over_one_opening_contract.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    after = tuple(route.route_id for route in create_standard_sayc_router().routes)
    assert len(before) == len(after) == 45 and before == after
    assert tuple(item.name for item in fields(SystemContext)) == ("system", "options")
    assert tuple(item.name for item in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system")
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert imports == {"__future__", "dataclasses", "enum", "system_profiles"}
    source_text = source.read_text(encoding="utf-8").casefold()
    for forbidden in ("nisim_nily_opening_policy", "nisim_nily_partnership_profile",
                      "rule of 20", "rule20", "multi_2d", "bergen",
                      "forcing_one_notrump", "sayc", "deal_simulator"):
        assert forbidden not in source_text
    definitions = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not definitions.intersection({
        "Hand", "Auction", "Call", "RuleDecision", "BiddingEngineResult",
        "BiddingEngine", "EngineRoute", "evaluate", "recommend", "choose_opening",
    })
