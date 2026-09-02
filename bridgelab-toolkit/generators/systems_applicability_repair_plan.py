"""Build an exact guarded repair plan from high-confidence audit entries."""

from __future__ import annotations

import json
from pathlib import Path


def generate(audit_path: Path, output_path: Path) -> dict:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    proposals = []
    for entry in audit["entries"]:
        if entry["confidence"] != "high" or not entry["proposed_remove"]:
            continue
        proposals.append(
            {
                "path": entry["path"],
                "current_systems": entry["current_systems"],
                "remove": [
                    {"value": value, "reason": entry["reason"]}
                    for value in entry["proposed_remove"]
                ],
                "proposed_systems": entry["proposed_systems"],
            }
        )
    plan = {
        "generated": "2026-08-16",
        "status": "approval_required",
        "source_changes_performed": False,
        "scope": "high_confidence_systems_applicability_removals",
        "source_audit": str(audit_path),
        "summary": {
            "files_to_update": len(proposals),
            "assignments_to_remove": sum(len(p["remove"]) for p in proposals),
        },
        "proposals": proposals,
        "guardrails": [
            "Verify every current systems list exactly before writing",
            "Back up every changed article",
            "Remove only the exact approved values",
            "Do not add or infer systems values",
            "Abort the full operation on metadata drift",
        ],
    }
    output_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return plan


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(
        root / "output/reports/systems_applicability_audit.json",
        root / "output/reports/systems_applicability_high_repair_plan.json",
    )
