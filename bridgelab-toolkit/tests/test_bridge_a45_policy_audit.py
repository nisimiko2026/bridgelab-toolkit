"""A4.5 structured policy/engine audit candidate tests."""

import pytest

from bridge.auction import Call
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_case import DecisionCase
from bridge.decision_evidence import (
    DecisionEvidence,
    Disagreement,
    DisagreementKind,
    EvidenceScope,
)
from bridge.policy_audit import (
    PolicyAuditCandidate,
    build_policy_audit_candidates,
)


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


def make_disagreement(
    *,
    kind: DisagreementKind,
    right_provider_id: str,
) -> Disagreement:
    return Disagreement(
        kind=kind,
        left_provider_id="bridgelab",
        right_provider_id=right_provider_id,
        explanation="A4.5 test disagreement.",
    )


def make_bridgelab() -> DecisionEvidence[object]:
    return make_evidence(
        provider_id="bridgelab",
        call="3C",
        scope=EvidenceScope.TREATMENT,
        system_id="2/1",
        convention_id="bergen",
        treatment_id="nisim-nily-bergen",
        partnership_id="nisim-nily",
    )


def test_possible_policy_gap_becomes_audit_candidate():
    bridgelab = make_bridgelab()
    external = make_evidence(
        provider_id="ben",
        call="4H",
    )

    case = DecisionCase(
        case_id="a45-policy-gap",
        bridgelab=bridgelab,
        external=(external,),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_POLICY_GAP,
                right_provider_id="ben",
            ),
        ),
    )

    candidates = build_policy_audit_candidates(case)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert isinstance(candidate, PolicyAuditCandidate)
    assert candidate.kind is DisagreementKind.POSSIBLE_POLICY_GAP
    assert candidate.bridgelab_recommendation == Call.parse("3C")
    assert candidate.external_recommendation == Call.parse("4H")
    assert candidate.external_provider_id == "ben"


def test_possible_engine_defect_becomes_separate_audit_kind():
    case = DecisionCase(
        case_id="a45-engine",
        bridgelab=make_bridgelab(),
        external=(
            make_evidence(
                provider_id="external-engine-check",
                call="4S",
            ),
        ),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_ENGINE_DEFECT,
                right_provider_id="external-engine-check",
            ),
        ),
    )

    candidates = build_policy_audit_candidates(case)

    assert len(candidates) == 1
    assert (
        candidates[0].kind
        is DisagreementKind.POSSIBLE_ENGINE_DEFECT
    )


def test_unknown_external_system_is_not_promoted_to_policy_gap():
    case = DecisionCase(
        case_id="a45-unknown",
        bridgelab=make_bridgelab(),
        external=(
            make_evidence(
                provider_id="ben",
                call="4H",
            ),
        ),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
                right_provider_id="ben",
            ),
        ),
    )

    assert build_policy_audit_candidates(case) == ()


def test_judgment_difference_is_not_promoted():
    case = DecisionCase(
        case_id="a45-judgment",
        bridgelab=make_bridgelab(),
        external=(
            make_evidence(
                provider_id="ben",
                call="4H",
            ),
        ),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.JUDGMENT_DIFFERENCE,
                right_provider_id="ben",
            ),
        ),
    )

    assert build_policy_audit_candidates(case) == ()


def test_policy_identity_is_preserved_from_bridgelab():
    case = DecisionCase(
        case_id="a45-policy-identity",
        bridgelab=make_bridgelab(),
        external=(
            make_evidence(
                provider_id="ben",
                call="4H",
            ),
        ),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_POLICY_GAP,
                right_provider_id="ben",
            ),
        ),
    )

    candidate = build_policy_audit_candidates(case)[0]

    assert candidate.system_id == "2/1"
    assert candidate.convention_id == "bergen"
    assert candidate.treatment_id == "nisim-nily-bergen"
    assert candidate.partnership_id == "nisim-nily"


def test_source_report_is_attached_to_candidate():
    case = DecisionCase(
        case_id="a45-source-report",
        bridgelab=make_bridgelab(),
        external=(
            make_evidence(
                provider_id="ben",
                call="4H",
            ),
        ),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_POLICY_GAP,
                right_provider_id="ben",
            ),
        ),
    )

    candidate = build_policy_audit_candidates(case)[0]

    assert candidate.source_report.case_id == "a45-source-report"
    assert candidate.source_report.total == 2

    assert tuple(
        entry.source_id
        for entry in candidate.source_report.entries
    ) == (
        "bridgelab",
        "ben",
    )


def test_multiple_auditable_disagreements_preserve_order():
    case = DecisionCase(
        case_id="a45-order",
        bridgelab=make_bridgelab(),
        external=(
            make_evidence(
                provider_id="ben",
                call="4H",
            ),
            make_evidence(
                provider_id="brl",
                call="3H",
            ),
        ),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_POLICY_GAP,
                right_provider_id="ben",
            ),
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_ENGINE_DEFECT,
                right_provider_id="brl",
            ),
        ),
    )

    candidates = build_policy_audit_candidates(case)

    assert tuple(
        candidate.external_provider_id
        for candidate in candidates
    ) == (
        "ben",
        "brl",
    )

    assert tuple(
        candidate.kind
        for candidate in candidates
    ) == (
        DisagreementKind.POSSIBLE_POLICY_GAP,
        DisagreementKind.POSSIBLE_ENGINE_DEFECT,
    )


def test_duplicate_external_provider_ids_are_not_overwritten():
    first = make_evidence(
        provider_id="ben",
        call="4H",
    )
    second = make_evidence(
        provider_id="ben",
        call="3H",
    )

    case = DecisionCase(
        case_id="a45-duplicates",
        bridgelab=make_bridgelab(),
        external=(
            first,
            second,
        ),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_POLICY_GAP,
                right_provider_id="ben",
            ),
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_ENGINE_DEFECT,
                right_provider_id="ben",
            ),
        ),
    )

    candidates = build_policy_audit_candidates(case)

    assert len(candidates) == 2
    assert candidates[0].external_recommendation == Call.parse("4H")
    assert candidates[1].external_recommendation == Call.parse("3H")


def test_non_auditable_disagreement_does_not_consume_duplicate_occurrence():
    first = make_evidence(
        provider_id="ben",
        call="4H",
    )
    second = make_evidence(
        provider_id="ben",
        call="3H",
    )

    case = DecisionCase(
        case_id="a45-duplicate-filter",
        bridgelab=make_bridgelab(),
        external=(
            first,
            second,
        ),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
                right_provider_id="ben",
            ),
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_POLICY_GAP,
                right_provider_id="ben",
            ),
        ),
    )

    candidates = build_policy_audit_candidates(case)

    assert len(candidates) == 1
    assert candidates[0].external_recommendation == Call.parse("4H")


def test_missing_matching_external_evidence_is_rejected():
    case = DecisionCase(
        case_id="a45-missing-external",
        bridgelab=make_bridgelab(),
        disagreements=(
            make_disagreement(
                kind=DisagreementKind.POSSIBLE_POLICY_GAP,
                right_provider_id="ben",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "auditable disagreement has no matching "
            "external evidence"
        ),
    ):
        build_policy_audit_candidates(case)


def test_case_without_bridgelab_produces_no_candidates():
    case = DecisionCase(
        case_id="a45-no-bridgelab",
    )

    assert build_policy_audit_candidates(case) == ()


def test_invalid_case_is_rejected():
    with pytest.raises(
        TypeError,
        match="case must be DecisionCase",
    ):
        build_policy_audit_candidates(object())
