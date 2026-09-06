from __future__ import annotations

from benchmarks.phase17d_restricted_choice_source_enrichment_audit import (
    run_phase17d_restricted_choice_source_enrichment_audit,
)


def test_phase17d_candidate_is_restricted_choice() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    assert result.phase == "17D"
    assert result.candidate == "RESTRICTED_CHOICE"


def test_phase17d_worked_source_contains_formula_and_action() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    assert result.formula_present_in_worked_source is True
    assert result.worked_source_contains_exact_action_rule is True


def test_phase17d_is_not_source_executable() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    assert result.source_executable is False
    assert result.production_implementation_authorized is False
    assert result.new_production_recommendations == 0


def test_phase17d_probability_engine_count_remains_one() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    assert result.registered_probability_engines == 1


def test_phase17d_required_sources_have_provenance_blockers() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    unresolved = {
        record.logical_path
        for record in result.source_records
        if record.provenance_classification
        == "UNTRACKED_PROVENANCE_UNRESOLVED"
    }

    assert (
        "knowledge/play/counting/vacant-places.md"
        in unresolved
    )

    assert (
        "knowledge/play/declarer-play/general-techniques/"
        "restricted-choice.md"
        in unresolved
    )

    assert (
        "knowledge/play/declarer-play/probability/finesse/"
        "a8732-vs-k1065-restricted-choice.md"
        in unresolved
    )


def test_phase17d_protected_sources_are_not_safe_to_stage() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    protected = [
        record
        for record in result.source_records
        if not record.safe_to_stage
    ]

    assert len(protected) >= 3


def test_phase17d_unresolved_dependencies_are_explicit() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    expected = {
        "SOURCE_PROVENANCE",
        "VACANT_PLACES_INPUT_CONTRACT",
        "OBSERVATION_SEMANTICS",
        "PRECISION_AND_ROUNDING",
        "ARCHITECTURE_READINESS",
    }

    assert set(result.unresolved_dependencies) == expected


def test_phase17d_preserves_safety_gates() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    gate_map = {
        gate.name: gate.passed
        for gate in result.gate_results
    }

    assert gate_map["no_hidden_information"] is True
    assert gate_map["no_formula_invention"] is True


def test_phase17d_blocks_provenance_and_architecture_gates() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    gate_map = {
        gate.name: gate.passed
        for gate in result.gate_results
    }

    assert gate_map["source_provenance_resolved"] is False
    assert gate_map["vacant_places_contract_complete"] is False
    assert gate_map["observation_semantics_complete"] is False
    assert gate_map["precision_contract_complete"] is False
    assert gate_map["architecture_proven_ready"] is False


def test_phase17d_selects_further_source_enrichment() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()

    assert result.phase17e_direction == (
        "FURTHER_RESTRICTED_CHOICE_SOURCE_ENRICHMENT"
    )
