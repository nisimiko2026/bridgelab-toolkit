"""A6.7 passive outcome evidence integration tests."""

import pytest

from bridge.capability_providers import Capability, ProviderDescriptor
from bridge.decision_case import DecisionCase
from bridge.double_dummy_evidence import DoubleDummyEvidence
from bridge.models import Seat, Suit
from bridge.outcome_evidence import add_outcome_evidence
from bridge.simulation_statistics import SimulationStatistics
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus


def make_dd() -> DoubleDummyEvidence:
    provider = ProviderDescriptor(
        provider_id="dds-test",
        capability=Capability.DOUBLE_DUMMY,
        implementation="dds-test",
        version="1",
    )
    result = TrickSolverResult(
        implementation="dds-test",
        version="1",
        deal_id="deal-1",
        declarer=Seat.NORTH,
        strain=Suit.SPADES,
        opening_lead=None,
        status=TrickSolverStatus.SUCCESS,
        maximum_declarer_tricks=10,
        elapsed_seconds=0.01,
    )
    return DoubleDummyEvidence(
        provider=provider,
        result=result,
        source_ids=("source-1",),
        notes=("reference measurement",),
    )


def make_sim() -> SimulationStatistics:
    return SimulationStatistics(
        runs=100,
        completed=80,
        abstained=15,
        max_steps=5,
        total_calls_added=250,
        max_calls_added=8,
        stop_reason_counts=(
            ("auction-complete", 80),
            ("max-steps", 5),
            ("no-recommendation", 15),
        ),
        stopped_seat_counts=(("N", 10), ("S", 5)),
    )


def test_empty_enrichment_preserves_case_content() -> None:
    case = DecisionCase(case_id="case-1", notes=("existing",))
    enriched = add_outcome_evidence(case)
    assert enriched == case
    assert enriched is not case


def test_double_dummy_is_appended() -> None:
    case = DecisionCase(case_id="case-1")
    dd = make_dd()
    enriched = add_outcome_evidence(case, double_dummy=(dd,))
    assert enriched.double_dummy == (dd,)
    assert case.double_dummy == ()


def test_simulation_is_appended() -> None:
    case = DecisionCase(case_id="case-1")
    sim = make_sim()
    enriched = add_outcome_evidence(case, simulations=(sim,))
    assert enriched.simulations == (sim,)
    assert case.simulations == ()


def test_existing_outcome_evidence_is_preserved_before_new_items() -> None:
    dd1, dd2 = make_dd(), make_dd()
    sim1, sim2 = make_sim(), make_sim()
    case = DecisionCase(
        case_id="case-1",
        double_dummy=(dd1,),
        simulations=(sim1,),
    )
    enriched = add_outcome_evidence(
        case,
        double_dummy=(dd2,),
        simulations=(sim2,),
    )
    assert enriched.double_dummy == (dd1, dd2)
    assert enriched.simulations == (sim1, sim2)


def test_notes_are_appended_and_trimmed() -> None:
    case = DecisionCase(case_id="case-1", notes=("existing",))
    enriched = add_outcome_evidence(
        case,
        notes=("  measured by DDS  ", "simulation reference"),
    )
    assert enriched.notes == (
        "existing",
        "measured by DDS",
        "simulation reference",
    )


def test_non_outcome_case_fields_are_unchanged() -> None:
    case = DecisionCase(case_id="case-1", notes=("existing",))
    enriched = add_outcome_evidence(
        case,
        double_dummy=(make_dd(),),
        simulations=(make_sim(),),
    )
    assert enriched.case_id == case.case_id
    assert enriched.bridgelab is case.bridgelab
    assert enriched.external == case.external
    assert enriched.corpus == case.corpus
    assert enriched.disagreements == case.disagreements


def test_integration_does_not_create_disagreements() -> None:
    enriched = add_outcome_evidence(
        DecisionCase(case_id="case-1"),
        double_dummy=(make_dd(),),
        simulations=(make_sim(),),
    )
    assert enriched.disagreements == ()


def test_original_case_is_unmodified() -> None:
    case = DecisionCase(case_id="case-1")
    enriched = add_outcome_evidence(case, notes=("new note",))
    assert case.notes == ()
    assert enriched.notes == ("new note",)


def test_generator_inputs_are_supported() -> None:
    dd, sim = make_dd(), make_sim()
    enriched = add_outcome_evidence(
        DecisionCase(case_id="case-1"),
        double_dummy=(x for x in (dd,)),
        simulations=(x for x in (sim,)),
        notes=(x for x in ("note",)),
    )
    assert enriched.double_dummy == (dd,)
    assert enriched.simulations == (sim,)
    assert enriched.notes == ("note",)


def test_invalid_case_is_rejected() -> None:
    with pytest.raises(TypeError, match="case must be DecisionCase"):
        add_outcome_evidence(object())


def test_invalid_double_dummy_entry_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="double_dummy entries must be DoubleDummyEvidence",
    ):
        add_outcome_evidence(
            DecisionCase(case_id="case-1"),
            double_dummy=(object(),),
        )


def test_invalid_simulation_entry_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="simulations entries must be SimulationStatistics",
    ):
        add_outcome_evidence(
            DecisionCase(case_id="case-1"),
            simulations=(object(),),
        )


@pytest.mark.parametrize("bad_note", ("", "   ", 42, None))
def test_invalid_note_is_rejected(bad_note) -> None:
    with pytest.raises(
        ValueError,
        match="notes entries must be non-blank strings",
    ):
        add_outcome_evidence(
            DecisionCase(case_id="case-1"),
            notes=(bad_note,),
        )


def test_non_iterable_outcome_inputs_are_rejected() -> None:
    case = DecisionCase(case_id="case-1")
    with pytest.raises(TypeError, match="simulations must be an iterable"):
        add_outcome_evidence(case, simulations=42)
    with pytest.raises(TypeError, match="double_dummy must be an iterable"):
        add_outcome_evidence(case, double_dummy=42)
    with pytest.raises(TypeError, match="notes must be an iterable"):
        add_outcome_evidence(case, notes=42)
