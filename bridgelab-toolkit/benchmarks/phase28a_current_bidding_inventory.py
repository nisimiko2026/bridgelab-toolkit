"""Phase 28A - Current bidding inventory and closure-readiness audit.

Audit-only: no production rules, routes, policies, defaults, or bidding
semantics are changed.

Run:
    python -m benchmarks.phase28a_current_bidding_inventory
"""

from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "bridge"
ROUTER = BRIDGE / "sayc_route_configuration.py"
JSON_OUT = ROOT / "bridgelab_phase28a_current_bidding_inventory.json"
MD_OUT = ROOT / "bridgelab_phase28a_current_bidding_inventory.md"

RESPONSE_FILES = (
    "sayc_responses.py", "sayc_1d_responses.py", "sayc_1h_responses.py",
    "sayc_1s_responses.py", "sayc_1d_notrump.py",
    "sayc_major_one_notrump.py", "two_over_one_responses.py",
)
REBID_FILES = (
    "sayc_1c1d_opener_rebids.py", "sayc_1c1h_opener_rebids.py",
    "sayc_1c1s_opener_rebids.py", "sayc_1d1h_opener_rebids.py",
    "sayc_1d1s_opener_rebids.py", "sayc_1h1s_opener_rebids.py",
    "sayc_major_raise_opener_rebids.py", "two_over_one_opener_rebids.py",
)
RESPONSE_ROUTES = (
    "sayc.response.1c", "sayc.response.1d",
    "sayc.response.1h", "sayc.response.1s",
)
REBID_ROUTES = (
    "sayc.opener.1c.1d", "sayc.opener.1c.1h", "sayc.opener.1c.1s",
    "sayc.opener.1d.1h", "sayc.opener.1d.1s", "sayc.opener.1h.1s",
    "sayc.opener.1h.2h", "sayc.opener.1s.2s",
)
TWO_OVER_ONE_ROUTES = (
    "sayc.2over1.opener.1h.2c", "sayc.2over1.opener.1h.2d",
    "sayc.2over1.opener.1s.2c", "sayc.2over1.opener.1s.2d",
)
DEFERRED = (
    ("Stayman residuals", "SOURCE_PARTIAL", "DEFER"),
    ("strong-2C residuals", "SOURCE_PARTIAL", "DEFER"),
    ("natural 1NT responses", "SOURCE_PARTIAL", "DEFER"),
    ("responder rebids", "SOURCE_PARTIAL", "DEFER"),
    ("three-level preempt responses", "SOURCE_PARTIAL", "DEFER"),
    ("weak-two responses", "PARTNERSHIP_DEPENDENT", "DEFER_POLICY_REQUIRED"),
    ("2NT response residuals", "SOURCE_PARTIAL", "DEFER"),
    ("Two-over-One unsupported opener rebids", "SOURCE_INSUFFICIENT", "DEFER"),
)

@dataclass(frozen=True)
class ModuleInventory:
    module: str
    rule_ids: tuple[str, ...]
    source_pointers: tuple[str, ...]
    abstention_guards: int

@dataclass(frozen=True)
class FamilyInventory:
    family_id: str
    phase12u_population: int
    phase12u_status: str
    current_rule_count: int
    current_routes: tuple[str, ...]
    source_pointer_count: int
    abstention_guards: int
    classification: str
    decision: str

@dataclass(frozen=True)
class Audit:
    phase: str
    production_route_count: int
    response_modules: tuple[ModuleInventory, ...]
    opener_rebid_modules: tuple[ModuleInventory, ...]
    families: tuple[FamilyInventory, ...]
    deferred_families: tuple[dict[str, str], ...]
    production_rules_added: int
    routes_added: int
    policies_added: int
    production_defaults_changed: bool
    knowledge_markdown_changed: int
    closure_ready: bool
    decision: str

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required Phase 28A input is missing: {path}")
    return path.read_text(encoding="utf-8")

