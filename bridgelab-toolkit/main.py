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
from commands.repair_play_principles_categories import (
    run as repair_play_principles_command,
)
from commands.repair_play_trump_play_categories import run as repair_play_trump_command
from commands.repair_play_signaling_category import run as repair_play_signaling_command
from commands.repair_play_probability_category import (
    run as repair_play_probability_command,
)
from commands.repair_play_defence_techniques_categories import (
    run as repair_play_defence_techniques_command,
)
from commands.repair_play_endplays_categories import run as repair_play_endplays_command
from commands.repair_play_coups_categories import run as repair_play_coups_command
from commands.repair_play_finesses_categories import run as repair_play_finesses_command
from commands.repair_play_general_techniques_categories import (
    run as repair_play_general_techniques_command,
)
from commands.repair_play_declarer_deception_categories import (
    run as repair_play_declarer_deception_command,
)
from commands.repair_play_declarer_notrump_categories import (
    run as repair_play_declarer_notrump_command,
)
from commands.repair_play_declarer_squeezes_categories import (
    run as repair_play_declarer_squeezes_command,
)
from commands.repair_play_defence_planning_category import (
    run as repair_play_defence_planning_command,
)
from commands.repair_play_defence_opening_leads_categories import (
    run as repair_play_defence_opening_leads_command,
)
from commands.repair_category_normalization_batch1 import (
    run as repair_category_normalization_batch1_command,
)
from commands.repair_category_normalization_batch2 import (
    run as repair_category_normalization_batch2_command,
)
from commands.repair_category_normalization_batch3_1 import (
    run as repair_category_normalization_batch3_1_command,
)
from commands.repair_category_normalization_batch3_2 import (
    run as repair_category_normalization_batch3_2_command,
)
from commands.repair_category_normalization_batch3_3a import (
    run as repair_category_normalization_batch3_3a_command,
)
from commands.repair_category_normalization_batch3_3b import (
    run as repair_category_normalization_batch3_3b_command,
)
from commands.repair_category_normalization_batch3_3c import (
    run as repair_category_normalization_batch3_3c_command,
)
from commands.repair_category_normalization_batch3_3d import (
    run as repair_category_normalization_batch3_3d_command,
)
from commands.repair_category_normalization_batch3_3e import (
    run as repair_category_normalization_batch3_3e_command,
)
from commands.repair_category_normalization_batch3_3f import (
    run as repair_category_normalization_batch3_3f_command,
)
from commands.repair_category_normalization_batch3_3g import (
    run as repair_category_normalization_batch3_3g_command,
)
from commands.repair_category_normalization_batch3_3h import (
    run as repair_category_normalization_batch3_3h_command,
)
from commands.repair_category_normalization_batch3_3i import (
    run as repair_category_normalization_batch3_3i_command,
)
from commands.repair_category_normalization_batch3_3j import (
    run as repair_category_normalization_batch3_3j_command,
)
from commands.repair_category_normalization_batch3_3k import (
    run as repair_category_normalization_batch3_3k_command,
)
from commands.repair_category_normalization_batch3_3l import (
    run as repair_category_normalization_batch3_3l_command,
)
from commands.repair_category_normalization_batch3_3m import (
    run as repair_category_normalization_batch3_3m_command,
)
from commands.repair_category_normalization_batch3_3n import (
    run as repair_category_normalization_batch3_3n_command,
)
from commands.repair_category_normalization_batch3_3o import (
    run as repair_category_normalization_batch3_3o_command,
)
from commands.repair_category_normalization_batch3_3p import (
    run as repair_category_normalization_batch3_3p_command,
)
from commands.repair_category_normalization_batch3_3q import (
    run as repair_category_normalization_batch3_3q_command,
)
from commands.repair_category_normalization_batch3_3r import (
    run as repair_category_normalization_batch3_3r_command,
)
from commands.repair_category_normalization_batch3_3s1 import (
    run as repair_category_normalization_batch3_3s1_command,
)
from commands.repair_category_normalization_batch3_3s2 import (
    run as repair_category_normalization_batch3_3s2_command,
)
from commands.repair_category_normalization_batch3_3t import (
    run as repair_category_normalization_batch3_3t_command,
)
from commands.repair_category_normalization_batch3_3u import (
    run as repair_category_normalization_batch3_3u_command,
)
from commands.repair_category_normalization_batch3_3v import (
    run as repair_category_normalization_batch3_3v_command,
)
from commands.repair_category_normalization_batch3_3w import (
    run as repair_category_normalization_batch3_3w_command,
)
from commands.repair_category_normalization_batch3_3x import (
    run as repair_category_normalization_batch3_3x_command,
)
from commands.repair_category_normalization_batch3_3y import (
    run as repair_category_normalization_batch3_3y_command,
)
from commands.repair_category_normalization_batch3_3z import (
    run as repair_category_normalization_batch3_3z_command,
)
from commands.repair_category_normalization_batch3_3aa import (
    run as repair_category_normalization_batch3_3aa_command,
)
from commands.repair_category_normalization_batch3_3ab import (
    run as repair_category_normalization_batch3_3ab_command,
)
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


