"""Record article-level decisions for the final systems applicability batch."""

from __future__ import annotations

import json
from pathlib import Path


REMOVALS = {
    "bidding/conventions/competitive/ghestem.md": ["precision"],
    "bidding/conventions/defensive-methods/crash.md": ["blue club", "precision", "strong club"],
    "bidding/conventions/defensive-methods/defense-against-multi-2d.md": ["precision"],
    "bidding/conventions/defensive-methods/defense-against-precision.md": ["precision", "standard american", "strong club"],
    "bidding/conventions/defensive-methods/defense-against-strong-club.md": ["precision", "strong club"],
    "bidding/conventions/defensive-methods/suction.md": ["blue club", "precision", "strong club"],
    "bidding/conventions/defensive-methods/twerb.md": ["blue club", "precision", "strong club"],
    "bidding/conventions/doubles/lightner-double.md": ["precision"],
    "bidding/conventions/relay/spiral-relay.md": ["strong club"],
    "bidding/conventions/responses/lebensohl-after-1nt-doubled.md": ["precision"],
    "bidding/conventions/slam-conventions/kickback.md": ["precision"],
    "bidding/principles/partnership/alert-procedures.md": ["precision"],
    "bidding/principles/partnership/partnership-agreements.md": ["precision", "standard american", "strong club"],
}


def removal_reason(path: str, value: str) -> str:
    if "defensive-methods" in path:
        return "opponent_or_subject_system_not_article_applicability"
    if path.endswith(("ghestem.md", "lightner-double.md", "lebensohl-after-1nt-doubled.md", "kickback.md")):
        return "ordinary_word_precision_not_precision_system"
    if path.endswith("spiral-relay.md"):
        return "strong_club_not_present_in_article_body"
    return "example_system_not_article_applicability"


def generate(audit_path: Path, json_output: Path, markdown_output: Path) -> dict:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    entries = []
    for item in audit["entries"]:
        if item["confidence"] != "manual":
            continue
        removed = REMOVALS.get(item["path"], [])
        retained = [value for value in item["current_systems"] if value not in removed]
        entries.append({
            "path": item["path"],
            "current_systems": item["current_systems"],
            "remove": [{"value": value, "reason": removal_reason(item["path"], value)} for value in removed],
            "retain": retained,
            "proposed_systems": retained,
        })
    removals = sum(len(item["remove"]) for item in entries)
    retained = sum(len(item["retain"]) for item in entries)
    review = {
        "generated": "2026-08-16",
        "status": "review_required",
        "source_changes_performed": False,
        "summary": {
            "articles_reviewed": len(entries),
            "assignments_reviewed": removals + retained,
            "assignments_proposed_for_removal": removals,
            "assignments_recommended_for_retention": retained,
            "files_with_removals": sum(bool(item["remove"]) for item in entries),
        },
        "entries": entries,
    }
    json_output.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Final Systems Applicability Review",
        "",
        "Generated: 2026-08-16  ",
        "Status: Review required  ",
        "Source changes performed: none",
        "",
        "## Summary",
        "",
        f"- {len(entries)} articles and {removals + retained} assignments reviewed individually.",
        f"- {removals} assignments in {sum(bool(item['remove']) for item in entries)} files are proposed for removal.",
        f"- {retained} assignments are recommended for retention.",
        "",
        "## Proposed removals",
        "",
        "| Article | Value | Reason |",
        "|---|---|---|",
    ]
    for item in entries:
        for removal in item["remove"]:
            lines.append(f"| `{item['path']}` | `{removal['value']}` | {removal['reason']} |")
    lines += [
        "",
        "## Decision boundary",
        "",
        "Only the 24 exact removals above are candidates for approval. The 53 retained assignments must not be removed.",
    ]
    markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return review


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(
        root / "output/reports/systems_applicability_audit.json",
        root / "output/reports/systems_manual_review.json",
        root / "output/reports/systems_manual_review.md",
    )
