from __future__ import annotations

from benchmarks.phase17f_restricted_choice_contract_enrichment_audit import (
    UNRESOLVED_DEPENDENCIES,
    run_audit,
)
from benchmarks.phase17_historical_provenance import (
    current_phase17_source_readiness,
    validate_historical_report,
)
from core.provenance import HistoricalReproducibilityStatus


def _recorded():
    validation = validate_historical_report("17F")
    assert validation.is_valid_recorded_output
    assert validation.payload is not None
    return validation.payload


def test_phase17f_candidate_and_classification() -> None:
    result = run_audit()

    assert result.phase == "17F"
    assert result.baseline_phase == "17E"
    assert result.candidate == "Restricted Choice Contract Enrichment"
    assert result.classification_before == "SOURCE_PARTIAL"
    assert result.classification_after == "SOURCE_PARTIAL"


def test_phase17f_source_provenance_remains_blocked() -> None:
    historical = _recorded()
    assert historical["historical_backup_found"] is True
    assert historical["historical_backup_is_identical"] is False
    assert historical["historical_backup_git_tracked"] is False
    current = current_phase17_source_readiness()
    assert current.status is HistoricalReproducibilityStatus.SOURCE_SNAPSHOT_MISSING
    assert current.is_source_reproducible is False


def test_phase17f_protected_sources_are_not_safe_to_stage() -> None:
    result = run_audit()

    protected = {
        record.logical_path: record
        for record in result.source_records
        if not record.safe_to_stage
    }

    assert "knowledge/play/counting/vacant-places.md" in protected
    assert (
        "knowledge/play/declarer-play/general-techniques/"
        "restricted-choice.md"
        in protected
    )
    assert (
        "knowledge/play/declarer-play/probability/"
        "percentage-plays.md"
        in protected
    )
    assert (
        "knowledge/play/declarer-play/probability/finesse/"
        "a8732-vs-k1065-restricted-choice.md"
        in protected
    )


def test_phase17f_vacant_places_contract_evidence_is_present() -> None:
    historical = _recorded()
    assert historical["vacant_places_relationship_contract_present"] is True
    assert historical["vacant_places_practical_procedure_present"] is True
    assert historical["vacant_places_uncertainty_guard_present"] is True
    assert run_audit().vacant_places_relationship_contract_present is False


def test_phase17f_restricted_choice_observation_evidence_is_present() -> None:
    historical = _recorded()
    assert historical["restricted_choice_observation_procedure_present"] is True
    assert historical["restricted_choice_noncertainty_guard_present"] is True
    assert run_audit().restricted_choice_observation_procedure_present is False


def test_phase17f_precision_contract_remains_partial() -> None:
    historical = _recorded()
    assert historical["worked_percentage_outputs_present"] is True
    assert historical["worked_equal_choice_present"] is True
    assert historical["explicit_precision_rounding_contract_present"] is False
    assert run_audit().worked_percentage_outputs_present is False


def test_phase17f_probability_architecture_is_scaffolding_only() -> None:
    result = run_audit()

    assert result.restricted_choice_question_exists is True
    assert result.vacant_places_question_exists is True
    assert result.restricted_choice_engine_registered is False
    assert result.vacant_places_engine_registered is False
    assert result.registered_probability_engines == 1


def test_phase17f_production_remains_blocked() -> None:
    result = run_audit()

    assert result.source_executable is False
    assert result.production_implementation_authorized is False
    assert result.new_production_recommendations == 0


def test_phase17f_unresolved_dependencies_are_exact() -> None:
    result = run_audit()

    assert result.unresolved_dependencies == UNRESOLVED_DEPENDENCIES
    assert result.unresolved_dependencies == (
        "SOURCE_PROVENANCE",
        "VACANT_PLACES_INPUT_CONTRACT",
        "OBSERVATION_SEMANTICS",
        "PRECISION_AND_ROUNDING",
        "ARCHITECTURE_READINESS",
    )


def test_phase17f_gate_classifications_are_conservative() -> None:
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


def test_phase17f_selects_contract_enrichment_for_phase17g() -> None:
    result = run_audit()

    assert (
        result.phase17g_direction
        == "RESTRICTED_CHOICE_CONTRACT_ENRICHMENT"
    )
