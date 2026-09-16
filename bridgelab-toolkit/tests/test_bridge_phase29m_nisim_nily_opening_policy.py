"""Tests of approved partnership knowledge, never invented opening semantics."""

import ast
from dataclasses import FrozenInstanceError, fields
import json
from pathlib import Path

import pytest

from bridge.models import Hand
from bridge.nisim_nily_opening_policy import (
    OpeningPolicyAuthority as Authority, OpeningPolicyStatus as Status,
    assess_rule_of_20, build_nisim_nily_opening_policy,
)


def propositions():
    return {p.policy_id: p for p in build_nisim_nily_opening_policy().propositions}


def test_identity_and_deterministic_immutable_serialization():
    policy = build_nisim_nily_opening_policy()
    assert (policy.policy_id, policy.version) == ("nisim-nily.opening-policy", "29M.1")
    assert policy.to_json() == build_nisim_nily_opening_policy().to_json()
    assert json.loads(policy.to_json()) == policy.to_dict()
    with pytest.raises(FrozenInstanceError):
        policy.version = "changed"
    policy.to_dict()["propositions"].clear()
    assert policy.propositions
    assert len({p.policy_id for p in policy.propositions}) == len(policy.propositions)
    assert all(p.provenance for p in policy.propositions)


@pytest.mark.parametrize("hand, hcp, longest, second, score, qualifies", [
    ("KQJ98.A974.8.J73", 11, 5, 4, 20, True),
    ("KQJ9.A974.83.J73", 11, 4, 4, 19, False),
    ("AJ4.Q96.KT8.Q952", 12, 4, 3, 19, False),
    ("AJ4.K96.KT8.Q952", 13, 4, 3, 20, True),
    ("KQJ98.A9742.8.73", 10, 5, 5, 20, True),
])
def test_strength_arithmetic_only(hand, hcp, longest, second, score, qualifies):
    result = assess_rule_of_20(Hand.parse(hand))
    assert (result.hcp, result.longest_suit_length, result.second_longest_suit_length,
            result.score, result.qualifies) == (hcp, longest, second, score, qualifies)
    assert result.intended_11_hcp_use == (hcp == 11)
    assert not result.selects_opening_call and not result.failure_implies_pass
    assert json.loads(result.to_json()) == result.to_dict()
    assert "hand" not in {f.name for f in fields(result)}
    with pytest.raises(FrozenInstanceError):
        result.score = 99


def test_helper_uses_valid_canonical_hand():
    with pytest.raises(TypeError):
        assess_rule_of_20("KQJ98.A974.8.J73")


def test_12_and_13_are_normal_strength_without_universal_rule20_gate():
    for key in ("strength-12", "strength-13-plus"):
        p = propositions()[key]
        assert p.normal_opening_strength and not p.requires_rule20
        assert p.preferred_call is None and not p.production_adopted
        assert "family" in p.limitations and "unresolved" in p.limitations
    assert propositions()["strength-11"].requires_rule20
    assert propositions()["strength-11"].preferred_call is None
    assert not propositions()["strength-10-or-less"].normal_opening_strength


def test_exact_five_five_majors_is_1s_partnership_policy():
    policy = build_nisim_nily_opening_policy()
    p = propositions()["equal-five-card-majors"]
    assert p.preferred_call == policy.equal_five_card_majors_choice == "1S"
    assert p.preferred_call != "1H"
    assert p.condition == "Spades == 5 and hearts == 5"
    assert p.authority is Authority.NISIM_NILY_PARTNERSHIP_POLICY
    assert p.status is Status.APPROVED and not p.production_adopted
    assert policy.equal_major_choice_requires_opening_eligibility
    assert propositions()["five-major-five-minor"].authority is Authority.NISIM_NILY_PARTNERSHIP_POLICY


