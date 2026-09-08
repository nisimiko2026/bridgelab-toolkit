"""Blob-pinned validation of recorded Phase 17 outputs.

This module authenticates historical artifacts.  It deliberately does not claim
to recompute conclusions whose original source snapshots were not preserved.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from core.provenance import (
    HistoricalReproducibility,
    HistoricalReproducibilityStatus,
    ProvenanceCategory,
    ProvenanceManifestEntry,
    ProvenanceStatus,
    ProvenanceValidationResult,
    ProvenanceValidator,
)

BASELINE_COMMIT = "5c61e35"
GIT_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_PREFIX = "bridgelab-toolkit/archive/phase17"

_REPORTS = {
    "17C": (
        "bridgelab_phase17c_safety_play_blocker_audit.json",
        "a683de1536d45507491503e401ddbd202e2e5e52",
    ),
    "17D": (
        "bridgelab_phase17d_restricted_choice_source_enrichment_audit.json",
        "6dff869a025779e86293f2e946b4e019a21bcbd1",
    ),
    "17E": (
        "bridgelab_phase17e_restricted_choice_source_reconciliation_audit.json",
        "09f4772d9aa5996a122516151bb5fb232c4dec7b",
    ),
    "17F": (
        "bridgelab_phase17f_restricted_choice_contract_enrichment_audit.json",
        "3d8c6783011824b355c3c2954fded065d58e1b21",
    ),
    "17G": (
        "bridgelab_phase17g_restricted_choice_supporting_source_audit.json",
        "f7b6ed3b6fda83907231ba36c7053cc3edef8a8d",
    ),
    "17H": (
        "bridgelab_phase17h_restricted_choice_contract_gap_resolution_audit.json",
        "7d0f46932ff859da38f9a507cb93270b429d8be3",
    ),
    "17I": (
        "bridgelab_phase17i_restricted_choice_contract_enrichment_audit.json",
        "9fda598589756639320fc5028f464d4e105ba615",
    ),
    "17J": (
        "bridgelab_phase17j_restricted_choice_contract_enrichment_audit.json",
        "ff50fe73a13a61c624be1b7e3b5033304dbf567f",
    ),
    "17K": (
        "bridgelab_phase17k_restricted_choice_close_defer_audit.json",
        "95bbfe55448eca833145baed278226b1046cd54f",
    ),
}

PHASE17_HISTORICAL_REPORT_MANIFEST = {
    phase: ProvenanceManifestEntry(
        logical_id=f"phase{phase.lower()}.historical-recorded-output",
        category=ProvenanceCategory.ARTIFACT,
        canonical_path=f"{ARCHIVE_PREFIX}/{filename}",
        provenance_commit=BASELINE_COMMIT,
        expected_blob_oid=blob_oid,
    )
    for phase, (filename, blob_oid) in _REPORTS.items()
}

PHASE17C_FULL_KIT_MANIFEST = ProvenanceManifestEntry(
    logical_id="phase17c.full-kit",
    category=ProvenanceCategory.ARTIFACT,
    canonical_path=f"{ARCHIVE_PREFIX}/bridgelab_phase17c_full_kit.zip",
    provenance_commit=BASELINE_COMMIT,
    expected_blob_oid="fe74ef953d2b967603bd8e011108cccd649dc5e4",
)
PHASE17C_BACKUP_MEMBER = (
    "bridgelab-toolkit/output/backups/spelling-repair-20260816-01/"
    "play/declarer-play/probabilty/vacant-places.md"
)
PHASE17C_BACKUP_MEMBER_BLOB = "5e7b3b70f9a7488beee9412b67f2e9be366a22c3"

MISSING_SOURCE_SNAPSHOTS = (
    "knowledge/play/declarer-play/probability/percentage-plays.md@phase17",
    "knowledge/play/counting/vacant-places.md@phase17",
    "knowledge/play/declarer-play/general-techniques/restricted-choice.md@phase17",
    (
        "knowledge/play/declarer-play/probability/finesse/"
        "a8732-vs-k1065-restricted-choice.md@phase17"
    ),
    "knowledge/play/principles/eight-ever-nine-never.md@phase17-modified",
    "knowledge/references/bridge-glossary.md@phase17-modified",
    "knowledge/references/bridge-terminology.md@phase17-modified",
    "knowledge/references/common-bridge-abbreviations.md@phase17-modified",
)

CURRENT_REQUIRED_SOURCE_PATHS = tuple(
    value.split("@", 1)[0] for value in MISSING_SOURCE_SNAPSHOTS[:4]
)


@dataclass(frozen=True, slots=True)
class HistoricalReportValidation:
    phase: str
    artifact: ProvenanceValidationResult
    reproducibility: HistoricalReproducibility
    payload: dict[str, Any] | None
    validation_errors: tuple[str, ...]

    @property
    def is_valid_recorded_output(self) -> bool:
        return self.artifact.is_authorized and not self.validation_errors


@dataclass(frozen=True, slots=True)
class ZipMemberValidation:
    artifact: ProvenanceValidationResult
    member_path: str
    status: ProvenanceStatus
    reason: str
    member_blob_oid: str | None = None
    content: bytes | None = None

    @property
    def is_authorized(self) -> bool:
        return self.status is ProvenanceStatus.AUTHORIZED


@dataclass(frozen=True, slots=True)
class CurrentSourceReadiness:
    """Truthful source availability in the current clean project checkout."""

    status: HistoricalReproducibilityStatus
    missing_paths: tuple[str, ...]
    available_paths: tuple[str, ...]

    @property
    def is_source_reproducible(self) -> bool:
        return not self.missing_paths


def current_phase17_source_readiness(
    *,
    project_root: Path = Path(__file__).resolve().parents[1],
) -> CurrentSourceReadiness:
    missing = tuple(
        path for path in CURRENT_REQUIRED_SOURCE_PATHS if not (project_root / path).is_file()
    )
    available = tuple(
        path for path in CURRENT_REQUIRED_SOURCE_PATHS if (project_root / path).is_file()
    )
    status = (
        HistoricalReproducibilityStatus.REPRODUCIBLE
        if not missing
        else HistoricalReproducibilityStatus.SOURCE_SNAPSHOT_MISSING
    )
    return CurrentSourceReadiness(status, missing, available)


def _recorded_output_reproducibility() -> HistoricalReproducibility:
    return HistoricalReproducibility(
        output_status=HistoricalReproducibilityStatus.RECORDED_OUTPUT_ONLY,
        source_status=HistoricalReproducibilityStatus.SOURCE_SNAPSHOT_MISSING,
        reason=(
            "The archived output is authentic and blob-pinned, but required "
            "Phase 17 source snapshots were not preserved."
        ),
        missing_source_snapshots=MISSING_SOURCE_SNAPSHOTS,
    )


def validate_historical_payload(
    phase: str,
    payload: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    if payload.get("phase") != phase:
        errors.append(
            f"phase mismatch: expected {phase}, observed {payload.get('phase')!r}"
        )
    if payload.get("source_executable") is not False:
        errors.append("recorded source_executable must remain false")
    if payload.get("production_implementation_authorized") is not False:
        errors.append("recorded production authorization must remain false")
    if payload.get("new_production_recommendations") != 0:
        errors.append("recorded new production recommendations must remain zero")

    gates = payload.get("gate_results", payload.get("gates"))
    if not isinstance(gates, list) or not gates:
        errors.append("recorded gate payload is missing or empty")

    if phase == "17C":
        if payload.get("classification_after") != "SOURCE_PARTIAL":
            errors.append("Phase 17C classification must remain SOURCE_PARTIAL")
        if payload.get("registered_probability_engines_required") != [
            "KNOWN_CARD_COUNT"
        ]:
            errors.append(
                "Phase 17C must continue to require only KNOWN_CARD_COUNT"
            )
    else:
        if payload.get("registered_probability_engines") != 1:
            errors.append(f"Phase {phase} recorded probability-engine count must be one")
    if phase in {"17E", "17F", "17G", "17H", "17I", "17J", "17K"}:
        if payload.get("classification_after") != "SOURCE_PARTIAL":
            errors.append(f"Phase {phase} classification must remain SOURCE_PARTIAL")
        if payload.get("restricted_choice_engine_registered") is not False:
            errors.append("Restricted Choice must remain unregistered")
        if payload.get("vacant_places_engine_registered") is not False:
            errors.append("Vacant Places must remain unregistered")
    if phase == "17K":
        if payload.get("disposition") != "DEFERRED":
            errors.append("Phase 17K disposition must remain DEFERRED")
        if payload.get("phase17_closed") is not True:
            errors.append("Phase 17K must remain recorded as closed")
    return tuple(errors)


def validate_historical_report(
    phase: str,
    *,
    repository_root: Path = GIT_ROOT,
) -> HistoricalReportValidation:
    try:
        entry = PHASE17_HISTORICAL_REPORT_MANIFEST[phase]
    except KeyError as error:
        raise ValueError(f"unsupported historical Phase 17 report: {phase}") from error
    artifact = ProvenanceValidator(repository_root).resolve_and_validate(entry)
    if not artifact.is_authorized or artifact.resolved_path is None:
        return HistoricalReportValidation(
            phase,
            artifact,
            _recorded_output_reproducibility(),
            None,
            (f"artifact provenance failed: {artifact.status.value}",),
        )
    try:
        raw = artifact.resolved_path.read_bytes()
        encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        payload = json.loads(raw.decode(encoding))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return HistoricalReportValidation(
            phase,
            artifact,
            _recorded_output_reproducibility(),
            None,
            (f"invalid archived JSON: {error}",),
        )
    if not isinstance(payload, dict):
        return HistoricalReportValidation(
            phase,
            artifact,
            _recorded_output_reproducibility(),
            None,
            ("archived JSON root must be an object",),
        )
    return HistoricalReportValidation(
        phase,
        artifact,
        _recorded_output_reproducibility(),
        payload,
        validate_historical_payload(phase, payload),
    )


def _git_blob_oid(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def validate_phase17c_backup_member(
    *,
    repository_root: Path = GIT_ROOT,
    member_path: str = PHASE17C_BACKUP_MEMBER,
) -> ZipMemberValidation:
    artifact = ProvenanceValidator(repository_root).resolve_and_validate(
        PHASE17C_FULL_KIT_MANIFEST
    )
    if not artifact.is_authorized or artifact.resolved_path is None:
        return ZipMemberValidation(
            artifact,
            member_path,
            artifact.status,
            f"ZIP artifact provenance failed: {artifact.reason}",
        )
    try:
        with ZipFile(artifact.resolved_path) as archive:
            matches = [info for info in archive.infolist() if info.filename == member_path]
            if not matches:
                return ZipMemberValidation(
                    artifact,
                    member_path,
                    ProvenanceStatus.MISSING,
                    "The exact approved ZIP member is missing.",
                )
            if len(matches) != 1:
                return ZipMemberValidation(
                    artifact,
                    member_path,
                    ProvenanceStatus.AMBIGUOUS,
                    "The exact approved ZIP member occurs more than once.",
                )
            content = archive.read(matches[0])
    except (BadZipFile, OSError) as error:
        return ZipMemberValidation(
            artifact,
            member_path,
            ProvenanceStatus.IDENTITY_MISMATCH,
            f"Unable to read the approved ZIP: {error}",
        )
    member_blob = _git_blob_oid(content)
    if member_blob != PHASE17C_BACKUP_MEMBER_BLOB:
        return ZipMemberValidation(
            artifact,
            member_path,
            ProvenanceStatus.IDENTITY_MISMATCH,
            "The exact ZIP member does not match its audited blob identity.",
            member_blob_oid=member_blob,
        )
    return ZipMemberValidation(
        artifact,
        member_path,
        ProvenanceStatus.AUTHORIZED,
        "The exact ZIP member and containing artifact are blob-pinned.",
        member_blob_oid=member_blob,
        content=content,
    )
