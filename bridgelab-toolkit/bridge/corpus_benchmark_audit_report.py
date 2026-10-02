"""Structured and text reports for corpus benchmark audits.

A5.7.2 — Benchmark Audit Report.

This module renders an already-produced CorpusBenchmarkAudit. It does not
rerun benchmarks, reclassify disagreements, rank evidence, infer correctness,
or modify BridgeLab policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus_benchmark_audit import (
    CorpusAuditGroup,
    CorpusBenchmarkAudit,
)
from .decision_evidence import DisagreementKind


@dataclass(frozen=True, slots=True)
class CorpusAuditReportRow:
    kind: DisagreementKind
    system_id: str | None
    convention_id: str | None
    treatment_id: str | None
    partnership_id: str | None
    external_provider_id: str
    count: int
    case_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, DisagreementKind):
            raise TypeError("kind must be DisagreementKind")
        if not isinstance(self.external_provider_id, str) or not self.external_provider_id.strip():
            raise ValueError("external_provider_id must be a non-blank string")
        if not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 1:
            raise ValueError("count must be a positive integer")
        if not isinstance(self.case_ids, tuple):
            raise TypeError("case_ids must be a tuple")
        if len(self.case_ids) != self.count:
            raise ValueError("case_ids length must equal count")


@dataclass(frozen=True, slots=True)
class CorpusBenchmarkAuditReport:
    benchmark_total: int
    evaluated: int
    skipped_unknown_system: int
    audit_candidate_count: int
    possible_policy_gaps: int
    possible_engine_defects: int
    rows: tuple[CorpusAuditReportRow, ...]

    def __post_init__(self) -> None:
        for name in (
            "benchmark_total",
            "evaluated",
            "skipped_unknown_system",
            "audit_candidate_count",
            "possible_policy_gaps",
            "possible_engine_defects",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

        if self.evaluated + self.skipped_unknown_system != self.benchmark_total:
            raise ValueError("evaluated plus skipped positions must equal benchmark_total")
        if self.possible_policy_gaps + self.possible_engine_defects != self.audit_candidate_count:
            raise ValueError("auditable kind counts must equal audit_candidate_count")
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not all(isinstance(row, CorpusAuditReportRow) for row in self.rows):
            raise TypeError("rows must contain CorpusAuditReportRow values")
        if sum(row.count for row in self.rows) != self.audit_candidate_count:
            raise ValueError("row counts must equal audit_candidate_count")


def _row(group: CorpusAuditGroup) -> CorpusAuditReportRow:
    return CorpusAuditReportRow(
        kind=group.key.kind,
        system_id=group.key.system_id,
        convention_id=group.key.convention_id,
        treatment_id=group.key.treatment_id,
        partnership_id=group.key.partnership_id,
        external_provider_id=group.key.external_provider_id,
        count=group.count,
        case_ids=group.case_ids,
    )


def build_corpus_benchmark_audit_report(
    audit: CorpusBenchmarkAudit,
) -> CorpusBenchmarkAuditReport:
    """Build a stable structured report from an existing aggregate audit."""

    if not isinstance(audit, CorpusBenchmarkAudit):
        raise TypeError("audit must be CorpusBenchmarkAudit")

    rows = tuple(_row(group) for group in audit.groups)

    return CorpusBenchmarkAuditReport(
        benchmark_total=audit.benchmark_total,
        evaluated=audit.evaluated,
        skipped_unknown_system=audit.skipped_unknown_system,
        audit_candidate_count=audit.audit_candidate_count,
        possible_policy_gaps=audit.count(DisagreementKind.POSSIBLE_POLICY_GAP),
        possible_engine_defects=audit.count(DisagreementKind.POSSIBLE_ENGINE_DEFECT),
        rows=rows,
    )


def _display(value: str | None) -> str:
    return value if value is not None else "UNKNOWN"


def render_corpus_benchmark_audit_report(
    report: CorpusBenchmarkAuditReport,
) -> str:
    """Render a deterministic human-readable audit report."""

    if not isinstance(report, CorpusBenchmarkAuditReport):
        raise TypeError("report must be CorpusBenchmarkAuditReport")

    lines = [
        "CORPUS BENCHMARK AUDIT REPORT",
        "",
        f"benchmark total: {report.benchmark_total}",
        f"evaluated: {report.evaluated}",
        f"skipped unknown system: {report.skipped_unknown_system}",
        f"audit candidates: {report.audit_candidate_count}",
        f"possible policy gaps: {report.possible_policy_gaps}",
        f"possible engine defects: {report.possible_engine_defects}",
        "",
        "AUDIT GROUPS",
    ]

    if not report.rows:
        lines.append("none")
        return "\n".join(lines)

    for index, row in enumerate(report.rows, start=1):
        lines.extend(
            (
                "",
                f"{index}. {row.kind.value}",
                f"   system: {_display(row.system_id)}",
                f"   convention: {_display(row.convention_id)}",
                f"   treatment: {_display(row.treatment_id)}",
                f"   partnership: {_display(row.partnership_id)}",
                f"   external provider: {row.external_provider_id}",
                f"   count: {row.count}",
                f"   case ids: {', '.join(row.case_ids)}",
            )
        )

    return "\n".join(lines)