def test_rule20_is_partnership_and_rule22_is_reference_only():
    policy = build_nisim_nily_opening_policy()
    assert policy.rule20_primary_hcp == 11
    assert policy.rule20_authority is Authority.NISIM_NILY_PARTNERSHIP_POLICY
    assert propositions()["rule20"].status is Status.APPROVED
    assert policy.rule22_status is Status.REFERENCE_ONLY
    assert not propositions()["rule22"].production_adopted
    assert propositions()["rule22"].authority is Authority.SUPPORTED_REFERENCE
    assert all(p.authority is not Authority.AUTHORITATIVE_REPOSITORY_SOURCE for p in policy.propositions)


def test_equal_minor_policies_and_protected_unresolved_domains():
    p = propositions()
    assert p["equal-minors-3-3"].preferred_call == "1C"
    assert p["equal-minors-4-4"].preferred_call == "1D"
    assert p["equal-minors-5-5"].status is Status.UNRESOLVED
    assert p["other-equal-minors"].status is Status.UNRESOLVED
    policy = build_nisim_nily_opening_policy()
    exclusions = {e.exclusion_id: e for e in policy.safety_exclusions}
    assert {"equal-minors", "strong-2c-playing-tricks", "weak-two-preempt", "equal-majors-6-6",
            "long-suit-variants", "unimplemented-approved-openings", "context-and-evaluation"} <= exclusions.keys()
    for exclusion in exclusions.values():
        assert exclusion.exclude_from_future_pass and not exclusion.implies_pass
        assert exclusion.unresolved_disposition == "UNKNOWN / ABSTAIN"


def test_no_fallback_or_positive_pass_created():
    policy = build_nisim_nily_opening_policy()
    assert policy.invariant == "PASS != FALLBACK_FOR_ABSTAIN"
    assert not any((policy.abstain_to_pass_allowed, policy.unknown_to_pass_allowed,
                    policy.registry_complement_is_pass, policy.failure_to_open_is_evidence_to_pass,
                    policy.production_integration))
    assert policy.positive_pass_status is Status.INCOMPLETE
    assert propositions()["pass-fallback-prohibition"].status is Status.PROHIBITED
    assert all(p.preferred_call not in ("P", "Pass") for p in policy.propositions)


def test_no_rules_router_or_decision_dependencies():
    import bridge.nisim_nily_opening_policy as module
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert imports <= {"__future__", "dataclasses", "enum", "evaluation", "models"}
    assert not any(isinstance(n, ast.FunctionDef) and n.name == "evaluate" for n in ast.walk(tree))
    assert not any(isinstance(n, ast.Attribute) and n.attr in ("recommend", "register", "add_route") for n in ast.walk(tree))


def test_production_and_prior_diagnostics_remain_compatible():
    from bridge.auction import Auction
    from bridge.bidding_rules import BiddingContext, SystemContext
    from bridge.models import Seat, Vulnerability
    from bridge.sayc import sayc_opening_rules, create_sayc_opening_engine
    from bridge.sayc_route_configuration import create_standard_sayc_router
    from bridge.opening_abstention_root_cause_audit import build_opening_root_cause_report
    from bridge.opening_pass_policy_audit import audit_passed_out_auction
    from bridge.opening_pass_source_policy_audit import build_opening_pass_source_report
    before = tuple(r.rule_id for r in sayc_opening_rules())
    build_nisim_nily_opening_policy()
    assess_rule_of_20(Hand.parse("KQJ98.A974.8.J73"))
    assert tuple(r.rule_id for r in sayc_opening_rules()) == before
    assert len(before) == 14 and len(create_standard_sayc_router().routes) == 45
    # Policy approval does not change today's known equal-major production boundary.
    context = BiddingContext.create(hand=Hand.parse("AKJ98.KQ974.8.73"), auction=Auction(Seat.NORTH),
                                    vulnerability=Vulnerability.NONE, system=SystemContext("SAYC"))
    assert not create_sayc_opening_engine().evaluate(context).has_recommendation
    assert callable(build_opening_root_cause_report)
    assert audit_passed_out_auction().is_passed_out
    assert build_opening_pass_source_report().implementation_readiness == "INCOMPLETE"
