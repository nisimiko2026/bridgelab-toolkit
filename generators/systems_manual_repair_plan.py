"""Build the guarded repair plan for approved manual-review removals."""

from __future__ import annotations

import json
from pathlib import Path


def generate(review_path: Path, output_path: Path) -> dict:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    proposals = [
        {
            "path": entry["path"],
            "current_systems": entry["current_systems"],
            "remove": entry["remove"],
            "proposed_systems": entry["proposed_systems"],
        }
        for entry in review["entries"]
        if entry["remove"]
    ]
    plan = {
        "generated": "2026-08-16",
        "status": "approved",
        "source_changes_performed": False,
        "scope": "24_exact_manual_review_removals",
        "summary": {
            "files_to_update": len(proposals),
            "assignments_to_remove": sum(len(item["remove"]) for item in proposals),
        },
        "proposals": proposals,
        "guardrails": [
            "Verify every current systems list exactly before writing",
            "Back up every changed article",
            "Remove only the 24 approved values",
            "Retain all 53 positively reviewed assignments",
            "Abort the full operation on metadata drift",
        ],
    }
    output_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return plan


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(
        root / "output/reports/systems_manual_review.json",
        root / "output/reports/systems_manual_repair_plan.json",
    )
