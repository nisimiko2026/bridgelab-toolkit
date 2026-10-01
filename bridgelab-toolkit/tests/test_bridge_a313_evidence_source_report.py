"""A3.13 evidence-source report tests."""

import json

from bridge.evidence_roles import EvidenceRole
from bridge.evidence_source_manifest import (
    EvidenceSourceEntry,
    EvidenceSourceManifest,
)
from bridge.evidence_source_report import (
    build_evidence_source_report,
)


def test_empty_manifest_produces_empty_report():
    manifest = EvidenceSourceManifest(
        case_id="a313-empty",
        entries=(),
    )

    report = build_evidence_source_report(manifest)

    assert report.case_id == "a313-empty"
    assert report.entries == ()
    assert report.total == 0


def test_provider_source_fields_are_preserved():
    manifest = EvidenceSourceManifest(
        case_id="a313-provider",
        entries=(
            EvidenceSourceEntry(
                role=EvidenceRole.EXTERNAL_RECOMMENDATION,
                source_kind="provider",
                source_id="ben",
                implementation="ben-rest",
                version="0.8.8.7",
            ),
        ),
    )

    report = build_evidence_source_report(manifest)

    entry = report.entries[0]

    assert entry.role == "external_recommendation"
    assert entry.source_kind == "provider"
    assert entry.source_id == "ben"
    assert entry.implementation == "ben-rest"
    assert entry.version == "0.8.8.7"
    assert entry.record_id is None


def test_corpus_record_identity_is_preserved():
    manifest = EvidenceSourceManifest(
        case_id="a313-corpus",
        entries=(
            EvidenceSourceEntry(
                role=EvidenceRole.OBSERVED_ACTION,
                source_kind="corpus",
                source_id="bridge-deals",
                version="2025-04",
                record_id="board-123",
            ),
        ),
    )

    report = build_evidence_source_report(manifest)

    entry = report.entries[0]

    assert entry.role == "observed_action"
    assert entry.source_kind == "corpus"
    assert entry.source_id == "bridge-deals"
    assert entry.version == "2025-04"
    assert entry.record_id == "board-123"


def test_unknown_simulation_source_remains_unknown():
    manifest = EvidenceSourceManifest(
        case_id="a313-simulation",
        entries=(
            EvidenceSourceEntry(
                role=EvidenceRole.STATISTICAL_ESTIMATE,
                source_kind="simulation",
                source_id=None,
            ),
        ),
    )

    report = build_evidence_source_report(manifest)

    entry = report.entries[0]

    assert entry.role == "statistical_estimate"
    assert entry.source_id is None
    assert entry.implementation is None
    assert entry.version is None
    assert entry.record_id is None


def test_entry_order_is_preserved():
    manifest = EvidenceSourceManifest(
        case_id="a313-order",
        entries=(
            EvidenceSourceEntry(
                role=EvidenceRole.POLICY_RECOMMENDATION,
                source_kind="provider",
                source_id="bridgelab",
            ),
            EvidenceSourceEntry(
                role=EvidenceRole.EXTERNAL_RECOMMENDATION,
                source_kind="provider",
                source_id="ben",
            ),
            EvidenceSourceEntry(
                role=EvidenceRole.EXTERNAL_RECOMMENDATION,
                source_kind="provider",
                source_id="brl",
            ),
        ),
    )

    report = build_evidence_source_report(manifest)

    assert tuple(
        entry.source_id
        for entry in report.entries
    ) == (
        "bridgelab",
        "ben",
        "brl",
    )


def test_same_source_id_entries_are_not_collapsed():
    manifest = EvidenceSourceManifest(
        case_id="a313-duplicate",
        entries=(
            EvidenceSourceEntry(
                role=EvidenceRole.EXTERNAL_RECOMMENDATION,
                source_kind="provider",
                source_id="ben",
                version="v1",
            ),
            EvidenceSourceEntry(
                role=EvidenceRole.EXTERNAL_RECOMMENDATION,
                source_kind="provider",
                source_id="ben",
                version="v2",
            ),
        ),
    )

    report = build_evidence_source_report(manifest)

    assert report.total == 2
    assert report.entries[0].version == "v1"
    assert report.entries[1].version == "v2"


def test_as_dict_is_json_friendly():
    manifest = EvidenceSourceManifest(
        case_id="a313-json",
        entries=(
            EvidenceSourceEntry(
                role=EvidenceRole.OUTCOME_MEASUREMENT,
                source_kind="double_dummy",
                source_id="dds",
                implementation="dds3",
                version="3.0.0",
            ),
        ),
    )

    report = build_evidence_source_report(manifest)

    payload = report.as_dict()
    encoded = json.dumps(payload)

    assert isinstance(encoded, str)
    assert payload["case_id"] == "a313-json"
    assert payload["total"] == 1

    assert payload["entries"][0] == {
        "role": "outcome_measurement",
        "source_kind": "double_dummy",
        "source_id": "dds",
        "implementation": "dds3",
        "version": "3.0.0",
        "record_id": None,
    }


def test_report_has_no_winner_or_scoring_fields():
    manifest = EvidenceSourceManifest(
        case_id="a313-passive",
        entries=(
            EvidenceSourceEntry(
                role=EvidenceRole.EXTERNAL_RECOMMENDATION,
                source_kind="provider",
                source_id="ben",
            ),
        ),
    )

    report = build_evidence_source_report(manifest)

    assert not hasattr(report, "winner")
    assert not hasattr(report, "preferred")
    assert not hasattr(report, "score")
    assert not hasattr(report, "recommendation")


def test_building_report_does_not_modify_manifest():
    entry = EvidenceSourceEntry(
        role=EvidenceRole.EXTERNAL_RECOMMENDATION,
        source_kind="provider",
        source_id="ben",
    )

    manifest = EvidenceSourceManifest(
        case_id="a313-immutable",
        entries=(entry,),
    )

    original_entries = manifest.entries

    build_evidence_source_report(manifest)

    assert manifest.entries is original_entries
    assert manifest.entries[0] is entry
