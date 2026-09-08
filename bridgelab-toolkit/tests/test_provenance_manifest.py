from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from benchmarks.phase17b_declarer_source_enrichment_audit import (
    BRIDGELAB_ROOT,
    PHASE17A_MANIFEST,
    _load_phase17a,
)
from core.provenance import (
    ProvenanceCategory,
    ProvenanceManifestEntry,
    ProvenanceStatus,
    ProvenanceValidator,
)


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "--quiet")
    _git(tmp_path, "config", "user.email", "provenance@example.invalid")
    _git(tmp_path, "config", "user.name", "Provenance Test")
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "phase17.json").write_text("{}", encoding="utf-8")
    _git(tmp_path, "add", "reports/phase17.json")
    _git(tmp_path, "commit", "--quiet", "-m", "baseline")
    return tmp_path


def _entry(**changes: object) -> ProvenanceManifestEntry:
    values: dict[str, object] = {
        "logical_id": "phase17-report",
        "category": ProvenanceCategory.ARTIFACT,
        "canonical_path": "reports/phase17.json",
    }
    values.update(changes)
    return ProvenanceManifestEntry(**values)  # type: ignore[arg-type]


def test_resolves_clean_tracked_canonical_path(repository: Path) -> None:
    result = ProvenanceValidator(repository).resolve_and_validate(_entry())
    assert result.status is ProvenanceStatus.AUTHORIZED
    assert result.repository_relative_path == "reports/phase17.json"
    assert not result.used_archive_fallback
    assert result.tracked and result.clean
    assert result.current_blob_oid


def test_resolves_only_approved_archive_fallback(repository: Path) -> None:
    (repository / "archive" / "phase17").mkdir(parents=True)
    _git(repository, "mv", "reports/phase17.json", "archive/phase17/phase17.json")
    _git(repository, "commit", "--quiet", "-m", "archive")
    result = ProvenanceValidator(repository).resolve_and_validate(
        _entry(archive_fallbacks=("archive/phase17/phase17.json",))
    )
    assert result.status is ProvenanceStatus.AUTHORIZED
    assert result.repository_relative_path == "archive/phase17/phase17.json"
    assert result.used_archive_fallback


def test_rejects_missing_artifact(repository: Path) -> None:
    result = ProvenanceValidator(repository).resolve_and_validate(
        _entry(canonical_path="reports/missing.json")
    )
    assert result.status is ProvenanceStatus.MISSING


@pytest.mark.parametrize(
    "path",
    ("../outside.json", "..\\outside.json", "C:/outside.json", "C:\\outside.json"),
)
def test_rejects_repository_escape_syntax(path: str) -> None:
    with pytest.raises(ValueError):
        _entry(canonical_path=path)


def test_rejects_unapproved_archive_fallback(repository: Path) -> None:
    archive = repository / "archive" / "other" / "phase17.json"
    archive.parent.mkdir(parents=True)
    archive.write_text("{}", encoding="utf-8")
    result = ProvenanceValidator(repository).validate_path(_entry(), archive)
    assert result.status is ProvenanceStatus.UNAUTHORIZED_FALLBACK


def test_rejects_ambiguous_approved_fallbacks(repository: Path) -> None:
    (repository / "reports" / "phase17.json").unlink()
    for relative in ("archive/phase17/a.json", "archive/phase17/b.json"):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    result = ProvenanceValidator(repository).resolve_and_validate(
        _entry(
            archive_fallbacks=(
                "archive/phase17/a.json",
                "archive/phase17/b.json",
            )
        )
    )
    assert result.status is ProvenanceStatus.AMBIGUOUS


def test_rejects_dirty_tracked_source(repository: Path) -> None:
    source = repository / "reports" / "phase17.json"
    source.write_text('{"dirty": true}', encoding="utf-8")
    result = ProvenanceValidator(repository).resolve_and_validate(
        _entry(category=ProvenanceCategory.SOURCE)
    )
    assert result.status is ProvenanceStatus.DIRTY_TRACKED


def test_rejects_untracked_source(repository: Path) -> None:
    source = repository / "sources" / "untracked.md"
    source.parent.mkdir()
    source.write_text("source", encoding="utf-8")
    result = ProvenanceValidator(repository).resolve_and_validate(
        _entry(
            category=ProvenanceCategory.SOURCE,
            canonical_path="sources/untracked.md",
        )
    )
    assert result.status is ProvenanceStatus.UNTRACKED


def test_rejects_enforced_blob_identity_mismatch(repository: Path) -> None:
    result = ProvenanceValidator(repository).resolve_and_validate(
        _entry(expected_blob_oid="0" * 40)
    )
    assert result.status is ProvenanceStatus.IDENTITY_MISMATCH


def test_reports_git_unavailable_as_git_error(repository: Path) -> None:
    with patch("core.provenance.subprocess.run", side_effect=FileNotFoundError("git")):
        result = ProvenanceValidator(repository).resolve_and_validate(_entry())
    assert result.status is ProvenanceStatus.GIT_ERROR


def test_phase17b_loads_phase17a_report_from_approved_archive() -> None:
    result = ProvenanceValidator(BRIDGELAB_ROOT).resolve_and_validate(
        PHASE17A_MANIFEST
    )
    assert result.status is ProvenanceStatus.AUTHORIZED
    assert result.used_archive_fallback
    assert result.repository_relative_path == (
        "bridgelab-toolkit/archive/phase17/"
        "bridgelab_phase17a_bridge_intelligence_source_readiness_audit.json"
    )
    assert _load_phase17a()["total_candidates"] == 38
