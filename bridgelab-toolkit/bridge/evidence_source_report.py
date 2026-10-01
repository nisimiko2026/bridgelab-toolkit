"""Serializable reporting view for BridgeLab evidence sources.

The report exposes source identity and semantic role for presentation
and integration. It does not rank sources, compare recommendations,
assign authority, vote, score providers, or select a winner.
"""

from __future__ import annotations

from dataclasses import dataclass

from .evidence_source_manifest import (
    EvidenceSourceEntry,
    EvidenceSourceManifest,
)


@dataclass(frozen=True, slots=True)
class EvidenceSourceReportEntry:
    """Serializable representation of one evidence source."""

    role: str
    source_kind: str
    source_id: str | None
    implementation: str | None
    version: str | None
    record_id: str | None

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-friendly representation."""

        return {
            "role": self.role,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "implementation": self.implementation,
            "version": self.version,
            "record_id": self.record_id,
        }


@dataclass(frozen=True, slots=True)
class EvidenceSourceReport:
    """Serializable source report for one decision case."""

    case_id: str
    entries: tuple[EvidenceSourceReportEntry, ...]

    @property
    def total(self) -> int:
        """Return the number of source entries."""

        return len(self.entries)

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-friendly representation."""

        return {
            "case_id": self.case_id,
            "total": self.total,
            "entries": [
                entry.as_dict()
                for entry in self.entries
            ],
        }


def _report_entry(
    entry: EvidenceSourceEntry,
) -> EvidenceSourceReportEntry:
    return EvidenceSourceReportEntry(
        role=entry.role.value,
        source_kind=entry.source_kind,
        source_id=entry.source_id,
        implementation=entry.implementation,
        version=entry.version,
        record_id=entry.record_id,
    )


def build_evidence_source_report(
    manifest: EvidenceSourceManifest,
) -> EvidenceSourceReport:
    """Build a passive serializable report from a source manifest."""

    return EvidenceSourceReport(
        case_id=manifest.case_id,
        entries=tuple(
            _report_entry(entry)
            for entry in manifest.entries
        ),
    )
