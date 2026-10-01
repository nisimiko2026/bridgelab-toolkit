"""Source manifest for evidence stored in a BridgeLab DecisionCase.

The manifest identifies where evidence came from and what semantic role
it plays. It does not rank sources, compare recommendations, assign
authority, vote, score providers, or select a winner.
"""

from __future__ import annotations

from dataclasses import dataclass

from .decision_case import DecisionCase
from .evidence_roles import EvidenceRole


@dataclass(frozen=True, slots=True)
class EvidenceSourceEntry:
    """Identity and role of one evidence source."""

    role: EvidenceRole
    source_kind: str
    source_id: str | None
    implementation: str | None = None
    version: str | None = None
    record_id: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceSourceManifest:
    """Ordered source manifest for one decision case."""

    case_id: str
    entries: tuple[EvidenceSourceEntry, ...]

    def for_role(
        self,
        role: EvidenceRole,
    ) -> tuple[EvidenceSourceEntry, ...]:
        """Return manifest entries carrying one semantic role."""

        return tuple(
            entry
            for entry in self.entries
            if entry.role is role
        )


def build_evidence_source_manifest(
    case: DecisionCase,
) -> EvidenceSourceManifest:
    """Build a passive source manifest from a DecisionCase."""

    entries: list[EvidenceSourceEntry] = []

    if case.bridgelab is not None:
        provider = case.bridgelab.result.provider
        entries.append(
            EvidenceSourceEntry(
                role=EvidenceRole.POLICY_RECOMMENDATION,
                source_kind="provider",
                source_id=provider.provider_id,
                implementation=provider.implementation,
                version=provider.version,
            )
        )

    for evidence in case.external:
        provider = evidence.result.provider
        entries.append(
            EvidenceSourceEntry(
                role=EvidenceRole.EXTERNAL_RECOMMENDATION,
                source_kind="provider",
                source_id=provider.provider_id,
                implementation=provider.implementation,
                version=provider.version,
            )
        )

    for record in case.corpus:
        provenance = record.provenance
        entries.append(
            EvidenceSourceEntry(
                role=EvidenceRole.OBSERVED_ACTION,
                source_kind="corpus",
                source_id=provenance.provider,
                version=provenance.provider_version,
                record_id=provenance.record_id,
            )
        )

    for statistics in case.simulations:
        entries.append(
            EvidenceSourceEntry(
                role=EvidenceRole.STATISTICAL_ESTIMATE,
                source_kind="simulation",
                source_id=None,
            )
        )

    for evidence in case.double_dummy:
        provider = evidence.provider
        entries.append(
            EvidenceSourceEntry(
                role=EvidenceRole.OUTCOME_MEASUREMENT,
                source_kind="double_dummy",
                source_id=provider.provider_id,
                implementation=provider.implementation,
                version=provider.version,
            )
        )

    return EvidenceSourceManifest(
        case_id=case.case_id,
        entries=tuple(entries),
    )