def rule_ids(text: str) -> tuple[str, ...]:
    tree = ast.parse(text)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "rule_id":
                found.append(value.value)
    return tuple(dict.fromkeys(found))

def source_pointers(text: str) -> tuple[str, ...]:
    tree = ast.parse(text)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        match = (
            isinstance(func, ast.Name) and func.id == "KnowledgeSource"
        ) or (
            isinstance(func, ast.Attribute) and func.attr == "KnowledgeSource"
        )
        if match:
            found.append(ast.unparse(node))
    return tuple(dict.fromkeys(found))

def inventory(name: str) -> ModuleInventory:
    text = read(BRIDGE / name)
    return ModuleInventory(
        module=f"bridge/{name}",
        rule_ids=rule_ids(text),
        source_pointers=source_pointers(text),
        abstention_guards=text.count("RuleDecision.not_applicable"),
    )

def route_ids() -> tuple[str, ...]:
    tree = ast.parse(read(ROUTER))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        match = (
            isinstance(func, ast.Name) and func.id == "EngineRoute"
        ) or (
            isinstance(func, ast.Attribute) and func.attr == "EngineRoute"
        )
        if match and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                found.append(first.value)
    return tuple(found)

def selected_routes(all_routes, wanted):
    available = set(all_routes)
    return tuple(route for route in wanted if route in available)

def build_audit() -> Audit:
    responses = tuple(inventory(name) for name in RESPONSE_FILES)
    rebids = tuple(inventory(name) for name in REBID_FILES)
    routes = route_ids()

    response_routes = selected_routes(routes, RESPONSE_ROUTES)
    rebid_routes = selected_routes(routes, REBID_ROUTES)
    two_over_one_routes = selected_routes(routes, TWO_OVER_ONE_ROUTES)

    response_rules = sum(len(x.rule_ids) for x in responses)
    rebid_rules = sum(len(x.rule_ids) for x in rebids)
    response_sources = sum(len(x.source_pointers) for x in responses)
    rebid_sources = sum(len(x.source_pointers) for x in rebids)
    response_guards = sum(x.abstention_guards for x in responses)
    rebid_guards = sum(x.abstention_guards for x in rebids)

    response_ok = (
        response_rules > 0 and response_sources > 0
        and set(response_routes) == set(RESPONSE_ROUTES)
    )
    rebid_ok = (
        rebid_rules > 0 and rebid_sources > 0
        and set(rebid_routes) == set(REBID_ROUTES)
        and set(two_over_one_routes) == set(TWO_OVER_ONE_ROUTES)
    )

    families = (
        FamilyInventory(
            "response.one-level-existing-rule", 693, "NOT_YET_AUDITED",
            response_rules, response_routes, response_sources, response_guards,
            "CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE" if response_ok
            else "CURRENT_COVERAGE_INCOMPLETE",
            "AUDITED_CURRENT_STATE_NO_BLIND_EXPANSION" if response_ok
            else "REVIEW_REQUIRED",
        ),
        FamilyInventory(
            "opener.one-level-rebid-existing-rule", 406, "NOT_YET_AUDITED",
            rebid_rules, rebid_routes + two_over_one_routes,
            rebid_sources, rebid_guards,
            "CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE" if rebid_ok
            else "CURRENT_COVERAGE_INCOMPLETE",
            "AUDITED_CURRENT_STATE_NO_BLIND_EXPANSION" if rebid_ok
            else "REVIEW_REQUIRED",
        ),
    )
    closure_ready = all(x.decision != "REVIEW_REQUIRED" for x in families)

    return Audit(
        "28A", len(routes), responses, rebids, families,
        tuple({"family": f, "classification": c, "decision": d}
              for f, c, d in DEFERRED),
        0, 0, 0, False, 0, closure_ready,
        "PROCEED TO PHASE 28 FINAL CLOSURE AUDIT" if closure_ready
        else "REVIEW CURRENT STRUCTURAL COVERAGE BEFORE CLOSURE",
    )

