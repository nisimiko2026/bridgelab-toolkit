"""Aggregate policy audit candidates from corpus benchmark results.

A5.7.1 — Benchmark Audit Aggregation Model.

This module aggregates already-classified audit candidates. It does not
reclassify disagreements, rank evidence, infer correctness, vote, or modify
BridgeLab policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus_benchmark import CorpusBenchmarkResult, CorpusBenchmarkStatus
from .decision_evidence import DisagreementKind
from .policy_audit import PolicyAuditCandidate, build_policy_audit_candidates


@dataclass(frozen=True, slots=True)
class CorpusAuditGroupKey:
    """Stable dimensions for one aggregate audit bucket."""

    kind: DisagreementKind
    system_id: str | None
    convention_id: str | None
    treatment_id: str | None
    partnership_id: str | None
    external_provider_id: str


@dataclass(frozen=True, slots=True)
class CorpusAuditGroup:
    """One descriptive group of already-classified audit candidates."""

    key: CorpusAuditGroupKey
    count: int
    case_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.key, CorpusAuditGroupKey):
            raise TypeError("key must be CorpusAuditGroupKey")
        if not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 1:
            raise ValueError("count must be a positive integer")
        if not isinstance(self.case_ids, tuple):
            raise TypeError("case_ids must be a tuple")
        if len(self.case_ids) != self.count:
            raise ValueError("case_ids length must equal count")
        if not all(isinstance(case_id, str) and case_id.strip() for case_id in self.case_ids):
            raise ValueError("case_ids must contain non-blank strings")


@dataclass(frozen=True, slots=True)
class CorpusBenchmarkAudit:
    """Aggregate audit view for one corpus benchmark run."""

    benchmark_total: int
    evaluated: int
    skipped_unknown_system: int
    audit_candidate_count: int
    groups: tuple[CorpusAuditGroup, ...]

    def __post_init__(self) -> None:
        for name in (
            "benchmark_total",
            "evaluated",
            "skipped_unknown_system",
            "audit_candidate_count",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

        if self.evaluated + self.skipped_unknown_system != self.benchmark_total:
            raise ValueError("evaluated plus skipped positions must equal benchmark_total")
        if not isinstance(self.groups, tuple):
            raise TypeError("groups must be a tuple")
        if not all(isinstance(group, CorpusAuditGroup) for group in self.groups):
            raise TypeError("groups must contain CorpusAuditGroup values")
        if sum(group.count for group in self.groups) != self.audit_candidate_count:
            raise ValueError("group counts must equal audit_candidate_count")

    def count(self, kind: DisagreementKind) -> int:
        """Count candidates of one already-classified disagreement kind."""
        if not isinstance(kind, DisagreementKind):
            raise TypeError("kind must be DisagreementKind")
        return sum(group.count for group in self.groups if group.key.kind is kind)


def _candidate_key(candidate: PolicyAuditCandidate) -> CorpusAuditGroupKey:
    return CorpusAuditGroupKey(
        kind=candidate.kind,
        system_id=candidate.system_id,
        convention_id=candidate.convention_id,
        treatment_id=candidate.treatment_id,
        partnership_id=candidate.partnership_id,
        external_provider_id=candidate.external_provider_id,
    )


def _sort_key(key: CorpusAuditGroupKey) -> tuple[str, ...]:
    return (
        key.kind.value,
        key.system_id or "",
        key.convention_id or "",
        key.treatment_id or "",
        key.partnership_id or "",
        key.external_provider_id,
    )


def aggregate_corpus_benchmark_audit(
    results: tuple[CorpusBenchmarkResult, ...],
) -> CorpusBenchmarkAudit:
    """Aggregate existing A4.5 audit candidates across benchmark results."""

    if not isinstance(results, tuple):
        raise TypeError("results must be a tuple")
    if not all(isinstance(result, CorpusBenchmarkResult) for result in results):
        raise TypeError("results must contain CorpusBenchmarkResult values")

    evaluated = 0
    skipped_unknown_system = 0
    buckets: dict[CorpusAuditGroupKey, list[str]] = {}

    for result in results:
        if result.status is CorpusBenchmarkStatus.SKIPPED_UNKNOWN_SYSTEM:
            skipped_unknown_system += 1
            continue

        if result.status is not CorpusBenchmarkStatus.EVALUATED:
            raise ValueError(f"unsupported benchmark status: {result.status}")
        if result.case is None:
            raise ValueError("evaluated benchmark result has no DecisionCase")

        evaluated += 1

        for candidate in build_policy_audit_candidates(result.case):
            key = _candidate_key(candidate)
            buckets.setdefault(key, []).append(candidate.case_id)

    groups = tuple(
        CorpusAuditGroup(
            key=key,
            count=len(buckets[key]),
            case_ids=tuple(buckets[key]),
        )
        for key in sorted(buckets, key=_sort_key)
    )

    return CorpusBenchmarkAudit(
        benchmark_total=len(results),
        evaluated=evaluated,
        skipped_unknown_system=skipped_unknown_system,
        audit_candidate_count=sum(group.count for group in groups),
        groups=groups,
    )
