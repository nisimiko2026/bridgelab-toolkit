"""A5.7.1 integration tests for corpus benchmark audit aggregation."""

from bridge.auction import Call
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.corpus_benchmark import (
    CorpusBenchmarkResult,
    CorpusBenchmarkStatus,
)
from bridge.corpus_benchmark_audit import aggregate_corpus_benchmark_audit
from bridge.corpus_decisions import CorpusBiddingDecision
from bridge.corpus import SourceProvenance
from bridge.decision_case import DecisionCase
from bridge.decision_evidence import (
    DecisionEvidence,
    Disagreement,
    DisagreementKind,
    EvidenceScope,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.auction import Auction


def make_evidence(
    *,
    provider_id: str,
    call: str,
    scope: EvidenceScope = EvidenceScope.PROVIDER,
    system_id: str | None = None,
    convention_id: str | None = None,
    treatment_id: str | None = None,
    partnership_id: str | None = None,
) -> DecisionEvidence[object]:
    return DecisionEvidence(
        result=CapabilityResult(
            provider=ProviderDescriptor(
                provider_id=provider_id,
                capability=Capability.BIDDING,
                implementation=f"{provider_id}-test",
                version="1",
            ),
            status=ProviderStatus.SUCCESS,
            recommendation=Call.parse(call),
        ),
        scope=scope,
        system_id=system_id,
        convention_id=convention_id,
        treatment_id=treatment_id,
        partnership_id=partnership_id,
    )


def make_bridgelab(
    *,
    system_id: str = "2/1",
    convention_id: str | None = "bergen",
    treatment_id: str | None = "nisim-nily-bergen",
    partnership_id: str | None = "nisim-nily",
) -> DecisionEvidence[object]:
    return make_evidence(
        provider_id="bridgelab",
        call="3C",
        scope=EvidenceScope.TREATMENT,
        system_id=system_id,
        convention_id=convention_id,
        treatment_id=treatment_id,
        partnership_id=partnership_id,
    )


def make_disagreement(
    *,
    kind: DisagreementKind,
    right_provider_id: str,
) -> Disagreement:
    return Disagreement(
        kind=kind,
        left_provider_id="bridgelab",
        right_provider_id=right_provider_id,
        explanation="A5.7.1 integration test disagreement.",
    )


def make_decision(*, record_id: str, system_id: str | None = "2/1") -> CorpusBiddingDecision:
    auction = Auction(Seat.NORTH)
    return CorpusBiddingDecision(
        provenance=SourceProvenance(
            provider="test-corpus",
            source="test.pbn",
            record_id=record_id,
        ),
        call_index=0,
        seat=Seat.NORTH,
        hand=Hand.parse("AKQJ.T98.765.432"),
        auction=auction,
        observed_call=Call.parse("4H"),
        vulnerability=Vulnerability.NONE,
        system_id=system_id,
    )


def evaluated_result(
    *,
    case_id: str,
    record_id: str,
    kind: DisagreementKind,
    external_provider_id: str = "test-corpus",
    bridgelab: DecisionEvidence[object] | None = None,
) -> CorpusBenchmarkResult:
    external = make_evidence(
        provider_id=external_provider_id,
        call="4H",
        scope=EvidenceScope.EXPERT_CORPUS,
    )
    case = DecisionCase(
        case_id=case_id,
        bridgelab=bridgelab or make_bridgelab(),
        external=(external,),
        disagreements=(
            make_disagreement(
                kind=kind,
                right_provider_id=external_provider_id,
            ),
        ),
    )
    return CorpusBenchmarkResult(
        decision=make_decision(record_id=record_id),
        status=CorpusBenchmarkStatus.EVALUATED,
        case=case,
    )


def test_same_policy_gap_dimensions_are_aggregated() -> None:
    results = (
        evaluated_result(
            case_id="case-1",
            record_id="1",
            kind=DisagreementKind.POSSIBLE_POLICY_GAP,
        ),
        evaluated_result(
            case_id="case-2",
            record_id="2",
            kind=DisagreementKind.POSSIBLE_POLICY_GAP,
        ),
    )

    audit = aggregate_corpus_benchmark_audit(results)

    assert audit.benchmark_total == 2
    assert audit.evaluated == 2
    assert audit.audit_candidate_count == 2
    assert len(audit.groups) == 1
    assert audit.groups[0].count == 2
    assert audit.groups[0].case_ids == ("case-1", "case-2")
    assert audit.groups[0].key.system_id == "2/1"
    assert audit.groups[0].key.convention_id == "bergen"
    assert audit.groups[0].key.treatment_id == "nisim-nily-bergen"
    assert audit.groups[0].key.partnership_id == "nisim-nily"
    assert audit.groups[0].key.external_provider_id == "test-corpus"


def test_policy_gap_and_engine_defect_are_separate_groups() -> None:
    results = (
        evaluated_result(
            case_id="gap",
            record_id="1",
            kind=DisagreementKind.POSSIBLE_POLICY_GAP,
        ),
        evaluated_result(
            case_id="engine",
            record_id="2",
            kind=DisagreementKind.POSSIBLE_ENGINE_DEFECT,
        ),
    )

    audit = aggregate_corpus_benchmark_audit(results)

    assert len(audit.groups) == 2
    assert audit.count(DisagreementKind.POSSIBLE_POLICY_GAP) == 1
    assert audit.count(DisagreementKind.POSSIBLE_ENGINE_DEFECT) == 1


def test_non_auditable_disagreement_is_not_promoted() -> None:
    result = evaluated_result(
        case_id="judgment",
        record_id="1",
        kind=DisagreementKind.JUDGMENT_DIFFERENCE,
    )

    audit = aggregate_corpus_benchmark_audit((result,))

    assert audit.evaluated == 1
    assert audit.audit_candidate_count == 0
    assert audit.groups == ()


def test_different_treatments_form_different_groups() -> None:
    first = evaluated_result(
        case_id="first",
        record_id="1",
        kind=DisagreementKind.POSSIBLE_POLICY_GAP,
    )
    second = evaluated_result(
        case_id="second",
        record_id="2",
        kind=DisagreementKind.POSSIBLE_POLICY_GAP,
        bridgelab=make_bridgelab(treatment_id="alternate-bergen"),
    )

    audit = aggregate_corpus_benchmark_audit((first, second))

    assert len(audit.groups) == 2
    assert {group.key.treatment_id for group in audit.groups} == {
        "nisim-nily-bergen",
        "alternate-bergen",
    }


def test_different_external_providers_form_different_groups() -> None:
    results = (
        evaluated_result(
            case_id="corpus",
            record_id="1",
            kind=DisagreementKind.POSSIBLE_POLICY_GAP,
            external_provider_id="test-corpus",
        ),
        evaluated_result(
            case_id="ben",
            record_id="2",
            kind=DisagreementKind.POSSIBLE_POLICY_GAP,
            external_provider_id="ben",
        ),
    )

    audit = aggregate_corpus_benchmark_audit(results)

    assert len(audit.groups) == 2
    assert {group.key.external_provider_id for group in audit.groups} == {
        "test-corpus",
        "ben",
    }


def test_skipped_unknown_system_is_accounted_but_not_audited() -> None:
    skipped = CorpusBenchmarkResult(
        decision=make_decision(record_id="unknown", system_id=None),
        status=CorpusBenchmarkStatus.SKIPPED_UNKNOWN_SYSTEM,
        reason="corpus bidding system is unknown",
    )

    audit = aggregate_corpus_benchmark_audit((skipped,))

    assert audit.benchmark_total == 1
    assert audit.evaluated == 0
    assert audit.skipped_unknown_system == 1
    assert audit.audit_candidate_count == 0
    assert audit.groups == ()
