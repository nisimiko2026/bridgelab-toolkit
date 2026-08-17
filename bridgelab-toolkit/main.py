"""
BridgeLab Toolkit
Main Application
"""

from __future__ import annotations

from pathlib import Path

import typer

from config import BACKUP_RETENTION_DAYS, REPOSITORY, REPORTS

from commands.scan import run as scan_command
from commands.debug import run as debug_command
from commands.enrich import run as enrich_command
from commands.validate import run as validate_command
from commands.metadata_audit import run as metadata_audit_command
from commands.category_impact import run as category_impact_command
from commands.repair_bidding_categories import run as repair_bidding_categories_command
from commands.repair_play_endgame_category import run as repair_play_endgame_command
from commands.repair_play_counting_category import run as repair_play_counting_command
from commands.sentinel_cleanup import run as sentinel_cleanup_command
from commands.repair_plan import run as repair_plan_command
from commands.repair_apply import run as repair_apply_command
from commands.repair_filenames import run as repair_filenames_command
from commands.resolve_duplicates import run as resolve_duplicates_command
from commands.repair_spelling import run as repair_spelling_command
from commands.repair_principles import run as repair_principles_command
from commands.repair_systems import run as repair_systems_command
from commands.backup_cleanup import run as backup_cleanup_command

from commands.statistics import run as statistics_command
from commands.coverage import run as coverage_command
from commands.orphans import run as orphans_command
from commands.orphan_plan import run as orphan_plan_command
from commands.orphan_apply import run as orphan_apply_command
from commands.duplicates import run as duplicates_command
from commands.related import run as related_command
from commands.learning_path import run as learning_path_command


# ============================================================
# Application
# ============================================================

app = typer.Typer(
    help="BridgeLab Knowledge Toolkit",
    add_completion=False,
)


# ============================================================
# Common Root Option
# ============================================================

def repository_option() -> Path:
    return typer.Option(
        REPOSITORY,
        "--root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Knowledge repository.",
    )


# ============================================================
# Repository Commands
# ============================================================

@app.command()
def scan(
    root: Path = repository_option(),
) -> None:
    """
    Scan the repository.
    """
    scan_command(root)


@app.command()
def debug(
    root: Path = repository_option(),
) -> None:
    """
    Debug the repository.
    """
    debug_command(root)


@app.command()
def enrich(
    root: Path = repository_option(),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Write enriched metadata to source articles.",
    ),
) -> None:
    """
    Enrich repository metadata.
    """
    enrich_command(root, apply=apply)


@app.command()
def validate(
    root: Path = repository_option(),
) -> None:
    """Validate repository health."""
    validate_command(root)


@app.command("metadata-audit")
def metadata_audit(
    root: Path = repository_option(),
) -> None:
    """Audit raw metadata without modifying repository files."""
    metadata_audit_command(root)


@app.command("category-impact")
def category_impact(
    root: Path = repository_option(),
    scope: str = typer.Option(
        "all",
        "--scope",
        help="Reviewed scope: all, bidding, play, or play:<topic>.",
    ),
) -> None:
    """Analyze reviewed structural category changes without writing files."""
    category_impact_command(root, scope=scope)


@app.command("repair-bidding-categories")
def repair_bidding_categories(
    root: Path = repository_option(),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "bidding-categories",
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Path-preserving backup destination; must not already exist.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Apply the reviewed category-line changes.",
    ),
) -> None:
    """Repair the 19 reviewed bidding categories; dry-run by default."""
    repair_bidding_categories_command(root, backup, apply)


@app.command("repair-play-endgame-category")
def repair_play_endgame_category(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Apply the reviewed single category-line change.",
    ),
) -> None:
    """Repair the reviewed defence-endgame category; dry-run by default."""
    repair_play_endgame_command(root, backup, apply)


@app.command("repair-play-counting-category")
def repair_play_counting_category(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Apply the reviewed single category-line change.",
    ),
) -> None:
    """Repair the reviewed defence-counting category; dry-run by default."""
    repair_play_counting_command(root, backup, apply)


@app.command("sentinel-cleanup")
def sentinel_cleanup(
    root: Path = repository_option(),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "sentinel-cleanup",
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Backup destination for applied sentinel cleanup.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Apply the exact proposed changes after creating backups.",
    ),
    only_reviewed_empty_subcategories: bool = typer.Option(
        False,
        "--only-reviewed-empty-subcategories",
        help="Limit the operation to approved intentional-empty subcategories.",
    ),
    only_reviewed_generated_reference_subcategories: bool = typer.Option(
        False,
        "--only-reviewed-generated-reference-subcategories",
        help="Limit the operation to approved generated-reference subcategories.",
    ),
) -> None:
    """Remove safe metadata sentinels without reserializing YAML."""
    sentinel_cleanup_command(
        root,
        backup,
        apply,
        only_reviewed_empty_subcategories=only_reviewed_empty_subcategories,
        only_reviewed_generated_reference_subcategories=(
            only_reviewed_generated_reference_subcategories
        ),
    )


@app.command("repair-plan")
def repair_plan(
    root: Path = repository_option(),
    output_directory: Path = typer.Option(
        REPORTS,
        "--output-directory",
        file_okay=False,
        resolve_path=True,
        help="Directory for JSON and Markdown repair plans.",
    ),
) -> None:
    """Generate read-only metadata repair proposals."""
    repair_plan_command(root, output_directory)


