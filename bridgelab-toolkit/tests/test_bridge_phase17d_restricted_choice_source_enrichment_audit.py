from __future__ import annotations

from benchmarks.phase17_historical_provenance import (
    CURRENT_REQUIRED_SOURCE_PATHS,
    current_phase17_source_readiness,
    validate_historical_report,
)
from core.provenance import HistoricalReproducibilityStatus


def _recorded():
    validation = validate_historical_report("17D")
    assert validation.is_valid_recorded_output
    assert validation.payload is not None
    return validation.payload


def test_phase17d_candidate_is_restricted_choice() -> None:
    result = _recorded()
    assert result["phase"] == "17D"
    assert result["candidate"] == "RESTRICTED_CHOICE"


def test_phase17d_worked_source_contains_formula_and_action() -> None:
    result = _recorded()
    assert result["formula_present_in_worked_source"] is True
    assert result["worked_source_contains_exact_action_rule"] is True


def test_phase17d_is_not_source_executable() -> None:
    result = _recorded()
    assert result["source_executable"] is False
    assert result["production_implementation_authorized"] is False
    assert result["new_production_recommendations"] == 0


def test_phase17d_probability_engine_count_remains_one() -> None:
    assert _recorded()["registered_probability_engines"] == 1


def test_phase17d_required_sources_have_provenance_blockers() -> None:
    historical = _recorded()
    unresolved = {r["logical_path"] for r in historical["source_records"] if r["provenance_classification"] == "UNTRACKED_PROVENANCE_UNRESOLVED"}
    assert set(CURRENT_REQUIRED_SOURCE_PATHS[1:]) <= unresolved
    current = current_phase17_source_readiness()
    assert current.status is HistoricalReproducibilityStatus.SOURCE_SNAPSHOT_MISSING
    assert set(CURRENT_REQUIRED_SOURCE_PATHS) == set(current.missing_paths)


def test_phase17d_protected_sources_are_not_safe_to_stage() -> None:
    assert sum(not r["safe_to_stage"] for r in _recorded()["source_records"]) >= 3


def test_phase17d_unresolved_dependencies_are_explicit() -> None:
    assert set(_recorded()["unresolved_dependencies"]) == {"SOURCE_PROVENANCE", "VACANT_PLACES_INPUT_CONTRACT", "OBSERVATION_SEMANTICS", "PRECISION_AND_ROUNDING", "ARCHITECTURE_READINESS"}


def test_phase17d_preserves_safety_gates() -> None:
    gates = {g["name"]: g["passed"] for g in _recorded()["gate_results"]}
    assert gates["no_hidden_information"] is True
    assert gates["no_formula_invention"] is True


def test_phase17d_blocks_provenance_and_architecture_gates() -> None:
    gates = {g["name"]: g["passed"] for g in _recorded()["gate_results"]}
    for name in ("source_provenance_resolved", "vacant_places_contract_complete", "observation_semantics_complete", "precision_contract_complete", "architecture_proven_ready"):
        assert gates[name] is False


def test_phase17d_selects_further_source_enrichment() -> None:
    assert _recorded()["phase17e_direction"] == "FURTHER_RESTRICTED_CHOICE_SOURCE_ENRICHMENT"
