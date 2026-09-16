"""Evidence/serialization guards, not speculative bridge-policy tests."""

import ast
import dataclasses
import json
from pathlib import Path
import re
import subprocess

import pytest

from bridge.opening_pass_source_policy_audit import (
    PolicySupport, SourceAuthority, build_opening_pass_source_report,
)
from bridge.sayc import sayc_opening_rules
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.source_authority import DEFAULT_SOURCE_AUTHORITY_REGISTRY


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "bridgelab-toolkit/bridge/opening_pass_source_policy_audit.py"


def test_deterministic_immutable_report_and_serialization():
    report = build_opening_pass_source_report()
    assert report == build_opening_pass_source_report()
    assert report.to_json() == build_opening_pass_source_report().to_json()
    assert json.loads(report.to_json()) == report.to_dict()
    assert tuple(e.evidence_id for e in report.source_inventory) == tuple(sorted(e.evidence_id for e in report.source_inventory))
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.implementation_readiness = "READY"
    data = report.to_dict()
    data["source_inventory"].clear()
    assert report.source_inventory


def test_inventory_paths_metadata_and_authority_are_real():
    report = build_opening_pass_source_report()
    for evidence in report.source_inventory:
        assert not evidence.positive_pass_support
        if evidence.path:
            path = ROOT / evidence.path
            assert path.is_file(), evidence.path
            if evidence.path.startswith("knowledge/"):
                body = path.read_text(encoding="utf-8-sig")
                assert re.search(r"^status:\s*['\"]?" + evidence.source_status, body, re.M)
                article = evidence.path[len("knowledge/"):-3]
                assert evidence.registry_authority == DEFAULT_SOURCE_AUTHORITY_REGISTRY.record_for(article).authority
    assert all(e.authority is not SourceAuthority.CANONICAL_PRODUCTION_REFERENCE or e.production_rules
               for e in report.source_inventory)
    assert all(e.registry_authority.value == "UNKNOWN" for e in report.source_inventory)
    assert next(e for e in report.source_inventory if e.evidence_id == "pass-tests").authority is SourceAuthority.TEST_ONLY


def test_matrix_matches_real_registry_and_has_separate_pass():
    rows = build_opening_pass_source_report().family_policy_matrix
    assert len(rows) == 15
    assert {r.rule_id for r in rows if r.rule_id} == {r.rule_id for r in sayc_opening_rules()}
    assert rows[-1].family == "Opening Pass" and rows[-1].rule_id is None
    assert all(not r.complement_explicitly_pass for r in rows)
    assert all("UNKNOWN" in r.complement_status for r in rows)
    assert len(create_standard_sayc_router().routes) == 45


def test_evidence_references_resolve_and_missing_policy_is_explicit():
    report = build_opening_pass_source_report()
    ids = {e.evidence_id for e in report.source_inventory}
    for field in dataclasses.fields(report):
        value = getattr(report, field.name)
        if isinstance(value, tuple):
            for item in value:
                if hasattr(item, "evidence_ids"):
                    assert set(item.evidence_ids) <= ids
    assert report.implementation_readiness == "INCOMPLETE"
    assert report.pass_recommendations_created == 0
    assert report.invariant == "PASS != FALLBACK_FOR_ABSTAIN"
    assert next(e for e in report.source_inventory if e.evidence_id == "pass-policy").authority is SourceAuthority.MISSING


def test_safety_boundaries_are_not_pass():
    report = build_opening_pass_source_report()
    findings = report.equal_suit_findings + report.strong_2c_safety_findings + report.weak_two_preempt_safety_findings + report.other_safety_findings
    by_id = {f.finding_id: f for f in findings}
    for key in ("equal-five-majors", "equal-minors", "strong-playing-tricks", "weak-preempt-overlap", "preempt-style", "seat-scope", "low-strength-screen"):
        assert by_id[key].safety_exclusion
        assert by_id[key].support in (PolicySupport.POLICY_REQUIRED, PolicySupport.SOURCE_INSUFFICIENT)
    assert all(f.support is not PolicySupport.PASS for f in findings + report.borderline_hand_findings)


def test_rule20_rule22_evidence_and_no_production_adoption():
    root = ROOT / "knowledge/bidding/principles/bidding-fundamentals"
    twenty = (root / "rule-of-20.md").read_text(encoding="utf-8")
    twenty_two = (root / "rule-of-22.md").read_text(encoding="utf-8")
    assert "Usually pass" in twenty and "11 + 5 + 4 = 20" in twenty
    assert "Quick Tricks ≥ 22" in twenty_two and "status: Standard" in twenty_two
    production = (ROOT / "bridgelab-toolkit/bridge/sayc.py").read_text(encoding="utf-8")
    assert not re.search(r"rule.of.(20|22)", production, re.I)
    findings = build_opening_pass_source_report().rule_20_22_findings
    assert {f.finding_id for f in findings} == {"rule20", "rule22"}
    assert all(f.support is PolicySupport.POLICY_REQUIRED for f in findings)


def test_major_tie_guidance_is_qualified_not_missing_or_conflicting():
    base = ROOT / "knowledge/bidding/natural-bids/opening-bids"
    heart = (base / "1-heart.md").read_text(encoding="utf-8")
    spade = (base / "1-spade.md").read_text(encoding="utf-8")
    assert "partnership agreement determines whether to open 1♥ or 1♠" in heart
    assert "Most five-card-major systems open **1♥** with **5-5**" in heart
    assert "**1♥**, allowing spades" in spade


def test_no_decision_logic_no_deal_retention_and_prior_audits_available():
    import bridge.opening_abstention_root_cause_audit as phase29j
    import bridge.opening_pass_policy_audit as phase29k
    assert callable(phase29j.build_opening_root_cause_report)
    assert callable(phase29k.build_opening_pass_policy_report)
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    assert not any(isinstance(n, ast.FunctionDef) and n.name == "evaluate" for n in ast.walk(tree))
    assert not any(isinstance(n, ast.Attribute) and n.attr in ("recommend", "parse", "evaluate") for n in ast.walk(tree))
    assert "deal" not in {f.name for f in dataclasses.fields(build_opening_pass_source_report())}


def test_audit_does_not_modify_existing_tracked_files():
    before = subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=ROOT)
    build_opening_pass_source_report()
    after = subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=ROOT)
    assert before == after
    permitted = {
        "bridgelab-toolkit/bridge/opening_pass_source_policy_audit.py",
        "bridgelab-toolkit/tests/test_bridge_phase29l_opening_pass_source_policy_audit.py",
        "bridgelab-toolkit/bridgelab_phase29l_opening_pass_source_policy_audit.md",
        "bridgelab-toolkit/bridgelab_phase29l_opening_pass_source_policy_audit.json",
    }
    assert set(after.decode().splitlines()) <= permitted
