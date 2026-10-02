"""A6.7.1 outcome simulation evidence correction tests."""

import pytest

from bridge.auction import Bid, Contract, Strain
from bridge.capability_providers import Capability, ProviderDescriptor
from bridge.decision_case import DecisionCase
from bridge.double_dummy_evidence import DoubleDummyEvidence
from bridge.models import Seat, Suit, Vulnerability
from bridge.outcome_evidence import add_outcome_evidence
from bridge.simulation_outcome import summarize_simulation_outcomes
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


def make_outcome_simulation():
    contract = Contract(
        bid=Bid(level=4, strain=Strain.SPADES),
        declarer=Seat.NORTH,
    )
    return summarize_simulation_outcomes(
        contract=contract,
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(9, 10, 10, 11),
    )


def make_auction_simulation_statistics() -> SimulationStatistics:
    return SimulationStatistics(
        runs=10,
        completed=8,
        abstained=1,
        max_steps=1,
        total_calls_added=20,
        max_calls_added=4,
        stop_reason_counts=(
            ("auction-complete", 8),
            ("max-steps", 1),
            ("no-recommendation", 1),
        ),
        stopped_seat_counts=(("N", 1),),
    )


def test_decision_case_accepts_outcome_simulation_summary() -> None:
    summary = make_outcome_simulation()
    case = DecisionCase(
        case_id="case-1",
        outcome_simulations=(summary,),
    )
    assert case.outcome_simulations == (summary,)


def test_auction_and_outcome_simulations_are_separate() -> None:
    auction_stats = make_auction_simulation_statistics()
    outcome_summary = make_outcome_simulation()

    case = DecisionCase(
        case_id="case-1",
        simulations=(auction_stats,),
        outcome_simulations=(outcome_summary,),
    )

    assert case.simulations == (auction_stats,)
    assert case.outcome_simulations == (outcome_summary,)


def test_outcome_evidence_appends_outcome_simulation() -> None:
    case = DecisionCase(case_id="case-1")
    summary = make_outcome_simulation()

    enriched = add_outcome_evidence(
        case,
        outcome_simulations=(summary,),
    )

    assert enriched.outcome_simulations == (summary,)
    assert enriched.simulations == ()
    assert case.outcome_simulations == ()


def test_existing_outcome_simulations_are_preserved_in_order() -> None:
    first = make_outcome_simulation()
    second = make_outcome_simulation()
    case = DecisionCase(
        case_id="case-1",
        outcome_simulations=(first,),
    )

    enriched = add_outcome_evidence(
        case,
        outcome_simulations=(second,),
    )

    assert enriched.outcome_simulations == (first, second)


def test_existing_auction_simulations_are_not_modified() -> None:
    auction_stats = make_auction_simulation_statistics()
    case = DecisionCase(
        case_id="case-1",
        simulations=(auction_stats,),
    )

    enriched = add_outcome_evidence(
        case,
        outcome_simulations=(make_outcome_simulation(),),
    )

    assert enriched.simulations == (auction_stats,)


def test_double_dummy_is_appended() -> None:
    case = DecisionCase(case_id="case-1")
    dd = make_dd()

    enriched = add_outcome_evidence(case, double_dummy=(dd,))

    assert enriched.double_dummy == (dd,)
    assert case.double_dummy == ()


def test_outcome_and_double_dummy_can_be_added_together() -> None:
    summary = make_outcome_simulation()
    dd = make_dd()

    enriched = add_outcome_evidence(
        DecisionCase(case_id="case-1"),
        outcome_simulations=(summary,),
        double_dummy=(dd,),
    )

    assert enriched.outcome_simulations == (summary,)
    assert enriched.double_dummy == (dd,)


def test_notes_are_appended_and_trimmed() -> None:
    case = DecisionCase(case_id="case-1", notes=("existing",))

    enriched = add_outcome_evidence(
        case,
        notes=("  measured outcome  ",),
    )

    assert enriched.notes == ("existing", "measured outcome")


def test_non_outcome_fields_are_unchanged() -> None:
    case = DecisionCase(case_id="case-1")

    enriched = add_outcome_evidence(
        case,
        outcome_simulations=(make_outcome_simulation(),),
        double_dummy=(make_dd(),),
    )

    assert enriched.case_id == case.case_id
    assert enriched.bridgelab is case.bridgelab
    assert enriched.external == case.external
    assert enriched.corpus == case.corpus
    assert enriched.disagreements == case.disagreements


def test_integration_does_not_create_disagreements() -> None:
    enriched = add_outcome_evidence(
        DecisionCase(case_id="case-1"),
        outcome_simulations=(make_outcome_simulation(),),
        double_dummy=(make_dd(),),
    )
    assert enriched.disagreements == ()


def test_original_case_is_unmodified() -> None:
    case = DecisionCase(case_id="case-1")
    enriched = add_outcome_evidence(
        case,
        outcome_simulations=(make_outcome_simulation(),),
    )
    assert case.outcome_simulations == ()
    assert enriched.outcome_simulations


def test_generator_inputs_are_supported() -> None:
    summary = make_outcome_simulation()
    dd = make_dd()

    enriched = add_outcome_evidence(
        DecisionCase(case_id="case-1"),
        outcome_simulations=(x for x in (summary,)),
        double_dummy=(x for x in (dd,)),
        notes=(x for x in ("note",)),
    )

    assert enriched.outcome_simulations == (summary,)
    assert enriched.double_dummy == (dd,)
    assert enriched.notes == ("note",)


def test_invalid_case_is_rejected() -> None:
    with pytest.raises(TypeError, match="case must be DecisionCase"):
        add_outcome_evidence(object())


def test_decision_case_rejects_wrong_outcome_simulation_type() -> None:
    with pytest.raises(
        TypeError,
        match="outcome_simulations entries must be SimulationOutcomeSummary",
    ):
        DecisionCase(
            case_id="case-1",
            outcome_simulations=(make_auction_simulation_statistics(),),
        )


def test_outcome_evidence_rejects_auction_statistics_as_outcome() -> None:
    with pytest.raises(
        TypeError,
        match="outcome_simulations entries must be SimulationOutcomeSummary",
    ):
        add_outcome_evidence(
            DecisionCase(case_id="case-1"),
            outcome_simulations=(make_auction_simulation_statistics(),),
        )


def test_invalid_double_dummy_entry_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="double_dummy entries must be DoubleDummyEvidence",
    ):
        add_outcome_evidence(
            DecisionCase(case_id="case-1"),
            double_dummy=(object(),),
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


def test_non_iterable_inputs_are_rejected() -> None:
    case = DecisionCase(case_id="case-1")

    with pytest.raises(
        TypeError,
        match="outcome_simulations must be an iterable",
    ):
        add_outcome_evidence(case, outcome_simulations=42)

    with pytest.raises(TypeError, match="double_dummy must be an iterable"):
        add_outcome_evidence(case, double_dummy=42)

    with pytest.raises(TypeError, match="notes must be an iterable"):
        add_outcome_evidence(case, notes=42)
