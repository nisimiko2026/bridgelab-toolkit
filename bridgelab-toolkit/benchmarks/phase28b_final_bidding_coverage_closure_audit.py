"""Phase 28B - Final bidding coverage closure audit.

This audit consumes the Phase 28A current-state inventory and applies the
conservative BridgeLab closure gate.  It changes no production bidding rules,
routes, policies, defaults, or knowledge semantics.

Run from the repository root:

    python -m benchmarks.phase28b_final_bidding_coverage_closure_audit

Required input:
    bridgelab_phase28a_current_bidding_inventory.json

Outputs:
    bridgelab_phase28b_final_bidding_coverage_closure_audit.json
    bridgelab_phase28b_final_bidding_coverage_closure_audit.md
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

PHASE28A_JSON = ROOT / "bridgelab_phase28a_current_bidding_inventory.json"
JSON_OUT = ROOT / "bridgelab_phase28b_final_bidding_coverage_closure_audit.json"
MD_OUT = ROOT / "bridgelab_phase28b_final_bidding_coverage_closure_audit.md"

EXPECTED_PHASE28A_DECISION = "PROCEED TO PHASE 28 FINAL CLOSURE AUDIT"
EXPECTED_CURRENT_CLASSIFICATION = "CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE"
EXPECTED_CURRENT_DECISION = "AUDITED_CURRENT_STATE_NO_BLIND_EXPANSION"
EXPECTED_ROUTE_COUNT = 45

EXPECTED_CURRENT_FAMILIES = (
    "response.one-level-existing-rule",
    "opener.one-level-rebid-existing-rule",
)

ALLOWED_DEFERRED_CLASSIFICATIONS = {
    "SOURCE_PARTIAL",
    "SOURCE_INSUFFICIENT",
    "PARTNERSHIP_DEPENDENT",
    "POLICY_REQUIRED",
}

ALLOWED_DEFERRED_DECISIONS = {
    "DEFER",
    "DEFER_POLICY_REQUIRED",
}

SOURCE_READY_CLASSIFICATIONS = {
    "HIGH_VALUE_SOURCE_READY",
    "SOURCE_READY",
    "IMPLEMENTABLE_SOURCE_READY",
}


@dataclass(frozen=True)
class FamilyClosure:
    family: str
    classification: str
    decision: str
    source_ready: bool
    closure_safe: bool
    rationale: str


@dataclass(frozen=True)
class ClosureAudit:
    phase: str
    phase28a_loaded: bool
    phase28a_closure_ready: bool
    production_route_count: int
    current_families: tuple[FamilyClosure, ...]
    deferred_families: tuple[FamilyClosure, ...]
    remaining_high_value_source_ready: int
    production_rules_added: int
    routes_added: int
    policies_added: int
    production_defaults_changed: bool
    knowledge_markdown_changed: int
    closure_gate: bool
    decision: str


def _load_phase28a() -> dict[str, Any]:
    if not PHASE28A_JSON.exists():
        raise FileNotFoundError(
            "Phase 28A JSON is required before Phase 28B: "
            f"{PHASE28A_JSON}"
        )

    data = json.loads(PHASE28A_JSON.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Phase 28A JSON root must be an object.")
    if data.get("phase") != "28A":
        raise ValueError(
            "Phase 28B expected Phase 28A input, got "
            f"{data.get('phase')!r}."
        )
    return data


def _require_zero_change_guards(data: dict[str, Any]) -> None:
    expected = {
        "production_rules_added": 0,
        "routes_added": 0,
        "policies_added": 0,
        "production_defaults_changed": False,
        "knowledge_markdown_changed": 0,
    }
    for key, value in expected.items():
        actual = data.get(key)
        if actual != value:
            raise ValueError(
                f"Phase 28A guard {key!r} changed: "
                f"expected {value!r}, got {actual!r}."
            )


def _current_family_closures(
    data: dict[str, Any],
) -> tuple[FamilyClosure, ...]:
    raw = data.get("families")
    if not isinstance(raw, list):
        raise ValueError("Phase 28A families must be a list.")

    by_id: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Every Phase 28A family entry must be an object.")
        family_id = item.get("family_id")
        if isinstance(family_id, str):
            by_id[family_id] = item

    missing = [x for x in EXPECTED_CURRENT_FAMILIES if x not in by_id]
    if missing:
        raise ValueError(
            "Phase 28A is missing expected current families: "
            + ", ".join(missing)
        )

    result: list[FamilyClosure] = []
    for family_id in EXPECTED_CURRENT_FAMILIES:
        item = by_id[family_id]
        classification = str(item.get("classification", ""))
        decision = str(item.get("decision", ""))
        source_ready = classification in SOURCE_READY_CLASSIFICATIONS
        closure_safe = (
            classification == EXPECTED_CURRENT_CLASSIFICATION
            and decision == EXPECTED_CURRENT_DECISION
            and not source_ready
        )
        result.append(
            FamilyClosure(
                family=family_id,
                classification=classification,
                decision=decision,
                source_ready=source_ready,
                closure_safe=closure_safe,
                rationale=(
                    "Current production has source-grounded partial coverage; "
                    "Phase 28A found no basis for blind production expansion."
                    if closure_safe
                    else "Current-family state does not satisfy the Phase 28 closure contract."
                ),
            )
        )
    return tuple(result)


def _deferred_family_closures(
    data: dict[str, Any],
) -> tuple[FamilyClosure, ...]:
    raw = data.get("deferred_families")
    if not isinstance(raw, list):
        raise ValueError("Phase 28A deferred_families must be a list.")

    result: list[FamilyClosure] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Every deferred family entry must be an object.")

        family = str(item.get("family", ""))
        classification = str(item.get("classification", ""))
        decision = str(item.get("decision", ""))
        if not family:
            raise ValueError("Deferred family name must not be blank.")

        source_ready = classification in SOURCE_READY_CLASSIFICATIONS
        closure_safe = (
            classification in ALLOWED_DEFERRED_CLASSIFICATIONS
            and decision in ALLOWED_DEFERRED_DECISIONS
            and not source_ready
        )

        if classification == "SOURCE_PARTIAL":
            rationale = (
                "Frozen source remains incomplete for an executable production contract."
            )
        elif classification == "SOURCE_INSUFFICIENT":
            rationale = (
                "Frozen source is insufficient for a safe production implementation."
            )
        elif classification in {"PARTNERSHIP_DEPENDENT", "POLICY_REQUIRED"}:
            rationale = (
                "Executable behavior depends on an explicit partnership policy."
            )
        else:
            rationale = "Classification requires review before closure."

        result.append(
            FamilyClosure(
                family=family,
                classification=classification,
                decision=decision,
                source_ready=source_ready,
                closure_safe=closure_safe,
                rationale=rationale,
            )
        )
    return tuple(result)


def build_audit() -> ClosureAudit:
    data = _load_phase28a()
    _require_zero_change_guards(data)

    route_count = data.get("production_route_count")
    if route_count != EXPECTED_ROUTE_COUNT:
        raise ValueError(
            "Production route count drifted before Phase 28B: "
            f"expected {EXPECTED_ROUTE_COUNT}, got {route_count!r}."
        )

    phase28a_ready = data.get("closure_ready") is True
    phase28a_decision_ok = data.get("decision") == EXPECTED_PHASE28A_DECISION

    current = _current_family_closures(data)
    deferred = _deferred_family_closures(data)

    all_families = current + deferred
    remaining_source_ready = sum(1 for x in all_families if x.source_ready)

    closure_gate = (
        phase28a_ready
        and phase28a_decision_ok
        and route_count == EXPECTED_ROUTE_COUNT
        and bool(current)
        and bool(deferred)
        and all(x.closure_safe for x in all_families)
        and remaining_source_ready == 0
    )

    return ClosureAudit(
        phase="28B",
        phase28a_loaded=True,
        phase28a_closure_ready=phase28a_ready,
        production_route_count=route_count,
        current_families=current,
        deferred_families=deferred,
        remaining_high_value_source_ready=remaining_source_ready,
        production_rules_added=0,
        routes_added=0,
        policies_added=0,
        production_defaults_changed=False,
        knowledge_markdown_changed=0,
        closure_gate=closure_gate,
        decision=(
            "PHASE 28 BIDDING COVERAGE COMPLETE"
            if closure_gate
            else "PHASE 28 CLOSURE BLOCKED"
        ),
    )


def _family_rows(items: tuple[FamilyClosure, ...]) -> list[str]:
    return [
        "| "
        + " | ".join(
            (
                x.family,
                x.classification,
                x.decision,
                str(x.source_ready),
                str(x.closure_safe),
            )
        )
        + " |"
        for x in items
    ]


def render_markdown(audit: ClosureAudit) -> str:
    lines = [
        "# Phase 28B - Final Bidding Coverage Closure Audit",
        "",
        "## Purpose",
        "",
        "Apply the final conservative bidding-coverage closure gate to the "
        "Phase 28A current-state inventory.",
        "",
        "This audit does not claim that BridgeLab implements every possible SAYC "
        "auction. Closure means that no family in the audited inventory remains "
        "both source-ready and unjustifiably unimplemented. Source-partial, "
        "source-insufficient, and partnership-dependent families remain deliberate "
        "abstention/defer boundaries.",
        "",
        "## Phase 28A gate",
        "",
        f"- Phase 28A loaded: **{audit.phase28a_loaded}**",
        f"- Phase 28A closure ready: **{audit.phase28a_closure_ready}**",
        f"- production route count: **{audit.production_route_count}**",
        "",
        "## Current-state families",
        "",
        "| Family | Classification | Decision | Source ready | Closure safe |",
        "|---|---|---|---|---|",
        *_family_rows(audit.current_families),
        "",
        "## Previously audited deferred families",
        "",
        "| Family | Classification | Decision | Source ready | Closure safe |",
        "|---|---|---|---|---|",
        *_family_rows(audit.deferred_families),
        "",
        "## Source-readiness result",
        "",
        "- remaining HIGH_VALUE_SOURCE_READY families: "
        f"**{audit.remaining_high_value_source_ready}**",
        "",
        "No approximate, qualitative, or partnership-dependent source language is "
        "promoted into a hard production threshold by this closure audit.",
        "",
        "## Production guards",
        "",
        f"- production rules added: {audit.production_rules_added}",
        f"- routes added: {audit.routes_added}",
        f"- policies added: {audit.policies_added}",
        f"- production defaults changed: {audit.production_defaults_changed}",
        f"- knowledge Markdown changed: {audit.knowledge_markdown_changed}",
        "",
        "## Final closure gate",
        "",
        f"- closure_gate: **{audit.closure_gate}**",
        f"- decision: **{audit.decision}**",
        "",
    ]

    if audit.closure_gate:
        lines.extend(
            [
                "Phase 28 bidding coverage is complete under the current frozen "
                "source corpus and explicit policy boundaries. Future bidding work "
                "should reopen coverage only when a new authoritative source, an "
                "explicit partnership policy, or a newly scoped feature supplies "
                "an executable contract.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Closure is blocked. Review the JSON output for a family whose "
                "`closure_safe` value is false or for a source-ready family that "
                "still requires implementation.",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> int:
    audit = build_audit()

    JSON_OUT.write_text(
        json.dumps(asdict(audit), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    MD_OUT.write_text(render_markdown(audit), encoding="utf-8")

    print("Phase 28B final bidding coverage closure audit")
    print(f"Phase 28A closure ready: {audit.phase28a_closure_ready}")
    print(f"Production routes: {audit.production_route_count}")
    print(
        "Remaining HIGH_VALUE_SOURCE_READY families: "
        f"{audit.remaining_high_value_source_ready}"
    )
    print(f"Closure gate: {audit.closure_gate}")
    print(f"Decision: {audit.decision}")
    print(f"Wrote: {JSON_OUT.name}")
    print(f"Wrote: {MD_OUT.name}")

    return 0 if audit.closure_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
