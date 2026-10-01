"""A3.14 source-manifest typed integration coverage."""

from bridge.capability_providers import (
    Capability,
    ProviderDescriptor,
)
from bridge.corpus import (
    CanonicalBoardRecord,
    SourceProvenance,
)
from bridge.decision_case import DecisionCase
from bridge.double_dummy_evidence import DoubleDummyEvidence
from bridge.evidence_roles import EvidenceRole
from bridge.evidence_source_manifest import (
    build_evidence_source_manifest,
)
from bridge.models import Seat
from bridge.simulation_statistics import SimulationStatistics
from bridge.trick_solver import (
    TrickSolverResult,
    TrickSolverStatus,
)


def corpus_record(
    *,
    provider: str = "bridge-deals",
    provider_version: str | None = "2025-04",
    record_id: str | None = "board-123",
) -> CanonicalBoardRecord:
    return CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider=provider,
            source="integration-test",
            record_id=record_id,
            provider_version=provider_version,
        ),
        dealer=Seat.NORTH,
        vulnerability=None,
    )

def double_dummy_evidence(
    *,
    provider_id: str = "dds",
    implementation: str = "dds3",
    version: str | None = "3.0.0",
) -> DoubleDummyEvidence:
    provider = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.DOUBLE_DUMMY,
        implementation=implementation,
        version=version,
    )

    result = TrickSolverResult(
        implementation=implementation,
        version=version,
        deal_id="deal-123",
        declarer=Seat.SOUTH,
        strain=None,
        opening_lead=None,
        status=TrickSolverStatus.SUCCESS,
        maximum_declarer_tricks=9,
        elapsed_seconds=0.01,
    )

    return DoubleDummyEvidence(
        provider=provider,
        result=result,
        source_ids=("deal-123",),
    )


def simulation_statistics() -> SimulationStatistics:
    return SimulationStatistics(
        runs=10,
        completed=8,
        abstained=1,
        max_steps=1,
        total_calls_added=24,
        max_calls_added=4,
        stop_reason_counts=(),
        stopped_seat_counts=(),
    )


def test_real_corpus_record_maps_to_observed_action_source():
    case = DecisionCase(
        case_id="a314-corpus",
        corpus=(corpus_record(),),
    )

    manifest = build_evidence_source_manifest(case)

    assert len(manifest.entries) == 1

    entry = manifest.entries[0]

    assert entry.role is EvidenceRole.OBSERVED_ACTION
    assert entry.source_kind == "corpus"
    assert entry.source_id == "bridge-deals"
    assert entry.version == "2025-04"
    assert entry.record_id == "board-123"
    assert entry.implementation is None


def test_corpus_unknown_identity_fields_remain_unknown():
    case = DecisionCase(
        case_id="a314-corpus-unknown",
        corpus=(
            corpus_record(
                provider="expert-corpus",
                provider_version=None,
                record_id=None,
            ),
        ),
    )

    manifest = build_evidence_source_manifest(case)

    entry = manifest.entries[0]

    assert entry.source_id == "expert-corpus"
    assert entry.version is None
    assert entry.record_id is None


def test_real_double_dummy_evidence_maps_to_outcome_measurement():
    case = DecisionCase(
        case_id="a314-dd",
        double_dummy=(double_dummy_evidence(),),
    )

    manifest = build_evidence_source_manifest(case)

    assert len(manifest.entries) == 1

    entry = manifest.entries[0]

    assert entry.role is EvidenceRole.OUTCOME_MEASUREMENT
    assert entry.source_kind == "double_dummy"
    assert entry.source_id == "dds"
    assert entry.implementation == "dds3"
    assert entry.version == "3.0.0"
    assert entry.record_id is None


