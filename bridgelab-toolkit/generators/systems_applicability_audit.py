"""Generate a conservative audit of taxonomy-valid systems assignments."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from core.document_roles import DocumentRole, classify_document_role


SYSTEM_PROFILE_NAMES = {
    "2-over-1": "two over one",
    "acol": "acol",
    "blue-club": "blue club",
    "carrot-club": "carrot club",
    "ehaa": "ehaa",
    "moscito": "moscito",
    "polish-club": "polish club",
    "precision": "precision",
    "roman-club": "roman club",
    "sayc": "sayc",
    "standard-american": "standard american",
    "super-precision": "super precision",
}


def classify(path: str, systems: list[str]) -> tuple[str, str, list[str]]:
    """Return confidence, reason, and conservatively proposed removals."""
    stem = Path(path).stem
    role = classify_document_role(path)
    if (
        path.startswith("bidding/systems/")
        and role is DocumentRole.ARTICLE
    ):
        own_system = SYSTEM_PROFILE_NAMES.get(stem)
        removals = [value for value in systems if value != own_system]
        reason = (
            "system_profile_cross_labels"
            if own_system
            else "system_profile_without_controlled_self_label"
        )
        return "high", reason, removals
    if role is not DocumentRole.ARTICLE:
        return "high", "index_page_reference_labels", list(systems)
    if len(systems) >= 4:
        return "medium", "broad_repeated_system_bundle", list(systems)
    return "manual", "limited_assignment_set_requires_semantic_review", []


def generate(database: Path, json_output: Path, markdown_output: Path) -> dict:
    articles = json.loads(database.read_text(encoding="utf-8"))
    entries = []
    confidence_counts: Counter[str] = Counter()
    proposed_by_confidence: Counter[str] = Counter()

    for article in articles:
        systems = article["metadata"].get("systems") or []
        if not systems:
            continue
        path = article["relative_path"]
        confidence, reason, removals = classify(path, systems)
        confidence_counts[confidence] += 1
        proposed_by_confidence[confidence] += len(removals)
        entries.append(
            {
                "path": path,
                "title": article["metadata"].get("title", ""),
                "current_systems": systems,
                "confidence": confidence,
                "reason": reason,
                "proposed_remove": removals,
                "proposed_systems": [v for v in systems if v not in removals],
            }
        )

    summary = {
        "articles_with_assignments": len(entries),
        "assignments_reviewed": sum(len(e["current_systems"]) for e in entries),
        "high_confidence_articles": confidence_counts["high"],
        "high_confidence_removals": proposed_by_confidence["high"],
        "medium_confidence_articles": confidence_counts["medium"],
        "medium_confidence_removals": proposed_by_confidence["medium"],
        "manual_review_articles": confidence_counts["manual"],
        "manual_review_assignments": sum(
            len(e["current_systems"]) for e in entries if e["confidence"] == "manual"
        ),
    }
    audit = {
        "generated": "2026-08-16",
        "status": "review_required",
        "source_changes_performed": False,
        "policy": "strict_applicability",
        "summary": summary,
        "classification_rules": {
            "high": "Cross-labels on system profiles and labels on index pages.",
            "medium": "Repeated bundles of four or more systems, characteristic of mention-based enrichment.",
            "manual": "One to three assignments needing article-level semantic review.",
        },
        "entries": entries,
    }
    json_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Systems Applicability Audit",
        "",
        "Generated: 2026-08-16  ",
        "Status: Review required  ",
        "Source changes performed: none",
        "",
        "## Summary",
        "",
        f"- {summary['assignments_reviewed']} assignments across {summary['articles_with_assignments']} articles were reviewed.",
        f"- High confidence: {summary['high_confidence_removals']} proposed removals across {summary['high_confidence_articles']} articles.",
        f"- Medium confidence: {summary['medium_confidence_removals']} proposed removals across {summary['medium_confidence_articles']} articles.",
        f"- Manual review: {summary['manual_review_assignments']} assignments across {summary['manual_review_articles']} articles.",
        "",
        "No source article was modified.",
        "",
        "## High-confidence proposals",
        "",
        "| Article | Reason | Remove | Retain |",
        "|---|---|---|---|",
    ]
    for entry in entries:
        if entry["confidence"] == "high":
            remove = ", ".join(f"`{v}`" for v in entry["proposed_remove"]) or "—"
            retain = ", ".join(f"`{v}`" for v in entry["proposed_systems"]) or "—"
            lines.append(f"| `{entry['path']}` | {entry['reason']} | {remove} | {retain} |")
    lines += [
        "",
        "## Medium-confidence proposals",
        "",
        "These repeated broad bundles are likely mention-derived, but should be approved separately from the high-confidence group.",
        "",
        "| Article | Remove |",
        "|---|---|",
    ]
    for entry in entries:
        if entry["confidence"] == "medium":
            remove = ", ".join(f"`{v}`" for v in entry["proposed_remove"])
            lines.append(f"| `{entry['path']}` | {remove} |")
    lines += [
        "",
        "## Approval boundary",
        "",
        "Approve high- and medium-confidence groups independently. Manual entries have no automatic removal proposal.",
    ]
    markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return audit


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(
        root / "output/repository.json",
        root / "output/reports/systems_applicability_audit.json",
        root / "output/reports/systems_applicability_audit.md",
    )