def module_rows(items):
    return [
        f"| {x.module} | {len(x.rule_ids)} | {len(x.source_pointers)} | {x.abstention_guards} |"
        for x in items
    ]

def render_markdown(audit: Audit) -> str:
    lines = [
        "# Phase 28A - Current Bidding Inventory", "",
        "## Purpose", "",
        "Re-audit the two Phase 12U families that were still marked "
        "`NOT_YET_AUDITED`, using the current production tree rather than the "
        "old Phase 12 simulation snapshot.", "",
        "This phase is audit-only. It adds no bidding rule, route, policy, "
        "default, or knowledge semantics.", "",
        "## Production router", "",
        f"- Current production route count: **{audit.production_route_count}**", "",
        "## One-level response inventory", "",
        "| Module | Rules | Source pointers | not_applicable guards |",
        "|---|---:|---:|---:|", *module_rows(audit.response_modules), "",
        "## Opener-rebid inventory", "",
        "| Module | Rules | Source pointers | not_applicable guards |",
        "|---|---:|---:|---:|", *module_rows(audit.opener_rebid_modules), "",
        "## Phase 12U family re-audit", "",
        "| Family | Phase 12U | Current rules | Routes | Sources | Guards | Classification | Decision |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for x in audit.families:
        lines.append(
            f"| {x.family_id} | {x.phase12u_status} | {x.current_rule_count} | "
            f"{len(x.current_routes)} | {x.source_pointer_count} | "
            f"{x.abstention_guards} | {x.classification} | {x.decision} |"
        )
    lines += [
        "", "## Interpretation", "",
        "The Phase 12U `NOT_YET_AUDITED` labels are historical. Current production "
        "contains explicit source-grounded rules and routes for both families. "
        "Phase 28A records that current structure without claiming that every "
        "possible SAYC branch is source-complete.", "",
        "Explicit `not_applicable` guards are treated as normal conservative rule "
        "eligibility/precedence behavior, not automatically as coverage defects.", "",
        "## Previously audited deferred families", "",
        "| Family | Classification | Decision |", "|---|---|---|",
    ]
    for x in audit.deferred_families:
        lines.append(f"| {x['family']} | {x['classification']} | {x['decision']} |")
    lines += [
        "",
        "These families remain deferred unless a frozen source or explicit "
        "partnership policy supplies an executable contract. Phase 28A does not "
        "convert approximate, qualitative, or partnership-dependent wording into "
        "hard production thresholds.", "",
        "## Guards", "",
        f"- production rules added: {audit.production_rules_added}",
        f"- routes added: {audit.routes_added}",
        f"- policies added: {audit.policies_added}",
        f"- production defaults changed: {audit.production_defaults_changed}",
        f"- knowledge Markdown changed: {audit.knowledge_markdown_changed}", "",
        "## Closure readiness", "",
        f"- closure_ready: **{audit.closure_ready}**",
        f"- decision: **{audit.decision}**", "",
        "Phase 28A does not claim complete SAYC coverage. It establishes whether "
        "the two old Phase 12U untouched buckets now have enough current "
        "source-grounded production structure to move to a final closure audit "
        "instead of expanding production merely to reduce abstention counts.", "",
    ]
    return "\n".join(lines)

def main() -> int:
    audit = build_audit()
    JSON_OUT.write_text(
        json.dumps(asdict(audit), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    MD_OUT.write_text(render_markdown(audit), encoding="utf-8")
    print("Phase 28A current bidding inventory")
    print(f"Production routes: {audit.production_route_count}")
    for family in audit.families:
        print(
            f"{family.family_id}: rules={family.current_rule_count}, "
            f"routes={len(family.current_routes)}, "
            f"sources={family.source_pointer_count}, "
            f"guards={family.abstention_guards}, "
            f"classification={family.classification}, "
            f"decision={family.decision}"
        )
    print(f"Closure ready: {audit.closure_ready}")
    print(f"Decision: {audit.decision}")
    print(f"Wrote: {JSON_OUT.name}")
    print(f"Wrote: {MD_OUT.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
