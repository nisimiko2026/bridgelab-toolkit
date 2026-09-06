from __future__ import annotations

from benchmarks.phase17c_safety_play_blocker_audit import (
    run_phase17c_safety_play_blocker_audit,
)


def test_phase17c_remains_source_partial() -> None:
    audit = run_phase17c_safety_play_blocker_audit()

    assert audit.classification_before == "SOURCE_PARTIAL"
    assert audit.classification_after == "SOURCE_PARTIAL"
    assert audit.source_executable is False


def test_phase17c_does_not_authorize_production() -> None:
    audit = run_phase17c_safety_play_blocker_audit()

    assert audit.production_implementation_authorized is False
    assert audit.new_production_recommendations == 0


def test_phase17c_preserves_hidden_information_boundary() -> None:
    audit = run_phase17c_safety_play_blocker_audit()

    hidden_gate = next(
        gate
        for gate in audit.gate_results
        if gate.name == "no_hidden_information_or_invention"
    )

    assert hidden_gate.passed is True


def test_phase17c_identifies_probability_blockers() -> None:
    audit = run_phase17c_safety_play_blocker_audit()

    assert "VACANT_PLACES" in audit.unregistered_probability_dependencies
    assert "RESTRICTED_CHOICE" in audit.unregistered_probability_dependencies
    assert (
        "CONDITIONAL_PERCENTAGE_PLAY"
        in audit.unregistered_probability_dependencies
    )


def test_phase17c_keeps_known_card_count_as_existing_engine() -> None:
    audit = run_phase17c_safety_play_blocker_audit()

    assert audit.registered_probability_engines_required == (
        "KNOWN_CARD_COUNT",
    )


def test_phase17c_all_action_gates_remain_blocked() -> None:
    audit = run_phase17c_safety_play_blocker_audit()

    failed = [gate for gate in audit.gate_results if not gate.passed]

    assert len(failed) == 9


def test_phase17c_has_one_safety_integrity_gate_passed() -> None:
    audit = run_phase17c_safety_play_blocker_audit()

    passed = [gate for gate in audit.gate_results if gate.passed]

    assert len(passed) == 1
    assert passed[0].name == "no_hidden_information_or_invention"


def test_phase17c_selects_probability_source_enrichment() -> None:
    audit = run_phase17c_safety_play_blocker_audit()

    assert audit.phase17d_direction == "PROBABILITY_SOURCE_ENRICHMENT"