def test_double_dummy_manifest_identity_comes_from_provider_descriptor():
    evidence = double_dummy_evidence(
        provider_id="precomputed-dd",
        implementation="reference-table",
        version="2026.1",
    )

    case = DecisionCase(
        case_id="a314-dd-provider",
        double_dummy=(evidence,),
    )

    manifest = build_evidence_source_manifest(case)

    entry = manifest.entries[0]

    assert entry.source_id == evidence.provider.provider_id
    assert entry.implementation == evidence.provider.implementation
    assert entry.version == evidence.provider.version


def test_simulation_statistics_remains_source_unknown():
    statistics = simulation_statistics()

    case = DecisionCase(
        case_id="a314-simulation",
        simulations=(statistics,),
    )

    manifest = build_evidence_source_manifest(case)

    assert len(manifest.entries) == 1

    entry = manifest.entries[0]

    assert entry.role is EvidenceRole.STATISTICAL_ESTIMATE
    assert entry.source_kind == "simulation"
    assert entry.source_id is None
    assert entry.implementation is None
    assert entry.version is None
    assert entry.record_id is None


def test_corpus_simulation_and_double_dummy_preserve_case_order_by_category():
    case = DecisionCase(
        case_id="a314-mixed",
        corpus=(
            corpus_record(
                provider="corpus-a",
                record_id="A",
            ),
            corpus_record(
                provider="corpus-b",
                record_id="B",
            ),
        ),
        simulations=(simulation_statistics(),),
        double_dummy=(
            double_dummy_evidence(
                provider_id="dds-a",
            ),
            double_dummy_evidence(
                provider_id="dds-b",
            ),
        ),
    )

    manifest = build_evidence_source_manifest(case)

    assert tuple(
        entry.role
        for entry in manifest.entries
    ) == (
        EvidenceRole.OBSERVED_ACTION,
        EvidenceRole.OBSERVED_ACTION,
        EvidenceRole.STATISTICAL_ESTIMATE,
        EvidenceRole.OUTCOME_MEASUREMENT,
        EvidenceRole.OUTCOME_MEASUREMENT,
    )

    assert tuple(
        entry.source_id
        for entry in manifest.entries
    ) == (
        "corpus-a",
        "corpus-b",
        None,
        "dds-a",
        "dds-b",
    )


def test_multiple_corpus_records_are_not_collapsed():
    case = DecisionCase(
        case_id="a314-corpus-duplicates",
        corpus=(
            corpus_record(
                provider="expert-corpus",
                record_id="board-1",
            ),
            corpus_record(
                provider="expert-corpus",
                record_id="board-2",
            ),
        ),
    )

    manifest = build_evidence_source_manifest(case)

    assert len(manifest.entries) == 2
    assert manifest.entries[0].record_id == "board-1"
    assert manifest.entries[1].record_id == "board-2"


def test_multiple_double_dummy_results_are_not_collapsed():
    case = DecisionCase(
        case_id="a314-dd-duplicates",
        double_dummy=(
            double_dummy_evidence(
                provider_id="dds",
                version="3.0",
            ),
            double_dummy_evidence(
                provider_id="dds",
                version="3.1",
            ),
        ),
    )

    manifest = build_evidence_source_manifest(case)

    assert len(manifest.entries) == 2
    assert manifest.entries[0].version == "3.0"
    assert manifest.entries[1].version == "3.1"


def test_building_manifest_does_not_mutate_typed_evidence():
    record = corpus_record()
    statistics = simulation_statistics()
    dd = double_dummy_evidence()

    case = DecisionCase(
        case_id="a314-immutable",
        corpus=(record,),
        simulations=(statistics,),
        double_dummy=(dd,),
    )

    original_corpus = case.corpus
    original_simulations = case.simulations
    original_double_dummy = case.double_dummy

    build_evidence_source_manifest(case)

    assert case.corpus is original_corpus
    assert case.simulations is original_simulations
    assert case.double_dummy is original_double_dummy

    assert case.corpus[0] is record
    assert case.simulations[0] is statistics
    assert case.double_dummy[0] is dd
