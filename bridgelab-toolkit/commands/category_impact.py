"""Console reporting for read-only structural category impact analysis."""

from __future__ import annotations

from pathlib import Path

import typer

from analysis.category_impact import analyze_category_impact
from core.repository import Repository


def run(root: Path) -> None:
    """Analyze reviewed structural category changes without writing files."""

    report = analyze_category_impact(Repository(root).build())
    typer.echo("BridgeLab Category Impact (read-only)")
    typer.echo()
    typer.echo("Per-file impact")
    for item in report.items:
        typer.echo(
            f"{item.path} | category={item.current_category!r} -> "
            f"{item.proposed_category!r} | subcategory={item.subcategory!r} | "
            f"old-tag={item.old_tag!r} present={item.old_tag_present} | "
            f"canonical-present={item.canonical_tag_present} | action={item.tag_action}"
        )

    typer.echo()
    typer.echo("Category impact")
    typer.echo(f"Repository articles             : {report.article_count}")
    typer.echo(f"Selected structural files       : {len(report.items)}")
    typer.echo(f"bidding population              : {report.bidding_before} -> {report.bidding_after}")
    typer.echo(f"play population                 : {report.play_before} -> {report.play_after}")
    typer.echo(
        f"Distinct category values         : {report.distinct_categories_before} -> "
        f"{report.distinct_categories_after}"
    )
    typer.echo(f"Structural findings eliminated  : {report.structural_findings_eliminated}")
    typer.echo(f"Provisional findings affected   : {report.provisional_findings_affected}")
    typer.echo(f"Path disagreements affected     : {report.path_disagreements_affected}")

    typer.echo()
    typer.echo("Tag impact")
    typer.echo(f"Old derived tags present        : {report.old_tags_present}")
    typer.echo(f"Canonical tags already present  : {report.canonical_tags_present}")
    typer.echo(f"Old tags becoming stale         : {report.stale_tags}")
    typer.echo(f"Canonical tags to add           : {report.canonical_tags_to_add}")
    typer.echo(f"Duplicate-tag risk              : {report.duplicate_tag_risk}")
    typer.echo(f"Structural tag findings removed : {report.structural_tag_findings_eliminated}")
    for old, new, count in report.tag_mappings:
        typer.echo(f"  {old!r} -> {new!r}: {count}")

    typer.echo()
    typer.echo("Related-ranking impact (top 10)")
    typer.echo(f"Category-match pairs changed    : {report.category_pairs_changed}")
    typer.echo(f"Category-match pairs added      : {report.category_pairs_added}")
    typer.echo(f"Category-match pairs removed    : {report.category_pairs_removed}")
    typer.echo(
        "Category-only ordering/set      : "
        f"{report.category_only_ranking.ordering_changed}/"
        f"{report.category_only_ranking.top_set_changed}"
    )
    typer.echo(
        "Category+tag ordering/set       : "
        f"{report.reconciled_ranking.ordering_changed}/"
        f"{report.reconciled_ranking.top_set_changed}"
    )
    typer.echo(
        "Incremental tag ordering/set    : "
        f"{report.tag_reconciliation_ranking.ordering_changed}/"
        f"{report.tag_reconciliation_ranking.top_set_changed}"
    )
    typer.echo(
        "Stale-tag removal ordering/set  : "
        f"{report.stale_tag_removal_ranking.ordering_changed}/"
        f"{report.stale_tag_removal_ranking.top_set_changed}"
    )
    typer.echo(
        "Canonical-tag add ordering/set  : "
        f"{report.canonical_tag_addition_ranking.ordering_changed}/"
        f"{report.canonical_tag_addition_ranking.top_set_changed}"
    )
    typer.echo(f"Pairs increased by canonical tag: {report.tag_pair_scores_increased}")
    typer.echo(f"Pairs decreased by stale removal: {report.tag_pair_scores_decreased}")
    for path, changed, score_delta in report.largest_ranking_impacts:
        typer.echo(f"  {path}: set-difference={changed}, top-score delta={score_delta:+d}")

    typer.echo()
    typer.echo("Relationship/cross-reference impact")
    typer.echo(f"Category edges                  : {report.category_edges_before} -> {report.category_edges_after}")
    typer.echo(f"Edges added/removed             : {report.category_edges_added}/{report.category_edges_removed}")
    typer.echo(f"Affected articles               : {report.relationship_articles_affected}")
    typer.echo(f"Cross-reference sets changed    : {report.crossref_candidate_sets_changed}")

    typer.echo()
    typer.echo("Repair/statistics/orphan impact")
    typer.echo(f"Repairable missing difficulty   : {report.repairable_missing_difficulty}")
    typer.echo(f"Repair fallback changes         : {report.repair_fallback_changes}")
    typer.echo(f"Orphan category groups          : {report.orphan_groups_before} -> {report.orphan_groups_after}")
    typer.echo(f"Orphan articles regrouped       : {report.orphan_articles_regrouped}")
    typer.echo(f"Orphan bidding population       : {report.orphan_bidding_before} -> {report.orphan_bidding_after}")
    typer.echo(f"Orphan play population          : {report.orphan_play_before} -> {report.orphan_play_after}")
    typer.echo()
    typer.secho("No source files were modified.", fg=typer.colors.YELLOW)
