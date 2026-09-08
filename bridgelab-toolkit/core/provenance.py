"""Deterministic Git provenance validation for repository artifacts and sources."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath


class ProvenanceCategory(str, Enum):
    ARTIFACT = "artifact"
    SOURCE = "source"


class ProvenanceStatus(str, Enum):
    AUTHORIZED = "authorized"
    MISSING = "missing"
    UNTRACKED = "untracked"
    DIRTY_TRACKED = "dirty-tracked"
    UNEXPECTED_PATH = "unexpected-path"
    UNAUTHORIZED_FALLBACK = "unauthorized-fallback"
    AMBIGUOUS = "ambiguous"
    IDENTITY_MISMATCH = "identity-mismatch"
    GIT_ERROR = "git-error"


class HistoricalReproducibilityStatus(str, Enum):
    REPRODUCIBLE = "reproducible"
    RECORDED_OUTPUT_ONLY = "recorded-output-only"
    SOURCE_SNAPSHOT_MISSING = "source-snapshot-missing"


@dataclass(frozen=True, slots=True)
class HistoricalReproducibility:
    output_status: HistoricalReproducibilityStatus
    source_status: HistoricalReproducibilityStatus
    reason: str
    missing_source_snapshots: tuple[str, ...] = ()


def _repository_relative(path: str) -> str:
    if "\\" in path:
        raise ValueError(
            f"provenance path must use repository-relative POSIX separators: {path!r}"
        )
    normalized = PurePosixPath(path)
    if (
        normalized.is_absolute()
        or ".." in normalized.parts
        or ":" in normalized.parts[0]
        or str(normalized) in {"", "."}
    ):
        raise ValueError(f"provenance path must be repository-relative: {path!r}")
    return normalized.as_posix()


@dataclass(frozen=True, slots=True)
class ProvenanceManifestEntry:
    logical_id: str
    category: ProvenanceCategory
    canonical_path: str
    archive_fallbacks: tuple[str, ...] = ()
    tracked_required: bool = True
    clean_required: bool = True
    provenance_commit: str | None = None
    expected_blob_oid: str | None = None

    def __post_init__(self) -> None:
        if not self.logical_id.strip():
            raise ValueError("logical provenance identifier must not be blank")
        object.__setattr__(self, "canonical_path", _repository_relative(self.canonical_path))
        object.__setattr__(
            self,
            "archive_fallbacks",
            tuple(_repository_relative(path) for path in self.archive_fallbacks),
        )
        allowed = (self.canonical_path, *self.archive_fallbacks)
        if len(set(allowed)) != len(allowed):
            raise ValueError("canonical and archive provenance paths must be unique")

    @property
    def allowed_paths(self) -> tuple[str, ...]:
        return (self.canonical_path, *self.archive_fallbacks)


@dataclass(frozen=True, slots=True)
class ProvenanceValidationResult:
    logical_id: str
    status: ProvenanceStatus
    reason: str
    resolved_path: Path | None = None
    repository_relative_path: str | None = None
    used_archive_fallback: bool = False
    tracked: bool | None = None
    clean: bool | None = None
    head_commit: str | None = None
    current_blob_oid: str | None = None
    expected_blob_oid: str | None = None

    @property
    def is_authorized(self) -> bool:
        return self.status is ProvenanceStatus.AUTHORIZED


class ProvenanceValidator:
    """Resolve only manifest-approved paths and validate their Git identity."""

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve()

    def resolve_and_validate(
        self,
        entry: ProvenanceManifestEntry,
    ) -> ProvenanceValidationResult:
        canonical = self.repository_root / entry.canonical_path
        if canonical.is_file():
            return self.validate_path(entry, canonical)

        fallbacks = [
            self.repository_root / path
            for path in entry.archive_fallbacks
            if (self.repository_root / path).is_file()
        ]
        if not fallbacks:
            return self._result(
                entry,
                ProvenanceStatus.MISSING,
                "Neither the canonical path nor an approved archive fallback exists.",
            )
        if len(fallbacks) > 1:
            names = ", ".join(
                path.relative_to(self.repository_root).as_posix() for path in fallbacks
            )
            return self._result(
                entry,
                ProvenanceStatus.AMBIGUOUS,
                f"Multiple approved archive fallbacks exist: {names}.",
            )
        return self.validate_path(entry, fallbacks[0])

    def validate_path(
        self,
        entry: ProvenanceManifestEntry,
        candidate: Path,
    ) -> ProvenanceValidationResult:
        candidate = candidate.resolve()
        try:
            relative = candidate.relative_to(self.repository_root).as_posix()
        except ValueError:
            return self._result(
                entry,
                ProvenanceStatus.UNEXPECTED_PATH,
                "Candidate path is outside the repository root.",
            )

        if relative not in entry.allowed_paths:
            status = (
                ProvenanceStatus.UNAUTHORIZED_FALLBACK
                if "archive" in PurePosixPath(relative).parts
                else ProvenanceStatus.UNEXPECTED_PATH
            )
            return self._result(
                entry,
                status,
                f"Candidate path is not authorized by the manifest: {relative}.",
            )
        if not candidate.is_file():
            return self._result(
                entry,
                ProvenanceStatus.MISSING,
                f"Authorized path does not exist: {relative}.",
            )

        try:
            head = self._git("rev-parse", "HEAD")
            tracked = self._git_is_tracked(relative)
            if entry.tracked_required and not tracked:
                return self._result(
                    entry,
                    ProvenanceStatus.UNTRACKED,
                    f"Tracked provenance is required for {relative}.",
                    candidate,
                    relative,
                    tracked=False,
                    clean=None,
                    head_commit=head,
                )

            status_output = self._git("status", "--porcelain=v1", "--", relative)
            clean = not bool(status_output)
            current_blob = self._git("hash-object", "--", relative)
            if entry.clean_required and tracked and not clean:
                return self._result(
                    entry,
                    ProvenanceStatus.DIRTY_TRACKED,
                    f"Clean committed provenance is required for {relative}.",
                    candidate,
                    relative,
                    tracked=tracked,
                    clean=False,
                    head_commit=head,
                    current_blob_oid=current_blob,
                )

            expected_blob = entry.expected_blob_oid
            if expected_blob is None and entry.provenance_commit is not None:
                expected_blob = self._git(
                    "rev-parse", f"{entry.provenance_commit}:{relative}"
                )
            if expected_blob is not None and current_blob != expected_blob:
                return self._result(
                    entry,
                    ProvenanceStatus.IDENTITY_MISMATCH,
                    f"Git blob identity does not match the enforced baseline for {relative}.",
                    candidate,
                    relative,
                    tracked=tracked,
                    clean=clean,
                    head_commit=head,
                    current_blob_oid=current_blob,
                    expected_blob_oid=expected_blob,
                )
        except (OSError, RuntimeError) as error:
            return self._result(entry, ProvenanceStatus.GIT_ERROR, str(error))

        return self._result(
            entry,
            ProvenanceStatus.AUTHORIZED,
            f"Resolved and validated {relative}.",
            candidate,
            relative,
            tracked=tracked,
            clean=clean,
            head_commit=head,
            current_blob_oid=current_blob,
            expected_blob_oid=expected_blob,
        )

    def _git(self, *arguments: str) -> str:
        completed = subprocess.run(
            ("git", "-C", str(self.repository_root), *arguments),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"Git provenance check failed: {detail}")
        return completed.stdout.strip()

    def _git_is_tracked(self, relative: str) -> bool:
        completed = subprocess.run(
            (
                "git",
                "-C",
                str(self.repository_root),
                "ls-files",
                "--error-unmatch",
                "--",
                relative,
            ),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode == 0:
            return True
        if completed.returncode == 1:
            return False
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Git provenance check failed: {detail}")

    def _result(
        self,
        entry: ProvenanceManifestEntry,
        status: ProvenanceStatus,
        reason: str,
        resolved_path: Path | None = None,
        relative_path: str | None = None,
        *,
        tracked: bool | None = None,
        clean: bool | None = None,
        head_commit: str | None = None,
        current_blob_oid: str | None = None,
        expected_blob_oid: str | None = None,
    ) -> ProvenanceValidationResult:
        return ProvenanceValidationResult(
            logical_id=entry.logical_id,
            status=status,
            reason=reason,
            resolved_path=resolved_path,
            repository_relative_path=relative_path,
            used_archive_fallback=(
                relative_path is not None and relative_path in entry.archive_fallbacks
            ),
            tracked=tracked,
            clean=clean,
            head_commit=head_commit,
            current_blob_oid=current_blob_oid,
            expected_blob_oid=expected_blob_oid,
        )
