from __future__ import annotations

from benchmarks.phase17b_declarer_source_enrichment_audit import run_audit


def test_phase17b_audit_runs_cleanly() -> None:
    result = run_audit()

    assert result.fixtures_failed == 0
    assert result.fixtures_passed == result.deterministic_fixtures


def test_phase17b_selected_candidate_is_safety_play() -> None:
    result = run_audit()

    assert result.selected_candidate == "safety play"
    assert result.before_classification == "SOURCE_PARTIAL"
    assert result.after_classification == "SOURCE_PARTIAL"


def test_phase17b_preserves_declarer_inventory() -> None:
    result = run_audit()

    assert result.declarer_candidates_considered == 9
    assert result.prospective_declarer_candidates == 8


def test_phase17b_modifies_only_one_canonical_source_file() -> None:
    result = run_audit()

    assert result.canonical_source_files_modified == 1
    assert result.selected_source_path == (
        "knowledge/play/declarer-play/general-techniques/safety-play.md"
    )


def test_phase17b_does_not_claim_source_executable() -> None:
    result = run_audit()

    assert result.source_executable is False

    assert result.source_executable_gate_items == 10
    assert result.source_executable_gate_items_passed == 0
    assert result.source_executable_gate_items_failed == 10


def test_phase17b_preserves_unresolved_source_boundaries() -> None:
    result = run_audit()

    assert result.unresolved_source_items == 8
    assert result.architecture_blocked_requirements > 0
    assert result.unsupported_probability_requirements > 0


def test_phase17b_adds_no_bridge_intelligence() -> None:
    result = run_audit()

    assert result.new_production_recommendations == 0
    assert result.unsupported_additions == 0
    assert result.invented_bridge_facts == 0
    assert result.hidden_information_violations == 0


def test_phase17b_probability_engine_boundary_remains_closed() -> None:
    result = run_audit()

    assert result.probability_requirements == 1
    assert result.supported_probability_requirements == 0
    assert result.unsupported_probability_requirements == 1


def test_phase17b_architecture_is_only_partially_ready() -> None:
    result = run_audit()

    assert result.architecture_requirements == 10

    assert (
        result.architecture_representable_requirements
        + result.architecture_blocked_requirements
        == result.architecture_requirements
    )

    assert result.architecture_representable_requirements == 7
    assert result.architecture_blocked_requirements == 3


def test_phase17b_selects_further_source_enrichment() -> None:
    result = run_audit()

    assert result.phase17c_direction == (
        "C. FURTHER DECLARER SOURCE ENRICHMENT"
    )