@app.command("repair-category-normalization-batch1")
def repair_category_normalization_batch1(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed six-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 1; dry-run by default."""
    repair_category_normalization_batch1_command(root, backup, apply)


@app.command("repair-category-normalization-batch2")
def repair_category_normalization_batch2(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed four-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 2; dry-run by default."""
    repair_category_normalization_batch2_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-1")
def repair_category_normalization_batch3_1(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed two-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.1; dry-run by default."""
    repair_category_normalization_batch3_1_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-2")
def repair_category_normalization_batch3_2(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed eight-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.2; dry-run by default."""
    repair_category_normalization_batch3_2_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3a")
def repair_category_normalization_batch3_3a(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed single-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3a; dry-run by default."""
    repair_category_normalization_batch3_3a_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3b")
def repair_category_normalization_batch3_3b(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed two-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3b; dry-run by default."""
    repair_category_normalization_batch3_3b_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3c")
def repair_category_normalization_batch3_3c(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed three-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3c; dry-run by default."""
    repair_category_normalization_batch3_3c_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3d")
def repair_category_normalization_batch3_3d(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed two-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3d; dry-run by default."""
    repair_category_normalization_batch3_3d_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3e")
def repair_category_normalization_batch3_3e(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed six-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3e; dry-run by default."""
    repair_category_normalization_batch3_3e_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3f")
def repair_category_normalization_batch3_3f(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed one-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3f; dry-run by default."""
    repair_category_normalization_batch3_3f_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3g")
def repair_category_normalization_batch3_3g(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed two-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3g; dry-run by default."""
    repair_category_normalization_batch3_3g_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3h")
def repair_category_normalization_batch3_3h(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed one-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3h; dry-run by default."""
    repair_category_normalization_batch3_3h_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3i")
def repair_category_normalization_batch3_3i(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed 20-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3i; dry-run by default."""
    repair_category_normalization_batch3_3i_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3j")
def repair_category_normalization_batch3_3j(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed 15-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3j; dry-run by default."""
    repair_category_normalization_batch3_3j_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3k")
def repair_category_normalization_batch3_3k(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed ten-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3k; dry-run by default."""
    repair_category_normalization_batch3_3k_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3l")
def repair_category_normalization_batch3_3l(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed five-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3l; dry-run by default."""
    repair_category_normalization_batch3_3l_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3m")
def repair_category_normalization_batch3_3m(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed 13-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3m; dry-run by default."""
    repair_category_normalization_batch3_3m_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3n")
def repair_category_normalization_batch3_3n(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed 13-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3n; dry-run by default."""
    repair_category_normalization_batch3_3n_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3o")
def repair_category_normalization_batch3_3o(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed 17-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3o; dry-run by default."""
    repair_category_normalization_batch3_3o_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3p")
def repair_category_normalization_batch3_3p(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed 16-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3p; dry-run by default."""
    repair_category_normalization_batch3_3p_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3q")
def repair_category_normalization_batch3_3q(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed four-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3q; dry-run by default."""
    repair_category_normalization_batch3_3q_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3r")
def repair_category_normalization_batch3_3r(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed nine-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3r; dry-run by default."""
    repair_category_normalization_batch3_3r_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3s1")
def repair_category_normalization_batch3_3s1(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed one-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3s1; dry-run by default."""
    repair_category_normalization_batch3_3s1_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3s2")
def repair_category_normalization_batch3_3s2(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed one-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3s2; dry-run by default."""
    repair_category_normalization_batch3_3s2_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3t")
def repair_category_normalization_batch3_3t(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed one-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3t; dry-run by default."""
    repair_category_normalization_batch3_3t_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3u")
def repair_category_normalization_batch3_3u(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed 17-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3u; dry-run by default."""
    repair_category_normalization_batch3_3u_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3v")
def repair_category_normalization_batch3_3v(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed four-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3v; dry-run by default."""
    repair_category_normalization_batch3_3v_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3w")
def repair_category_normalization_batch3_3w(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed three-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3w; dry-run by default."""
    repair_category_normalization_batch3_3w_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3x")
def repair_category_normalization_batch3_3x(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit fresh path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed one-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3x; dry-run by default."""
    repair_category_normalization_batch3_3x_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3y")
def repair_category_normalization_batch3_3y(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None, "--backup", help="Fresh path-preserving backup directory (required with --apply)."
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed one-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3y; dry-run by default."""
    repair_category_normalization_batch3_3y_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3z")
def repair_category_normalization_batch3_3z(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None, "--backup", help="Fresh path-preserving backup directory (required with --apply)."
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed one-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3z; dry-run by default."""
    repair_category_normalization_batch3_3z_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3aa")
def repair_category_normalization_batch3_3aa(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None, "--backup", help="Fresh path-preserving backup directory (required with --apply)."
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed three-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3aa; dry-run by default."""
    repair_category_normalization_batch3_3aa_command(root, backup, apply)


@app.command("repair-category-normalization-batch3-3ab")
def repair_category_normalization_batch3_3ab(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None, "--backup", help="Fresh path-preserving backup directory (required with --apply)."
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed two-file category-line batch."
    ),
) -> None:
    """Repair Phase 3A category normalization Batch 3.3ab; dry-run by default."""
    repair_category_normalization_batch3_3ab_command(root, backup, apply)


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


@app.command("repair-play-principles-categories")
def repair_play_principles_categories(
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
        help="Apply the reviewed two-file category-line batch.",
    ),
) -> None:
    """Repair reviewed play-principles categories; dry-run by default."""
    repair_play_principles_command(root, backup, apply)


@app.command("repair-play-trump-play-categories")
def repair_play_trump_play_categories(
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
        help="Apply the reviewed four-file category-line batch.",
    ),
) -> None:
    """Repair reviewed declarer trump-play categories; dry-run by default."""
    repair_play_trump_command(root, backup, apply)


@app.command("repair-play-signaling-category")
def repair_play_signaling_category(
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
    """Repair the reviewed defence-signaling category; dry-run by default."""
    repair_play_signaling_command(root, backup, apply)


@app.command("repair-play-probability-category")
def repair_play_probability_category(
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
    """Repair the reviewed declarer-probability category; dry-run by default."""
    repair_play_probability_command(root, backup, apply)


@app.command("repair-play-defence-techniques-categories")
def repair_play_defence_techniques_categories(
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
        help="Apply the reviewed two-file category-line batch.",
    ),
) -> None:
    """Repair reviewed defence-techniques categories; dry-run by default."""
    repair_play_defence_techniques_command(root, backup, apply)


@app.command("repair-play-endplays-categories")
def repair_play_endplays_categories(
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
        help="Apply the reviewed three-file category-line batch.",
    ),
) -> None:
    """Repair reviewed declarer-endplays categories; dry-run by default."""
    repair_play_endplays_command(root, backup, apply)


@app.command("repair-play-coups-categories")
def repair_play_coups_categories(
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
        help="Apply the reviewed four-file category-line batch.",
    ),
) -> None:
    """Repair reviewed declarer-coups categories; dry-run by default."""
    repair_play_coups_command(root, backup, apply)


@app.command("repair-play-finesses-categories")
def repair_play_finesses_categories(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed seven-file batch."
    ),
) -> None:
    """Repair reviewed declarer-finesses categories; dry-run by default."""
    repair_play_finesses_command(root, backup, apply)


@app.command("repair-play-general-techniques-categories")
def repair_play_general_techniques_categories(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed three-file category-line batch."
    ),
) -> None:
    """Repair reviewed declarer general-techniques categories; dry-run by default."""
    repair_play_general_techniques_command(root, backup, apply)


@app.command("repair-play-declarer-deception-categories")
def repair_play_declarer_deception_categories(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed five-file category-line batch."
    ),
) -> None:
    """Repair reviewed declarer-deception categories; dry-run by default."""
    repair_play_declarer_deception_command(root, backup, apply)


@app.command("repair-play-declarer-notrump-categories")
def repair_play_declarer_notrump_categories(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed eight-file category-line batch."
    ),
) -> None:
    """Repair reviewed declarer-notrump categories; dry-run by default."""
    repair_play_declarer_notrump_command(root, backup, apply)


@app.command("repair-play-declarer-squeezes-categories")
def repair_play_declarer_squeezes_categories(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed ten-file category-line batch."
    ),
) -> None:
    """Repair reviewed declarer-squeezes categories; dry-run by default."""
    repair_play_declarer_squeezes_command(root, backup, apply)


@app.command("repair-play-defence-planning-category")
def repair_play_defence_planning_category(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed single category-line change."
    ),
) -> None:
    """Repair the reviewed defence-planning category; dry-run by default."""
    repair_play_defence_planning_command(root, backup, apply)


@app.command("repair-play-defence-opening-leads-categories")
def repair_play_defence_opening_leads_categories(
    root: Path = repository_option(),
    backup: Path | None = typer.Option(
        None,
        "--backup",
        file_okay=False,
        resolve_path=True,
        help="Required explicit path-preserving backup destination with --apply.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the reviewed ten-file category-line batch."
    ),
) -> None:
    """Repair reviewed defence opening-leads categories; dry-run by default."""
    repair_play_defence_opening_leads_command(root, backup, apply)


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
