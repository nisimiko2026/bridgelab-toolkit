from __future__ import annotations

from benchmarks.phase17k_restricted_choice_close_defer_audit import (
    UNRESOLVED_DEPENDENCIES,
    run_audit,
)


def test_phase17k_candidate_and_classification() -> None:
    result = run_audit()

    assert result.phase == "17K"
    assert result.baseline_phase == "17J"
    assert result.candidate == "Restricted Choice Close/Defer Audit"
    assert result.classification_before == "SOURCE_PARTIAL"
    assert result.classification_after == "SOURCE_PARTIAL"


def test_phase17k_source_provenance_remains_blocked() -> None:
    result = run_audit()

    assert result.historical_backup_found is True
    assert result.historical_backup_is_identical is False
    assert result.historical_backup_git_tracked is False
    assert result.vacant_places_git_history_found is False

    source_by_path = {
        record.logical_path: record
        for record in result.source_records
    }

    assert (
        source_by_path[
            "knowledge/play/counting/vacant-places.md"
        ].provenance_classification
        == "UNTRACKED_PROVENANCE_UNRESOLVED"
    )
    assert (
        source_by_path[
            "knowledge/play/declarer-play/general-techniques/"
            "restricted-choice.md"
        ].provenance_classification
        == "UNTRACKED_PROVENANCE_UNRESOLVED"
    )



def test_phase17k_protected_sources_are_not_safe_to_stage() -> None:
    result = run_audit()

    assert len(result.source_records) == 7
    assert all(record.safe_to_stage is False for record in result.source_records)


def test_phase17k_vacant_places_contract_evidence_is_present() -> None:
    result = run_audit()

    assert result.vacant_places_relationship_contract_present is True
    assert result.vacant_places_practical_procedure_present is True
    assert result.vacant_places_uncertainty_guard_present is True


def test_phase17k_restricted_choice_observation_evidence_is_present() -> None:
    result = run_audit()

    assert result.restricted_choice_observation_procedure_present is True
    assert result.restricted_choice_noncertainty_guard_present is True


def test_phase17k_precision_contract_remains_partial() -> None:
    result = run_audit()

    assert result.worked_percentage_outputs_present is True
    assert result.worked_equal_choice_present is True
    assert result.explicit_precision_rounding_contract_present is False


def test_phase17k_probability_architecture_is_scaffolding_only() -> None:
    result = run_audit()

    assert result.restricted_choice_question_exists is True
    assert result.vacant_places_question_exists is True
    assert result.restricted_choice_engine_registered is False
    assert result.vacant_places_engine_registered is False
    assert result.registered_probability_engines == 1


def test_phase17k_production_remains_blocked() -> None:
    result = run_audit()

    assert result.source_executable is False
    assert result.production_implementation_authorized is False
    assert result.new_production_recommendations == 0


def test_phase17k_unresolved_dependencies_are_exact() -> None:
    result = run_audit()

    assert result.unresolved_dependencies == UNRESOLVED_DEPENDENCIES
    assert result.unresolved_dependencies == (
        "SOURCE_PROVENANCE",
        "VACANT_PLACES_INPUT_CONTRACT",
        "OBSERVATION_SEMANTICS",
        "PRECISION_AND_ROUNDING",
        "ARCHITECTURE_READINESS",
    )


def test_phase17k_gate_classifications_are_conservative() -> None:
    result = run_audit()

    gates = {
        gate.name: gate
        for gate in result.gates
    }

    assert gates["SOURCE_PROVENANCE"].classification == "BLOCKED"
    assert gates["SOURCE_PROVENANCE"].production_gate_passed is False

    assert (
        gates["VACANT_PLACES_INPUT_CONTRACT"].classification
        == "SOURCE_PARTIAL"
    )
    assert (
        gates["VACANT_PLACES_INPUT_CONTRACT"].production_gate_passed
        is False
    )

    assert (
        gates["OBSERVATION_SEMANTICS"].classification
        == "SOURCE_PARTIAL"
    )
    assert (
        gates["OBSERVATION_SEMANTICS"].production_gate_passed
        is False
    )

    assert (
        gates["PRECISION_AND_ROUNDING"].classification
        == "SOURCE_PARTIAL"
    )
    assert (
        gates["PRECISION_AND_ROUNDING"].production_gate_passed
        is False
    )

    assert (
        gates["ARCHITECTURE_READINESS"].classification
        == "SOURCE_PARTIAL"
    )
    assert (
        gates["ARCHITECTURE_READINESS"].production_gate_passed
        is False
    )

    assert gates["NO_HIDDEN_INFORMATION"].classification == "COMPLETE"
    assert (
        gates["NO_HIDDEN_INFORMATION"].production_gate_passed
        is True
    )

    assert gates["NO_FORMULA_INVENTION"].classification == "COMPLETE"
    assert (
        gates["NO_FORMULA_INVENTION"].production_gate_passed
        is True
    )


def test_phase17k_closes_and_defers_restricted_choice_work() -> None:
    result = run_audit()

    assert result.disposition == "DEFERRED"
    assert result.phase17_closed is True
    assert "new authoritative source evidence" in result.resume_condition
    assert "unresolved production blockers" in result.resume_condition
    assert not hasattr(result, "phase17l_direction")


def test_phase17k_contract_gaps_remain_unresolved() -> None:
    result = run_audit()

    assert result.source_provenance_gap_resolved is False
    assert result.vacant_places_input_contract_gap_resolved is False
    assert result.observation_semantics_gap_resolved is False
    assert result.precision_and_rounding_gap_resolved is False
    assert result.architecture_readiness_gap_resolved is False
