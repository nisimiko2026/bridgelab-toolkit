from benchmarks.phase17_historical_provenance import (
    current_phase17_source_readiness,
    validate_historical_report,
)
from core.provenance import HistoricalReproducibilityStatus


def _recorded():
    validation = validate_historical_report("17E")
    assert validation.is_valid_recorded_output
    assert validation.payload is not None
    return validation.payload


def test_phase17e_candidate_and_classification_remain_source_partial():
    result = _recorded()
    assert result["phase"] == "17E"
    assert result["candidate"] == "RESTRICTED_CHOICE"
    assert result["classification_before"] == result["classification_after"] == "SOURCE_PARTIAL"


def test_phase17e_untracked_source_history_is_not_resolved():
    assert _recorded()["provenance_history_found_for_untracked_sources"] is False
    assert current_phase17_source_readiness().status is HistoricalReproducibilityStatus.SOURCE_SNAPSHOT_MISSING


def test_phase17e_protected_sources_remain_unsafe_to_stage():
    protected = [r for r in _recorded()["source_records"] if r["provenance_classification"] in {"UNTRACKED_PROVENANCE_UNRESOLVED", "TRACKED_MODIFIED_USER_OWNED"}]
    assert protected
    assert all(not r["safe_to_modify"] and not r["safe_to_stage"] for r in protected)


def test_phase17e_source_contract_evidence_is_present_but_incomplete():
    result = _recorded()
    assert result["vacant_places_source_contract_present"] is True
    assert result["restricted_choice_observation_contract_present"] is True
    assert result["explicit_precision_rounding_contract_present"] is False


def test_phase17e_probability_question_scaffolding_exists_and_is_tested():
    result = _recorded()
    assert result["restricted_choice_question_exists"] is True
    assert result["vacant_places_question_exists"] is True
    assert result["question_scaffolding_tested"] is True


def test_phase17e_restricted_choice_and_vacant_places_engines_are_not_registered():
    result = _recorded()
    assert result["restricted_choice_engine_registered"] is False
    assert result["vacant_places_engine_registered"] is False
    assert result["registered_probability_engines"] == 1


def test_phase17e_production_remains_blocked():
    result = _recorded()
    assert result["source_executable"] is False
    assert result["production_implementation_authorized"] is False
    assert result["new_production_recommendations"] == 0


def test_phase17e_unresolved_dependencies_remain_explicit():
    assert set(_recorded()["unresolved_dependencies"]) == {"SOURCE_PROVENANCE", "VACANT_PLACES_INPUT_CONTRACT", "OBSERVATION_SEMANTICS", "PRECISION_AND_ROUNDING", "ARCHITECTURE_READINESS"}


def test_phase17e_gate_classifications_are_conservative():
    gates = {g["name"]: g for g in _recorded()["gate_results"]}
    assert gates["source_provenance"]["classification"] == "BLOCKED"
    for name in ("vacant_places_input_contract", "observation_semantics", "precision_and_rounding", "architecture_readiness"):
        assert gates[name]["classification"] == "SOURCE_PARTIAL"
        assert gates[name]["production_gate_passed"] is False
    assert gates["no_hidden_information"]["production_gate_passed"] is True
    assert gates["no_formula_invention"]["production_gate_passed"] is True


def test_phase17e_selects_contract_enrichment_not_implementation():
    assert _recorded()["phase17f_direction"] == "RESTRICTED_CHOICE_CONTRACT_ENRICHMENT"
