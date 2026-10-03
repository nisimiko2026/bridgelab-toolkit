"""A9.1 evidence-review contract tests."""
import pytest

from bridge.evidence_review_contract import (
    EvidenceReference,
    EvidenceReview,
    ReviewClassification,
    ReviewDisposition,
    review,
)


def ref():
    return EvidenceReference("sayc-source", "Explicit supporting statement.")


def test_all_required_review_classes_exist():
    assert {x.value for x in ReviewClassification} == {
        "expected-abstention",
        "core-gap",
        "system-dependent",
        "unknown-convention",
        "known-convention-missing-treatment",
        "partnership-agreement",
        "judgment",
        "possible-engine-defect",
        "insufficient-evidence",
    }


def test_empty_source_rejected():
    with pytest.raises(ValueError):
        EvidenceReference("", "x")


def test_empty_statement_rejected():
    with pytest.raises(ValueError):
        EvidenceReference("x", "")


def test_empty_replay_key_rejected():
    with pytest.raises(ValueError):
        review(
            replay_key="",
            classification=ReviewClassification.EXPECTED_ABSTENTION,
            disposition=ReviewDisposition.NO_CHANGE,
            rationale="supported",
        )


def test_empty_rationale_rejected():
    with pytest.raises(ValueError):
        review(
            replay_key="r",
            classification=ReviewClassification.EXPECTED_ABSTENTION,
            disposition=ReviewDisposition.NO_CHANGE,
            rationale="",
        )


def test_insufficient_evidence_must_request_more_evidence():
    with pytest.raises(ValueError):
        review(
            replay_key="r",
            classification=ReviewClassification.INSUFFICIENT_EVIDENCE,
            disposition=ReviewDisposition.NO_CHANGE,
            rationale="not enough evidence",
        )


def test_insufficient_evidence_valid():
    x = review(
        replay_key="r",
        classification=ReviewClassification.INSUFFICIENT_EVIDENCE,
        disposition=ReviewDisposition.NEEDS_MORE_EVIDENCE,
        rationale="not enough evidence",
    )
    assert x.disposition is ReviewDisposition.NEEDS_MORE_EVIDENCE


def test_possible_engine_defect_cannot_directly_become_knowledge_work():
    with pytest.raises(ValueError):
        review(
            replay_key="r",
            classification=ReviewClassification.POSSIBLE_ENGINE_DEFECT,
            disposition=ReviewDisposition.CANDIDATE_KNOWLEDGE_WORK,
            rationale="investigate implementation",
            evidence=(ref(),),
        )


def test_possible_engine_defect_can_request_investigation():
    x = review(
        replay_key="r",
        classification=ReviewClassification.POSSIBLE_ENGINE_DEFECT,
        disposition=ReviewDisposition.CANDIDATE_ENGINE_INVESTIGATION,
        rationale="source and implementation appear inconsistent",
        evidence=(ref(),),
    )
    assert x.evidence == (ref(),)


def test_candidate_knowledge_work_requires_evidence():
    with pytest.raises(ValueError):
        review(
            replay_key="r",
            classification=ReviewClassification.SYSTEM_DEPENDENT,
            disposition=ReviewDisposition.CANDIDATE_KNOWLEDGE_WORK,
            rationale="candidate system rule",
        )


def test_candidate_engine_investigation_requires_evidence():
    with pytest.raises(ValueError):
        review(
            replay_key="r",
            classification=ReviewClassification.POSSIBLE_ENGINE_DEFECT,
            disposition=ReviewDisposition.CANDIDATE_ENGINE_INVESTIGATION,
            rationale="candidate implementation issue",
        )


def test_expected_abstention_can_require_no_change():
    x = review(
        replay_key="sayc-production@1:seed:2",
        classification=ReviewClassification.EXPECTED_ABSTENTION,
        disposition=ReviewDisposition.NO_CHANGE,
        rationale="explicitly unsupported position",
        evidence=(ref(),),
    )
    assert x.classification is ReviewClassification.EXPECTED_ABSTENTION


def test_contract_preserves_notes_and_evidence_order():
    a = EvidenceReference("a", "A")
    b = EvidenceReference("b", "B")
    x = review(
        replay_key="r",
        classification=ReviewClassification.PARTNERSHIP_AGREEMENT,
        disposition=ReviewDisposition.NEEDS_MORE_EVIDENCE,
        rationale="agreement not supplied",
        evidence=(a, b),
        notes=("n1", "n2"),
    )
    assert x.evidence == (a, b)
    assert x.notes == ("n1", "n2")


def test_no_ranking_or_bid_choice_surface():
    x = EvidenceReview(
        replay_key="r",
        classification=ReviewClassification.JUDGMENT,
        disposition=ReviewDisposition.NEEDS_MORE_EVIDENCE,
        rationale="judgment case",
    )
    for name in (
        "rank", "ranking", "score", "winner", "priority",
        "recommended_bid", "best_bid", "correct_bid",
    ):
        assert not hasattr(x, name)


def test_deterministic_value_object():
    kwargs = dict(
        replay_key="r",
        classification=ReviewClassification.CORE_GAP,
        disposition=ReviewDisposition.CANDIDATE_KNOWLEDGE_WORK,
        rationale="explicit core capability is absent",
        evidence=(ref(),),
    )
    assert review(**kwargs) == review(**kwargs)
