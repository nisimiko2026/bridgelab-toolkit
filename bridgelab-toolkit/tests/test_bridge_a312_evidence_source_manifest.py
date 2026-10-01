"""A3.12 evidence-source manifest tests."""

from bridge.auction import Call
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_case import DecisionCase
from bridge.decision_evidence import (
    DecisionEvidence,
    EvidenceScope,
)
from bridge.evidence_roles import EvidenceRole
from bridge.evidence_source_manifest import (
    build_evidence_source_manifest,
)
from bridge.simulation_statistics import SimulationStatistics


def bidding_evidence(
    provider_id: str,
    call: str,
    scope: EvidenceScope,
    *,
    implementation: str | None = None,
    version: str | None = "test",
) -> DecisionEvidence:
    provider = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation=(
            implementation
            if implementation is not None
            else f"{provider_id}-test"
        ),
        version=version,
    )

    return DecisionEvidence(
        result=CapabilityResult(
            provider=provider,
            status=ProviderStatus.SUCCESS,
            recommendation=Call.parse(call),
        ),
        scope=scope,
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


def test_empty_case_has_empty_manifest():
    manifest = build_evidence_source_manifest(
        DecisionCase(case_id="a312-empty")
    )

    assert manifest.case_id == "a312-empty"
    assert manifest.entries == ()


def test_bridgelab_provider_identity_is_preserved():
    bridge = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
        implementation="bridgelab-policy",
        version="1",
    )

    manifest = build_evidence_source_manifest(
        DecisionCase(
            case_id="a312-policy",
            bridgelab=bridge,
        )
    )

    entry = manifest.entries[0]

    assert entry.role is EvidenceRole.POLICY_RECOMMENDATION
    assert entry.source_kind == "provider"
    assert entry.source_id == "bridgelab"
    assert entry.implementation == "bridgelab-policy"
    assert entry.version == "1"


def test_external_provider_identity_is_preserved():
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
        implementation="ben-rest",
        version="0.8.8.7",
    )

    manifest = build_evidence_source_manifest(
        DecisionCase(
            case_id="a312-ben",
            external=(ben,),
        )
    )

    entry = manifest.entries[0]

    assert entry.role is EvidenceRole.EXTERNAL_RECOMMENDATION
    assert entry.source_id == "ben"
    assert entry.implementation == "ben-rest"
    assert entry.version == "0.8.8.7"


def test_multiple_external_sources_preserve_order():
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )
    brl = bidding_evidence(
        "brl",
        "3H",
        EvidenceScope.PROVIDER,
    )

    manifest = build_evidence_source_manifest(
        DecisionCase(
            case_id="a312-order",
            external=(ben, brl),
        )
    )

    assert tuple(
        entry.source_id
        for entry in manifest.entries
    ) == ("ben", "brl")


def test_simulation_does_not_invent_provider_identity():
    statistics = simulation_statistics()

    manifest = build_evidence_source_manifest(
        DecisionCase(
            case_id="a312-simulation",
            simulations=(statistics,),
        )
    )

    entry = manifest.entries[0]

    assert entry.role is EvidenceRole.STATISTICAL_ESTIMATE
    assert entry.source_kind == "simulation"
    assert entry.source_id is None
    assert entry.implementation is None
    assert entry.version is None
    assert entry.record_id is None


def test_for_role_filters_without_reordering():
    bridge = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
    )
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )
    brl = bidding_evidence(
        "brl",
        "3H",
        EvidenceScope.PROVIDER,
    )

    manifest = build_evidence_source_manifest(
        DecisionCase(
            case_id="a312-filter",
            bridgelab=bridge,
            external=(ben, brl),
        )
    )

    external = manifest.for_role(
        EvidenceRole.EXTERNAL_RECOMMENDATION
    )

    assert tuple(
        entry.source_id
        for entry in external
    ) == ("ben", "brl")


def test_same_recommendation_does_not_merge_sources():
    bridge = bidding_evidence(
        "bridgelab",
        "4H",
        EvidenceScope.PARTNERSHIP,
    )
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    manifest = build_evidence_source_manifest(
        DecisionCase(
            case_id="a312-same",
            bridgelab=bridge,
            external=(ben,),
        )
    )

    assert len(manifest.entries) == 2

    assert manifest.entries[0].role is (
        EvidenceRole.POLICY_RECOMMENDATION
    )
    assert manifest.entries[1].role is (
        EvidenceRole.EXTERNAL_RECOMMENDATION
    )

    assert manifest.entries[0].source_id == "bridgelab"
    assert manifest.entries[1].source_id == "ben"


def test_manifest_has_no_winner_or_scoring_fields():
    manifest = build_evidence_source_manifest(
        DecisionCase(
            case_id="a312-passive",
            bridgelab=bidding_evidence(
                "bridgelab",
                "3C",
                EvidenceScope.PARTNERSHIP,
            ),
            external=(
                bidding_evidence(
                    "ben",
                    "4H",
                    EvidenceScope.PROVIDER,
                ),
            ),
        )
    )

    assert not hasattr(manifest, "winner")
    assert not hasattr(manifest, "preferred")
    assert not hasattr(manifest, "score")
    assert not hasattr(manifest, "recommendation")


def test_building_manifest_does_not_modify_case():
    bridge = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
    )
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    case = DecisionCase(
        case_id="a312-immutable",
        bridgelab=bridge,
        external=(ben,),
        notes=("Original.",),
    )

    original_external = case.external
    original_notes = case.notes

    build_evidence_source_manifest(case)

    assert case.bridgelab is bridge
    assert case.external is original_external
    assert case.notes is original_notes