@app.command("repair-apply")
def repair_apply(
    root: Path = repository_option(),
    plan: Path = typer.Option(
        REPORTS / "metadata_repair_plan.json",
        "--plan",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "metadata-repair",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
    include_low_confidence: bool = typer.Option(
        False,
        "--include-low-confidence",
        help="Apply low-confidence proposals after explicit editorial review.",
    ),
) -> None:
    """Apply medium/high-confidence repairs after backing up source files."""
    repair_apply_command(
        root,
        plan,
        backup,
        apply,
        include_low_confidence=include_low_confidence,
    )


@app.command("repair-filenames")
def repair_filenames(
    root: Path = repository_option(),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "filename-repair",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
) -> None:
    """Rename known invalid files and update exact inbound references."""
    repair_filenames_command(root, backup, apply)


@app.command("repair-spelling")
def repair_spelling(
    root: Path = repository_option(),
    plan: Path = typer.Option(
        REPORTS / "spelling_rename_audit.json",
        "--plan",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "spelling-repair",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
    include_medium_confidence: bool = typer.Option(
        False,
        "--include-medium-confidence",
        help="Include the reviewed natural-rebids index rename.",
    ),
) -> None:
    """Apply audited spelling corrections with backups."""
    repair_spelling_command(
        root,
        plan,
        backup,
        apply,
        include_medium_confidence=include_medium_confidence,
    )


@app.command("repair-principles")
def repair_principles(
    root: Path = repository_option(),
    plan: Path = typer.Option(
        REPORTS / "principles_migration_plan.json",
        "--plan",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "principles-migration",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
    include_medium_confidence: bool = typer.Option(
        False,
        "--include-medium-confidence",
        help="Rename the partnership index to partnership-principles-index.md.",
    ),
) -> None:
    """Apply the reviewed principles terminology migration with backups."""
    repair_principles_command(
        root,
        plan,
        backup,
        apply,
        include_medium_confidence=include_medium_confidence,
    )


@app.command("repair-systems")
def repair_systems(
    root: Path = repository_option(),
    plan: Path = typer.Option(
        REPORTS / "systems_removal_plan.json",
        "--plan",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "systems-removal",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
) -> None:
    """Apply the reviewed removal-first systems metadata plan."""
    repair_systems_command(root, plan, backup, apply)


@app.command("resolve-duplicates")
def resolve_duplicates(
    root: Path = repository_option(),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "duplicate-resolution",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
) -> None:
    """Apply the reviewed duplicate filename resolution."""
    resolve_duplicates_command(root, backup, apply)


@app.command("cleanup-backups")
def cleanup_backups(
    backup_root: Path = typer.Option(
        REPORTS.parent / "backups",
        "--backup-root",
        exists=True,
        file_okay=False,
        resolve_path=True,
        help="Directory containing dated repair backup directories.",
    ),
    retention_days: int = typer.Option(
        BACKUP_RETENTION_DAYS,
        "--retention-days",
        min=1,
        help="Keep dated backups for this many full days.",
    ),
    apply: bool = typer.Option(False, "--apply"),
) -> None:
    """List or remove dated backups older than the retention period."""
    backup_cleanup_command(backup_root, retention_days, apply)


# ============================================================
# Analysis Commands
# ============================================================

@app.command()
def statistics(
    root: Path = repository_option(),
) -> None:
    """
    Display repository statistics.
    """
    statistics_command(root)


@app.command()
def coverage(
    root: Path = repository_option(),
) -> None:
    """
    Display repository coverage.
    """
    coverage_command(root)


@app.command()
def orphans(
    root: Path = repository_option(),
) -> None:
    """
    Display orphan articles.
    """
    orphans_command(root)


@app.command("orphan-plan")
def orphan_plan(
    root: Path = repository_option(),
    output_directory: Path = typer.Option(
        REPORTS,
        "--output-directory",
        file_okay=False,
        resolve_path=True,
        help="Directory for JSON and Markdown orphan repair plans.",
    ),
) -> None:
    """Generate read-only parent-index proposals for orphan articles."""
    orphan_plan_command(root, output_directory)


@app.command("orphan-apply")
def orphan_apply(
    root: Path = repository_option(),
    plan: Path = typer.Option(
        REPORTS / "orphan_repair_plan.json",
        "--plan",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "orphan-repair",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
    include_medium_confidence: bool = typer.Option(
        False,
        "--include-medium-confidence",
        help="Include reviewed nearest-ancestor index proposals.",
    ),
) -> None:
    """Apply approved parent-index references with backups."""
    orphan_apply_command(
        root,
        plan,
        backup,
        apply,
        include_medium_confidence=include_medium_confidence,
    )


@app.command()
def duplicates(
    root: Path = repository_option(),
) -> None:
    """
    Display duplicate articles.
    """
    duplicates_command(root)


@app.command()
def related(
    article: str = typer.Argument(
        ...,
        help="Article ID or path.",
    ),
    root: Path = repository_option(),
) -> None:
    """
    Display related articles.
    """
    related_command(root, article)


@app.command("learning-path")
def learning_path(
    article: str = typer.Argument(
        ...,
        help="Article ID or path.",
    ),
    root: Path = repository_option(),
) -> None:
    """
    Display a learning path.
    """
    learning_path_command(root, article)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    app()
