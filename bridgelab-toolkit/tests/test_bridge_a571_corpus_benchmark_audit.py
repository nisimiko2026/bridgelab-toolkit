from dataclasses import replace

import pytest

from bridge.corpus_benchmark import (
    CorpusBenchmarkResult,
    CorpusBenchmarkStatus,
)
from bridge.corpus_benchmark_audit import (
    CorpusAuditGroup,
    CorpusAuditGroupKey,
    CorpusBenchmarkAudit,
    aggregate_corpus_benchmark_audit,
)
from bridge.decision_evidence import DisagreementKind
from bridge.policy_audit import PolicyAuditCandidate


def test_group_key_is_immutable() -> None:
    key = CorpusAuditGroupKey(
        kind=DisagreementKind.POSSIBLE_POLICY_GAP,
        system_id="SAYC",
        convention_id="stayman",
        treatment_id="standard",
        partnership_id=None,
        external_provider_id="corpus",
    )

    with pytest.raises(Exception):
        key.system_id = "2/1"  # type: ignore[misc]


def test_group_validates_positive_count() -> None:
    key = CorpusAuditGroupKey(
        kind=DisagreementKind.POSSIBLE_POLICY_GAP,
        system_id="SAYC",
        convention_id=None,
        treatment_id=None,
        partnership_id=None,
        external_provider_id="corpus",
    )

    with pytest.raises(ValueError):
        CorpusAuditGroup(key=key, count=0, case_ids=())


def test_group_requires_case_count_match() -> None:
    key = CorpusAuditGroupKey(
        kind=DisagreementKind.POSSIBLE_POLICY_GAP,
        system_id="SAYC",
        convention_id=None,
        treatment_id=None,
        partnership_id=None,
        external_provider_id="corpus",
    )

    with pytest.raises(ValueError):
        CorpusAuditGroup(key=key, count=2, case_ids=("case-1",))


def test_empty_audit_is_valid() -> None:
    audit = aggregate_corpus_benchmark_audit(())

    assert audit.benchmark_total == 0
    assert audit.evaluated == 0
    assert audit.skipped_unknown_system == 0
    assert audit.audit_candidate_count == 0
    assert audit.groups == ()


def test_audit_validates_accounting() -> None:
    with pytest.raises(ValueError):
        CorpusBenchmarkAudit(
            benchmark_total=2,
            evaluated=1,
            skipped_unknown_system=0,
            audit_candidate_count=0,
            groups=(),
        )


def test_count_requires_disagreement_kind() -> None:
    audit = CorpusBenchmarkAudit(
        benchmark_total=0,
        evaluated=0,
        skipped_unknown_system=0,
        audit_candidate_count=0,
        groups=(),
    )

    with pytest.raises(TypeError):
        audit.count("POSSIBLE_POLICY_GAP")  # type: ignore[arg-type]


def test_aggregate_requires_tuple() -> None:
    with pytest.raises(TypeError):
        aggregate_corpus_benchmark_audit([])  # type: ignore[arg-type]


def test_aggregate_rejects_non_benchmark_members() -> None:
    with pytest.raises(TypeError):
        aggregate_corpus_benchmark_audit(("bad",))  # type: ignore[arg-type]
