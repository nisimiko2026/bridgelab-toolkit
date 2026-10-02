"""A4.3 immutable DecisionCase evidence enrichment tests."""

import pytest

from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.corpus import (
    CanonicalBoardRecord,
    SourceProvenance,
)
from bridge.decision_case import DecisionCase
from bridge.decision_case_enrichment import enrich_decision_case
from bridge.decision_evidence import (
    DecisionEvidence,
    Disagreement,
    DisagreementKind,
    EvidenceScope,
)
from bridge.double_dummy_evidence import DoubleDummyEvidence
from bridge.models import Seat, Vulnerability
from bridge.simulation_statistics import SimulationStatistics
from bridge.trick_solver import (
    TrickSolverResult,
    TrickSolverStatus,
)


def make_policy_evidence(
    provider_id: str = "bridgelab",
) -> DecisionEvidence[object]:
    return DecisionEvidence(
        result=CapabilityResult(
            provider=ProviderDescriptor(
                provider_id=provider_id,
                capability=Capability.BIDDING,
                implementation="test",
            ),
            status=ProviderStatus.ABSTAIN,
            recommendation=None,
        ),
        scope=EvidenceScope.SYSTEM,
        system_id="test-system",
    )


def make_corpus(
    record_id: str,
) -> CanonicalBoardRecord:
    return CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider="test-corpus",
            source="test-source",
            record_id=record_id,
        ),
        dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
    )


def make_simulation(
    runs: int,
) -> SimulationStatistics:
    return SimulationStatistics(
        runs=runs,
        completed=runs,
        abstained=0,
        max_steps=0,
        total_calls_added=runs,
        max_calls_added=1 if runs else 0,
        stop_reason_counts=(),
        stopped_seat_counts=(),
    )


def make_double_dummy(
    deal_id: str,
) -> DoubleDummyEvidence:
    provider = ProviderDescriptor(
        provider_id="test-dd",
        capability=Capability.DOUBLE_DUMMY,
        implementation="test-dd",
    )

    result = TrickSolverResult(
        implementation="test-dd",
        version="1",
        deal_id=deal_id,
        declarer=Seat.NORTH,
        strain=None,
        opening_lead=None,
        status=TrickSolverStatus.SUCCESS,
        maximum_declarer_tricks=9,
        elapsed_seconds=0.01,
    )

    return DoubleDummyEvidence(
        provider=provider,
        result=result,
    )


def test_empty_enrichment_preserves_case_contents():
    bridgelab = make_policy_evidence()

    case = DecisionCase(
        case_id="a43-empty",
        bridgelab=bridgelab,
        notes=("existing",),
    )

    enriched = enrich_decision_case(case)

    assert enriched == case
    assert enriched is not case


def test_corpus_evidence_is_appended():
    existing = make_corpus("existing")
    added = make_corpus("added")

    case = DecisionCase(
        case_id="a43-corpus",
        corpus=(existing,),
    )

    enriched = enrich_decision_case(
        case,
        corpus=(added,),
    )

    assert enriched.corpus == (
        existing,
        added,
    )


def test_simulation_evidence_is_appended():
    existing = make_simulation(10)
    added = make_simulation(20)

    case = DecisionCase(
        case_id="a43-simulation",
        simulations=(existing,),
    )

    enriched = enrich_decision_case(
        case,
        simulations=(added,),
    )

    assert enriched.simulations == (
        existing,
        added,
    )


def test_double_dummy_evidence_is_appended():
    existing = make_double_dummy("existing")
    added = make_double_dummy("added")

    case = DecisionCase(
        case_id="a43-dd",
        double_dummy=(existing,),
    )

    enriched = enrich_decision_case(
        case,
        double_dummy=(added,),
    )

    assert enriched.double_dummy == (
        existing,
        added,
    )


def test_all_reference_evidence_categories_can_be_added_together():
    corpus = make_corpus("board-1")
    simulation = make_simulation(100)
    double_dummy = make_double_dummy("deal-1")

    case = DecisionCase(
        case_id="a43-all",
        bridgelab=make_policy_evidence(),
    )

    enriched = enrich_decision_case(
        case,
        corpus=(corpus,),
        simulations=(simulation,),
        double_dummy=(double_dummy,),
    )

    assert enriched.corpus == (corpus,)
    assert enriched.simulations == (simulation,)
    assert enriched.double_dummy == (double_dummy,)


def test_bridgelab_external_and_disagreements_are_preserved():
    bridgelab = make_policy_evidence("bridgelab")
    external = make_policy_evidence("external")

    disagreement = Disagreement(
        kind=DisagreementKind.JUDGMENT_DIFFERENCE,
        left_provider_id="bridgelab",
        right_provider_id="external",
        explanation="Test disagreement.",
    )

    case = DecisionCase(
        case_id="a43-preserve",
        bridgelab=bridgelab,
        external=(external,),
        disagreements=(disagreement,),
    )

    enriched = enrich_decision_case(
        case,
        corpus=(make_corpus("board-1"),),
        simulations=(make_simulation(10),),
        double_dummy=(make_double_dummy("deal-1"),),
    )

    assert enriched.bridgelab is bridgelab
    assert enriched.external == (external,)
    assert enriched.disagreements == (disagreement,)


def test_notes_are_appended_in_order():
    case = DecisionCase(
        case_id="a43-notes",
        notes=("first",),
    )

    enriched = enrich_decision_case(
        case,
        notes=(
            "second",
            "third",
        ),
    )

    assert enriched.notes == (
        "first",
        "second",
        "third",
    )


def test_original_case_is_not_mutated():
    original_corpus = (make_corpus("original"),)

    case = DecisionCase(
        case_id="a43-immutable",
        corpus=original_corpus,
    )

    enriched = enrich_decision_case(
        case,
        corpus=(make_corpus("new"),),
    )

    assert case.corpus is original_corpus
    assert len(case.corpus) == 1
    assert len(enriched.corpus) == 2
    assert enriched is not case


def test_caller_order_is_preserved_within_each_category():
    corpus_one = make_corpus("one")
    corpus_two = make_corpus("two")
    corpus_three = make_corpus("three")

    case = DecisionCase(
        case_id="a43-order",
        corpus=(corpus_one,),
    )

    enriched = enrich_decision_case(
        case,
        corpus=(
            corpus_two,
            corpus_three,
        ),
    )

    assert enriched.corpus == (
        corpus_one,
        corpus_two,
        corpus_three,
    )


def test_invalid_case_is_rejected():
    with pytest.raises(
        TypeError,
        match="case must be DecisionCase",
    ):
        enrich_decision_case(object())


def test_non_tuple_evidence_is_rejected():
    case = DecisionCase(
        case_id="a43-invalid-tuple",
    )

    with pytest.raises(
        TypeError,
        match="corpus must be a tuple",
    ):
        enrich_decision_case(
            case,
            corpus=[],
        )


def test_wrong_evidence_type_is_rejected():
    case = DecisionCase(
        case_id="a43-invalid-entry",
    )

    with pytest.raises(
        TypeError,
        match="simulations entries must be SimulationStatistics",
    ):
        enrich_decision_case(
            case,
            simulations=(object(),),
        )


def test_invalid_notes_are_rejected():
    case = DecisionCase(
        case_id="a43-invalid-notes",
    )

    with pytest.raises(
        ValueError,
        match="notes entries must be non-blank strings",
    ):
        enrich_decision_case(
            case,
            notes=("valid", "   "),
        )
