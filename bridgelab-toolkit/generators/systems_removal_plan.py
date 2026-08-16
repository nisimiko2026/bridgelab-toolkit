"""Generate the reviewed removal-first systems metadata plan."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


TAXONOMY = {
    "acol",
    "blue club",
    "carrot club",
    "ehaa",
    "moscito",
    "polish club",
    "precision",
    "roman club",
    "sayc",
    "standard american",
    "strong club",
    "super precision",
    "two over one",
}


def generate(database: Path, json_output: Path, markdown_output: Path) -> None:
    articles = json.loads(database.read_text(encoding="utf-8"))
    proposals: list[dict] = []
    removed_values: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    retained_assignments = 0

    for article in articles:
        path = article["relative_path"]
        systems = article["metadata"].get("systems") or []
        removals: list[dict[str, str]] = []
        for value in systems:
            reason = None
            if not path.startswith("bidding/"):
                reason = "non_bidding_article"
            elif value not in TAXONOMY:
                reason = "outside_system_taxonomy"
            if reason:
                removals.append({"value": value, "reason": reason})
                removed_values[value] += 1
                reasons[reason] += 1
            else:
                retained_assignments += 1
        if removals:
            proposals.append(
                {
                    "path": path,
                    "current_systems": systems,
                    "remove": removals,
                    "proposed_systems": [
                        value
                        for value in systems
                        if value not in {item["value"] for item in removals}
                    ],
                }
            )

    plan = {
        "generated": "2026-08-16",
        "status": "review_required",
        "source_changes_performed": False,
        "policy": "strict_applicability",
        "taxonomy": sorted(TAXONOMY),
        "summary": {
            "files_with_removals": len(proposals),
            "assignments_to_remove": sum(
                len(proposal["remove"]) for proposal in proposals
            ),
            "non_bidding_assignments": reasons["non_bidding_article"],
            "outside_taxonomy_assignments": reasons["outside_system_taxonomy"],
            "taxonomy_valid_assignments_retained_for_review": retained_assignments,
        },
        "removals_by_value": dict(removed_values.most_common()),
        "proposals": proposals,
        "guardrails": [
            "Back up every changed article",
            "Remove only exact reviewed list items",
            "Do not fill any empty systems list",
            "Do not remove taxonomy-valid bidding assignments in this phase",
            "Run all tests and validate the repository",
            "Regenerate the cache and rerun the systems audit",
        ],
    }
    json_output.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    markdown = f"""# Systems Metadata Removal Plan

Generated: 2026-08-16  
Status: Review required  
Source changes performed: none

## Scope

This removal-first phase implements the approved strict-applicability policy conservatively. It removes system assignments from non-bidding articles and removes convention/method values that are outside the controlled system taxonomy. It does not fill empty values or remove taxonomy-valid assignments from bidding articles.

## Impact

- {len(proposals)} files have proposed removals.
- {sum(len(proposal['remove']) for proposal in proposals)} exact assignments are proposed for removal.
- {reasons['non_bidding_article']} assignments occur on non-bidding articles.
- {reasons['outside_system_taxonomy']} assignments are convention or method names outside the system taxonomy.
- {retained_assignments} taxonomy-valid assignments remain for a later applicability review.

## Removed values

| Value | Assignments |
|---|---:|
"""
    for value, count in removed_values.most_common():
        markdown += f"| `{value}` | {count} |\n"

    markdown += """

## Controlled taxonomy retained in this phase

"""
    markdown += "\n".join(f"- `{value}`" for value in sorted(TAXONOMY))
    markdown += """

## Guardrails

1. Back up every changed article.
2. Remove only the exact file/value pairs in the JSON plan.
3. Do not fill any empty `systems` list.
4. Do not remove taxonomy-valid bidding assignments during this phase.
5. Run all toolkit tests and validate every article.
6. Regenerate the cache and rerun the systems audit.

## Approval boundary

Approval applies only to the 385 exact removals recorded in the JSON plan. The 510 retained assignments require a separate applicability audit.
"""
    markdown_output.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(
        root / "output/repository.json",
        root / "output/reports/systems_removal_plan.json",
        root / "output/reports/systems_removal_plan.md",
    )
