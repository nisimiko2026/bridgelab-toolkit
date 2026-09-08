from __future__ import annotations

from benchmarks.phase17_historical_provenance import validate_historical_report


def _recorded():
    validation = validate_historical_report("17C")
    assert validation.is_valid_recorded_output
    assert validation.payload is not None
    return validation.payload


def test_phase17c_remains_source_partial() -> None:
    result = _recorded()
    assert result["classification_before"] == "SOURCE_PARTIAL"
    assert result["classification_after"] == "SOURCE_PARTIAL"
    assert result["source_executable"] is False


def test_phase17c_does_not_authorize_production() -> None:
    result = _recorded()
    assert result["production_implementation_authorized"] is False
    assert result["new_production_recommendations"] == 0


def test_phase17c_preserves_hidden_information_boundary() -> None:
    gates = {gate["name"]: gate for gate in _recorded()["gate_results"]}
    assert gates["no_hidden_information_or_invention"]["passed"] is True


def test_phase17c_identifies_probability_blockers() -> None:
    dependencies = _recorded()["unregistered_probability_dependencies"]
    assert {"VACANT_PLACES", "RESTRICTED_CHOICE", "CONDITIONAL_PERCENTAGE_PLAY"} <= set(dependencies)


def test_phase17c_keeps_known_card_count_as_existing_engine() -> None:
    assert _recorded()["registered_probability_engines_required"] == ["KNOWN_CARD_COUNT"]


def test_phase17c_all_action_gates_remain_blocked() -> None:
    assert sum(not gate["passed"] for gate in _recorded()["gate_results"]) == 9


def test_phase17c_has_one_safety_integrity_gate_passed() -> None:
    passed = [gate for gate in _recorded()["gate_results"] if gate["passed"]]
    assert [gate["name"] for gate in passed] == ["no_hidden_information_or_invention"]


def test_phase17c_selects_probability_source_enrichment() -> None:
    assert _recorded()["phase17d_direction"] == "PROBABILITY_SOURCE_ENRICHMENT"
