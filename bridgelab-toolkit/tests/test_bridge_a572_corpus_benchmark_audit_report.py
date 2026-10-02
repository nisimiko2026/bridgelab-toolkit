"""A5.7.2 structured and text corpus benchmark audit report tests."""

import pytest

from bridge.corpus_benchmark_audit import (
    CorpusAuditGroup,
    CorpusAuditGroupKey,
    CorpusBenchmarkAudit,
)
from bridge.corpus_benchmark_audit_report import (
    CorpusAuditReportRow,
    CorpusBenchmarkAuditReport,
    build_corpus_benchmark_audit_report,
    render_corpus_benchmark_audit_report,
)
from bridge.decision_evidence import DisagreementKind


def make_group(
    *,
    kind: DisagreementKind = DisagreementKind.POSSIBLE_POLICY_GAP,
    system_id: str | None = "2/1",
    convention_id: str | None = "bergen",
    treatment_id: str | None = "nisim-nily-bergen",
    partnership_id: str | None = "nisim-nily",
    external_provider_id: str = "test-corpus",
    case_ids: tuple[str, ...] = ("case-1",),
) -> CorpusAuditGroup:
    return CorpusAuditGroup(
        key=CorpusAuditGroupKey(
            kind=kind,
            system_id=system_id,
            convention_id=convention_id,
            treatment_id=treatment_id,
            partnership_id=partnership_id,
            external_provider_id=external_provider_id,
        ),
        count=len(case_ids),
        case_ids=case_ids,
    )


def make_audit(
    *groups: CorpusAuditGroup,
    evaluated: int = 1,
    skipped: int = 0,
) -> CorpusBenchmarkAudit:
    return CorpusBenchmarkAudit(
        benchmark_total=evaluated + skipped,
        evaluated=evaluated,
        skipped_unknown_system=skipped,
        audit_candidate_count=sum(group.count for group in groups),
        groups=tuple(groups),
    )


def test_build_empty_report() -> None:
    report = build_corpus_benchmark_audit_report(
        make_audit(evaluated=0)
    )

    assert report.benchmark_total == 0
    assert report.evaluated == 0
    assert report.skipped_unknown_system == 0
    assert report.audit_candidate_count == 0
    assert report.possible_policy_gaps == 0
    assert report.possible_engine_defects == 0
    assert report.rows == ()


def test_build_report_preserves_group_dimensions_and_case_ids() -> None:
    group = make_group(case_ids=("case-1", "case-2"))

    report = build_corpus_benchmark_audit_report(
        make_audit(group, evaluated=2)
    )

    assert report.audit_candidate_count == 2
    assert report.possible_policy_gaps == 2
    assert report.possible_engine_defects == 0
    assert len(report.rows) == 1

    row = report.rows[0]
    assert row.kind is DisagreementKind.POSSIBLE_POLICY_GAP
    assert row.system_id == "2/1"
    assert row.convention_id == "bergen"
    assert row.treatment_id == "nisim-nily-bergen"
    assert row.partnership_id == "nisim-nily"
    assert row.external_provider_id == "test-corpus"
    assert row.count == 2
    assert row.case_ids == ("case-1", "case-2")


def test_build_report_counts_both_auditable_kinds() -> None:
    audit = make_audit(
        make_group(
            kind=DisagreementKind.POSSIBLE_POLICY_GAP,
            case_ids=("gap-1", "gap-2"),
        ),
        make_group(
            kind=DisagreementKind.POSSIBLE_ENGINE_DEFECT,
            external_provider_id="ben",
            case_ids=("engine-1",),
        ),
        evaluated=3,
    )

    report = build_corpus_benchmark_audit_report(audit)

    assert report.audit_candidate_count == 3
    assert report.possible_policy_gaps == 2
    assert report.possible_engine_defects == 1
    assert len(report.rows) == 2


def test_build_report_preserves_skipped_unknown_system() -> None:
    report = build_corpus_benchmark_audit_report(
        make_audit(make_group(), evaluated=1, skipped=4)
    )

    assert report.benchmark_total == 5
    assert report.evaluated == 1
    assert report.skipped_unknown_system == 4


def test_build_report_rejects_invalid_input() -> None:
    with pytest.raises(TypeError, match="audit must be CorpusBenchmarkAudit"):
        build_corpus_benchmark_audit_report(object())  # type: ignore[arg-type]


def test_report_row_requires_matching_case_count() -> None:
    with pytest.raises(ValueError, match="case_ids length must equal count"):
        CorpusAuditReportRow(
            kind=DisagreementKind.POSSIBLE_POLICY_GAP,
            system_id="2/1",
            convention_id="bergen",
            treatment_id="nisim-nily-bergen",
            partnership_id="nisim-nily",
            external_provider_id="test-corpus",
            count=2,
            case_ids=("only-one",),
        )


def test_report_validates_kind_accounting() -> None:
    row = CorpusAuditReportRow(
        kind=DisagreementKind.POSSIBLE_POLICY_GAP,
        system_id="2/1",
        convention_id="bergen",
        treatment_id="nisim-nily-bergen",
        partnership_id="nisim-nily",
        external_provider_id="test-corpus",
        count=1,
        case_ids=("case-1",),
    )

    with pytest.raises(
        ValueError,
        match="auditable kind counts must equal audit_candidate_count",
    ):
        CorpusBenchmarkAuditReport(
            benchmark_total=1,
            evaluated=1,
            skipped_unknown_system=0,
            audit_candidate_count=1,
            possible_policy_gaps=0,
            possible_engine_defects=0,
            rows=(row,),
        )


def test_render_empty_report() -> None:
    report = build_corpus_benchmark_audit_report(
        make_audit(evaluated=0)
    )

    text = render_corpus_benchmark_audit_report(report)

    assert "CORPUS BENCHMARK AUDIT REPORT" in text
    assert "benchmark total: 0" in text
    assert "audit candidates: 0" in text
    assert "AUDIT GROUPS\nnone" in text


def test_render_report_contains_summary_and_group_details() -> None:
    report = build_corpus_benchmark_audit_report(
        make_audit(
            make_group(case_ids=("case-1", "case-2")),
            evaluated=2,
            skipped=1,
        )
    )

    text = render_corpus_benchmark_audit_report(report)

    assert "benchmark total: 3" in text
    assert "evaluated: 2" in text
    assert "skipped unknown system: 1" in text
    assert "possible policy gaps: 2" in text
    assert f"1. {DisagreementKind.POSSIBLE_POLICY_GAP.value}" in text
    assert "system: 2/1" in text
    assert "convention: bergen" in text
    assert "treatment: nisim-nily-bergen" in text
    assert "partnership: nisim-nily" in text
    assert "external provider: test-corpus" in text
    assert "count: 2" in text
    assert "case ids: case-1, case-2" in text


def test_render_unknown_dimensions_as_unknown() -> None:
    report = build_corpus_benchmark_audit_report(
        make_audit(
            make_group(
                system_id=None,
                convention_id=None,
                treatment_id=None,
                partnership_id=None,
            )
        )
    )

    text = render_corpus_benchmark_audit_report(report)

    assert "system: UNKNOWN" in text
    assert "convention: UNKNOWN" in text
    assert "treatment: UNKNOWN" in text
    assert "partnership: UNKNOWN" in text


def test_render_rejects_invalid_input() -> None:
    with pytest.raises(
        TypeError,
        match="report must be CorpusBenchmarkAuditReport",
    ):
        render_corpus_benchmark_audit_report(object())  # type: ignore[arg-type]
