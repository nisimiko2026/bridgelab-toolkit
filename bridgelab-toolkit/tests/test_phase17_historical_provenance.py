from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

from benchmarks import (
    phase17f_restricted_choice_contract_enrichment_audit,
    phase17g_restricted_choice_supporting_source_audit,
    phase17h_restricted_choice_contract_gap_resolution_audit,
    phase17i_restricted_choice_contract_enrichment_audit,
    phase17j_restricted_choice_contract_enrichment_audit,
    phase17k_restricted_choice_close_defer_audit,
)
from benchmarks.phase17_bridge_intelligence_source_readiness_audit import (
    run_phase17_source_readiness_audit,
)
from benchmarks.phase17_historical_provenance import (
    CURRENT_REQUIRED_SOURCE_PATHS,
    GIT_ROOT,
    MISSING_SOURCE_SNAPSHOTS,
    PHASE17_HISTORICAL_REPORT_MANIFEST,
    PHASE17C_BACKUP_MEMBER_BLOB,
    current_phase17_source_readiness,
    validate_historical_payload,
    validate_historical_report,
    validate_phase17c_backup_member,
)
from bridge import create_standard_sayc_router
from bridge.declarer_play_state import PlayedCard
from bridge.models import Card, Seat, Suit
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY
from bridge.probability_questions import (
    RestrictedChoiceQuestion,
    VacantPlacesQuestion,
)
from core.provenance import (
    HistoricalReproducibilityStatus,
    ProvenanceStatus,
    ProvenanceValidator,
)


PHASES = ("17C", "17D", "17E", "17F", "17G", "17H", "17I", "17J", "17K")


@pytest.mark.parametrize("phase", PHASES)
def test_historical_phase17_report_is_blob_pinned_recorded_output(phase: str) -> None:
    result = validate_historical_report(phase)
    assert result.artifact.status is ProvenanceStatus.AUTHORIZED
    assert result.artifact.current_blob_oid == (
        PHASE17_HISTORICAL_REPORT_MANIFEST[phase].expected_blob_oid
    )
    assert result.is_valid_recorded_output
    assert result.payload is not None and result.payload["phase"] == phase


def test_historical_report_blob_mismatch_is_rejected() -> None:
    entry = replace(
        PHASE17_HISTORICAL_REPORT_MANIFEST["17C"],
        expected_blob_oid="0" * 40,
    )
    result = ProvenanceValidator(GIT_ROOT).resolve_and_validate(entry)
    assert result.status is ProvenanceStatus.IDENTITY_MISMATCH


def test_historical_report_phase_mismatch_is_rejected() -> None:
    errors = validate_historical_payload(
        "17C",
        {
            "phase": "17D",
            "source_executable": False,
            "production_implementation_authorized": False,
            "new_production_recommendations": 0,
            "classification_after": "SOURCE_PARTIAL",
            "registered_probability_engines_required": ["KNOWN_CARD_COUNT"],
            "gate_results": [{"name": "recorded"}],
        },
    )
    assert errors == ("phase mismatch: expected 17C, observed '17D'",)


def test_authorized_output_does_not_claim_source_reproducibility() -> None:
    result = validate_historical_report("17K")
    assert result.artifact.status is ProvenanceStatus.AUTHORIZED
    assert (
        result.reproducibility.output_status
        is HistoricalReproducibilityStatus.RECORDED_OUTPUT_ONLY
    )
    assert (
        result.reproducibility.source_status
        is HistoricalReproducibilityStatus.SOURCE_SNAPSHOT_MISSING
    )
    assert result.reproducibility.missing_source_snapshots == MISSING_SOURCE_SNAPSHOTS


def test_current_readiness_distinguishes_baseline_from_missing_snapshots() -> None:
    readiness = current_phase17_source_readiness()
    assert readiness.available_paths == (CURRENT_REQUIRED_SOURCE_PATHS[0],)
    assert readiness.missing_paths == CURRENT_REQUIRED_SOURCE_PATHS[1:]
    assert dict(readiness.source_states) == {
        CURRENT_REQUIRED_SOURCE_PATHS[0]: (
            "TRACKED_BASELINE_PRESENT_BUT_HISTORICAL_CONTENT_UNAVAILABLE"
        ),
        CURRENT_REQUIRED_SOURCE_PATHS[1]: "MISSING",
        CURRENT_REQUIRED_SOURCE_PATHS[2]: "MISSING",
        CURRENT_REQUIRED_SOURCE_PATHS[3]: "MISSING",
    }


def test_exact_phase17c_zip_member_is_blob_pinned_without_extraction() -> None:
    result = validate_phase17c_backup_member()
    assert result.status is ProvenanceStatus.AUTHORIZED
    assert result.member_blob_oid == PHASE17C_BACKUP_MEMBER_BLOB
    assert result.content


def test_missing_phase17c_zip_member_is_rejected() -> None:
    result = validate_phase17c_backup_member(member_path="not/approved/missing.md")
    assert result.status is ProvenanceStatus.MISSING
    assert result.content is None


def test_phase17f_to_k_have_no_temporary_extraction_dependency() -> None:
    modules = (
        phase17f_restricted_choice_contract_enrichment_audit,
        phase17g_restricted_choice_supporting_source_audit,
        phase17h_restricted_choice_contract_gap_resolution_audit,
        phase17i_restricted_choice_contract_enrichment_audit,
        phase17j_restricted_choice_contract_enrichment_audit,
        phase17k_restricted_choice_close_defer_audit,
    )
    assert all("phase17c_fullkit_temp" not in inspect.getsource(module) for module in modules)


def test_historical_validation_changes_no_production_invariants() -> None:
    audit = run_phase17_source_readiness_audit()
    registry = DEFAULT_PROBABILITY_ENGINE_REGISTRY
    assert audit.production_guards["production_recommendations"] == 4
    assert len(create_standard_sayc_router().routes) == 45
    assert len(registry.registrations) == 1
    assert registry.calculator_for(
        RestrictedChoiceQuestion(
            "restricted",
            subject_suit=Suit.SPADES,
            observed_defender=Seat.EAST,
            observed_play=PlayedCard(Seat.EAST, Card.parse("KS")),
        )
    ) is None
    assert registry.calculator_for(
        VacantPlacesQuestion(
            "vacant",
            subject_suit=Suit.SPADES,
            defenders=(Seat.EAST, Seat.WEST),
        )
    ) is None
