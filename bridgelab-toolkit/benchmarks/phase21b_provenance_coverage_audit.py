"""Conservative, static provenance coverage inventory for production BridgeLab.

This audit reports repository evidence.  It does not infer bridge correctness,
source authority, or production readiness from paths, Git identity, or tests.
"""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from benchmarks.phase17_historical_provenance import (
    PHASE17_HISTORICAL_REPORT_MANIFEST,
    PHASE17C_FULL_KIT_MANIFEST,
)
from benchmarks.phase17b_declarer_source_enrichment_audit import PHASE17A_MANIFEST
from bridge.bidding_rules import KnowledgeSource
from bridge.declarer_recommendation import UNBLOCK_SOURCE, DeclarerTechnique
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY
from bridge.sayc_route_configuration import create_standard_sayc_router
from core.provenance import (
    ProvenanceCategory,
    ProvenanceManifestEntry,
    ProvenanceValidator,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GIT_ROOT = PROJECT_ROOT.parent
KNOWLEDGE_ROOT = GIT_ROOT / "knowledge"


class ProductionElementType(str, Enum):
    BIDDING_ROUTE = "BIDDING_ROUTE"
    PROBABILITY_ENGINE = "PROBABILITY_ENGINE"
    DECLARER_TECHNIQUE = "DECLARER_TECHNIQUE"
    DEFENSIVE_ALGORITHM = "DEFENSIVE_ALGORITHM"
    OPENING_LEAD_ALGORITHM = "OPENING_LEAD_ALGORITHM"


class ProvenanceLinkState(str, Enum):
    DIRECT = "DIRECT"
    RUNTIME_CONDITIONAL = "RUNTIME_CONDITIONAL"
    INDIRECT_MANIFEST = "INDIRECT_MANIFEST"
    NO_LINK = "NO_LINK"
    BROKEN = "BROKEN"
    AMBIGUOUS = "AMBIGUOUS"


class ResolutionState(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class ArtifactPresenceState(str, Enum):
    PRESENT = "PRESENT"
    HISTORICAL_ONLY = "HISTORICAL_ONLY"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class VerificationState(str, Enum):
    BLOB_VERIFIED = "BLOB_VERIFIED"
    PATH_TRACKED = "PATH_TRACKED"
    DECLARED_ONLY = "DECLARED_ONLY"
    UNVERIFIED = "UNVERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class AuthorityState(str, Enum):
    EXISTING_AUTHENTICATED_CLASSIFICATION = "EXISTING_AUTHENTICATED_CLASSIFICATION"
    SUPPORTING_ONLY = "SUPPORTING_ONLY"
    HISTORICAL_RECORD = "HISTORICAL_RECORD"
    PARTIAL = "PARTIAL"
    PARTNERSHIP_DEPENDENT = "PARTNERSHIP_DEPENDENT"
    UNKNOWN = "UNKNOWN"


class CoverageState(str, Enum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ProductionProvenanceEntry:
    element_type: ProductionElementType
    element_id: str
    registry_name: str
    registered: bool
    engine_type: str
    route_id: str | None
    link_state: ProvenanceLinkState
    resolution_state: ResolutionState
    artifact_state: ArtifactPresenceState
    verification_state: VerificationState
    authority_state: AuthorityState
    coverage_state: CoverageState
    source_ids: tuple[str, ...] = ()
    classification_notes: str = ""


@dataclass(frozen=True, slots=True)
class RouteRuleEdge:
    route_id: str
    engine_type: str
    rule_id: str
    occurrence: int


@dataclass(frozen=True, slots=True)
class SourceArtifactEntry:
    source_id: str
    source_kind: str
    display_name: str
    declared_path: str
    heading: str | None
    manifest_id: str | None
    category: str | None
    provenance_commit: str | None
    expected_blob_oid: str | None
    resolution_state: ResolutionState
    artifact_presence: ArtifactPresenceState
    verification_state: VerificationState
    authority_state: AuthorityState
    referenced_by_count: int


@dataclass(frozen=True, slots=True)
class DeferredCapabilityStatus:
    capability_id: str
    classification: str
    production_registered: bool
    facts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProvenanceCoverageAudit:
    production_entries: tuple[ProductionProvenanceEntry, ...]
    route_rule_edges: tuple[RouteRuleEdge, ...]
    source_artifacts: tuple[SourceArtifactEntry, ...]
    deferred_capabilities: tuple[DeferredCapabilityStatus, ...]
    primary_summary: tuple[tuple[str, int], ...]
    source_summary: tuple[tuple[str, int], ...]
    diagnostics: tuple[tuple[str, int], ...]
    limitations: tuple[str, ...]
    audit_status: str


def _manifest_entries() -> tuple[ProvenanceManifestEntry, ...]:
    return (
        PHASE17A_MANIFEST,
        *tuple(PHASE17_HISTORICAL_REPORT_MANIFEST[key] for key in sorted(PHASE17_HISTORICAL_REPORT_MANIFEST)),
        PHASE17C_FULL_KIT_MANIFEST,
    )


def _route_and_rule_inventory() -> tuple[
    tuple[ProductionProvenanceEntry, ...],
    tuple[RouteRuleEdge, ...],
    tuple[str, ...],
    int,
]:
    router = create_standard_sayc_router()
    production: list[ProductionProvenanceEntry] = []
    edges: list[RouteRuleEdge] = []
    modules: set[str] = set()
    rule_objects: set[int] = set()
    for route in router.routes:
        production.append(
            ProductionProvenanceEntry(
                ProductionElementType.BIDDING_ROUTE,
                route.route_id,
                "STANDARD_SAYC_ROUTER",
                True,
                type(route.engine).__name__,
                route.route_id,
                ProvenanceLinkState.RUNTIME_CONDITIONAL,
                ResolutionState.UNKNOWN,
                ArtifactPresenceState.UNKNOWN,
                VerificationState.NOT_APPLICABLE,
                AuthorityState.UNKNOWN,
                CoverageState.NOT_ESTABLISHED,
                classification_notes=(
                    "The route has no provenance field; applicable RuleDecision values "
                    "must carry KnowledgeSource references."
                ),
            )
        )
        for occurrence, rule in enumerate(route.engine.rules):
            modules.add(type(rule).__module__)
            rule_objects.add(id(rule))
            edges.append(RouteRuleEdge(route.route_id, type(route.engine).__name__, rule.rule_id, occurrence))
    return tuple(production), tuple(edges), tuple(sorted(modules)), len(rule_objects)


def _production_inventory() -> tuple[
    tuple[ProductionProvenanceEntry, ...],
    tuple[RouteRuleEdge, ...],
    tuple[str, ...],
    int,
]:
    routes, edges, rule_modules, unique_rule_objects = _route_and_rule_inventory()
    declarer_resolution, declarer_presence, declarer_verification = (
        _knowledge_reference_state(UNBLOCK_SOURCE)
    )
    probability = tuple(
        ProductionProvenanceEntry(
            ProductionElementType.PROBABILITY_ENGINE,
            question_type.__name__,
            "DEFAULT_PROBABILITY_ENGINE_REGISTRY",
            True,
            calculator.__name__,
            None,
            ProvenanceLinkState.NO_LINK,
            ResolutionState.NOT_APPLICABLE,
            ArtifactPresenceState.UNKNOWN,
            VerificationState.NOT_APPLICABLE,
            AuthorityState.UNKNOWN,
            CoverageState.NOT_ESTABLISHED,
            classification_notes="Production probability evidence has no attached KnowledgeSource.",
        )
        for question_type, calculator in DEFAULT_PROBABILITY_ENGINE_REGISTRY.registrations
    )
    declarer = (
        ProductionProvenanceEntry(
            ProductionElementType.DECLARER_TECHNIQUE,
            DeclarerTechnique.SIMPLE_UNBLOCK_KING.value,
            "DECLARER_RECOMMENDATION_ENGINE",
            True,
            "evaluate_declarer_play",
            None,
            ProvenanceLinkState.DIRECT,
            declarer_resolution,
            declarer_presence,
            declarer_verification,
            AuthorityState.UNKNOWN,
            CoverageState.NOT_ESTABLISHED,
            (UNBLOCK_SOURCE.serialize(),),
            (
                "Direct production reference; neither source authority nor exact "
                "capability coverage is established by the citation alone."
            ),
        ),
    )
    return (
        tuple(
            sorted(
                (*routes, *probability, *declarer),
                key=lambda item: (item.element_type.value, item.element_id),
            )
        ),
        edges,
        rule_modules,
        unique_rule_objects,
    )


def _module_path(module_name: str) -> Path:
    return PROJECT_ROOT.joinpath(*module_name.split(".")).with_suffix(".py")


def _literal_strings(tree: ast.Module) -> dict[str, str]:
    values: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
            value = node.value
        else:
            continue
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            for target in targets:
                if isinstance(target, ast.Name):
                    values[target.id] = value.value
    return values


def _string_value(node: ast.expr, constants: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def _knowledge_source_references(modules: tuple[str, ...]) -> tuple[tuple[KnowledgeSource, ...], int, int]:
    references: list[KnowledgeSource] = []
    constructor_count = 0
    unresolved = 0
    inspected_modules = {
        *modules,
        "bridge.declarer_recommendation",
        "bridge.probability_engine",
    }
    for module_name in sorted(inspected_modules):
        tree = ast.parse(_module_path(module_name).read_text(encoding="utf-8"))
        constants = _literal_strings(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "KnowledgeSource":
                continue
            constructor_count += 1
            if not node.args:
                unresolved += 1
                continue
            article = _string_value(node.args[0], constants)
            heading = _string_value(node.args[1], constants) if len(node.args) > 1 else None
            if article is None or (len(node.args) > 1 and heading is None):
                unresolved += 1
                continue
            references.append(KnowledgeSource(article, heading))
    unique = {source.serialize(): source for source in references}
    return tuple(unique[key] for key in sorted(unique)), constructor_count, unresolved


def _git_tracked(relative_path: str) -> bool:
    import subprocess

    completed = subprocess.run(
        ("git", "-C", str(GIT_ROOT), "ls-files", "--error-unmatch", "--", relative_path),
        check=False,
        capture_output=True,
    )
    return completed.returncode == 0


def _headings(path: Path) -> frozenset[str]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return frozenset()
    return frozenset(line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#"))


def _knowledge_reference_state(
    source: KnowledgeSource,
) -> tuple[ResolutionState, ArtifactPresenceState, VerificationState]:
    relative = f"knowledge/{source.article_id}.md"
    path = GIT_ROOT / relative
    present = path.is_file()
    heading_resolved = present and (
        source.heading is None or source.heading in _headings(path)
    )
    return (
        ResolutionState.RESOLVED if heading_resolved else ResolutionState.UNRESOLVED,
        ArtifactPresenceState.PRESENT if present else ArtifactPresenceState.MISSING,
        (
            VerificationState.PATH_TRACKED
            if present and _git_tracked(relative)
            else VerificationState.UNVERIFIED
        ),
    )


def _knowledge_artifacts(sources: tuple[KnowledgeSource, ...]) -> tuple[SourceArtifactEntry, ...]:
    article_counts = Counter(source.article_id for source in sources)
    entries: list[SourceArtifactEntry] = []
    for source in sources:
        relative = f"knowledge/{source.article_id}.md"
        path = GIT_ROOT / relative
        present = path.is_file()
        heading_resolved = source.heading is None or source.heading in _headings(path)
        entries.append(
            SourceArtifactEntry(
                f"knowledge:{source.serialize()}",
                "KNOWLEDGE_SOURCE_REFERENCE",
                source.serialize(),
                relative,
                source.heading,
                None,
                ProvenanceCategory.SOURCE.value,
                None,
                None,
                ResolutionState.RESOLVED if present and heading_resolved else ResolutionState.UNRESOLVED,
                ArtifactPresenceState.PRESENT if present else ArtifactPresenceState.MISSING,
                VerificationState.PATH_TRACKED if present and _git_tracked(relative) else VerificationState.UNVERIFIED,
                AuthorityState.UNKNOWN,
                article_counts[source.article_id],
            )
        )
    return tuple(entries)


def _manifest_artifacts() -> tuple[SourceArtifactEntry, ...]:
    validator = ProvenanceValidator(GIT_ROOT)
    entries: list[SourceArtifactEntry] = []
    for manifest in _manifest_entries():
        result = validator.resolve_and_validate(manifest)
        entries.append(
            SourceArtifactEntry(
                f"manifest:{manifest.logical_id}",
                "PROVENANCE_MANIFEST_ARTIFACT",
                manifest.logical_id,
                result.repository_relative_path or manifest.canonical_path,
                None,
                manifest.logical_id,
                manifest.category.value,
                manifest.provenance_commit,
                manifest.expected_blob_oid,
                ResolutionState.RESOLVED if result.resolved_path else ResolutionState.UNRESOLVED,
                ArtifactPresenceState.HISTORICAL_ONLY if result.resolved_path else ArtifactPresenceState.MISSING,
                VerificationState.BLOB_VERIFIED if result.is_authorized else VerificationState.UNVERIFIED,
                AuthorityState.HISTORICAL_RECORD,
                0,
            )
        )
    return tuple(entries)


def _deferred_capabilities() -> tuple[DeferredCapabilityStatus, ...]:
    return (
        DeferredCapabilityStatus("NATURAL_1NT_RESPONSES", "DOCUMENT_ONLY", False, ("Phase 19 deferred",)),
        DeferredCapabilityStatus("RESTRICTED_CHOICE", "SOURCE_PARTIAL", False, ("authenticated historical outputs", "required current sources missing", "historical source snapshots unavailable")),
        DeferredCapabilityStatus("SAFETY_PLAY", "SOURCE_PARTIAL", False, ("Phase 19 deferred",)),
        DeferredCapabilityStatus("SECOND_HAND_LOW", "DEFERRED", False, ("source contract incomplete",)),
        DeferredCapabilityStatus("STANDARD_HONOR_LEAD", "DEFERRED", False, ("suit selection and exceptions incomplete",)),
        DeferredCapabilityStatus("THIRD_HAND_HIGH", "DEFERRED", False, ("source contract incomplete",)),
        DeferredCapabilityStatus("VACANT_PLACES", "SOURCE_PARTIAL", False, ("exact ZIP member blob-pinned", "historical recorded evidence only", "current canonical source missing", "reproducibility unavailable")),
    )


def _counts(values: list[str]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(Counter(values).items()))


def run_audit() -> ProvenanceCoverageAudit:
    production, edges, rule_modules, unique_rule_objects = _production_inventory()
    sources, constructor_count, unresolved_constructors = _knowledge_source_references(rule_modules)
    knowledge = _knowledge_artifacts(sources)
    manifests = _manifest_artifacts()
    source_artifacts = tuple(sorted((*knowledge, *manifests), key=lambda item: item.source_id))

    primary_summary = tuple(sorted({
        "primary_production_elements": len(production),
        "bidding_routes": sum(item.element_type is ProductionElementType.BIDDING_ROUTE for item in production),
        "probability_engines": sum(item.element_type is ProductionElementType.PROBABILITY_ENGINE for item in production),
        "declarer_techniques": sum(item.element_type is ProductionElementType.DECLARER_TECHNIQUE for item in production),
        "defensive_algorithms": 0,
        "opening_lead_algorithms": 0,
        **{f"link_{key}": value for key, value in _counts([item.link_state.value for item in production])},
        **{f"resolution_{key}": value for key, value in _counts([item.resolution_state.value for item in production])},
        **{f"artifact_{key}": value for key, value in _counts([item.artifact_state.value for item in production])},
        **{f"verification_{key}": value for key, value in _counts([item.verification_state.value for item in production])},
        **{f"authority_{key}": value for key, value in _counts([item.authority_state.value for item in production])},
        **{f"coverage_{key}": value for key, value in _counts([item.coverage_state.value for item in production])},
    }.items()))
    source_summary = tuple(sorted({
        "combined_inventory_entries": len(source_artifacts),
        "knowledge_source_references": len(knowledge),
        "knowledge_article_ids": len({item.declared_path for item in knowledge}),
        "knowledge_references_resolved": sum(
            item.resolution_state is ResolutionState.RESOLVED for item in knowledge
        ),
        "knowledge_references_unresolved": sum(
            item.resolution_state is ResolutionState.UNRESOLVED for item in knowledge
        ),
        "manifest_entries": len(manifests),
        "manifest_artifacts_authorized": sum(item.verification_state is VerificationState.BLOB_VERIFIED for item in manifests),
        "manifest_source_category": sum(item.category == ProvenanceCategory.SOURCE.value for item in manifests),
        "historical_only_artifacts": sum(item.artifact_presence is ArtifactPresenceState.HISTORICAL_ONLY for item in source_artifacts),
        "blob_verified_artifacts": sum(item.verification_state is VerificationState.BLOB_VERIFIED for item in source_artifacts),
    }.items()))
    diagnostics = tuple(sorted({
        "production_reachable_modules_inspected": len(
            {
                *rule_modules,
                "bridge.declarer_recommendation",
                "bridge.probability_engine",
            }
        ),
        "knowledge_source_constructor_calls": constructor_count,
        "statically_resolved_knowledge_sources": len(sources),
        "unresolved_knowledge_source_constructors": unresolved_constructors,
        "route_rule_edges": len(edges),
        "unique_rule_ids": len({edge.rule_id for edge in edges}),
        "unique_rule_objects": unique_rule_objects,
        "unique_rule_occurrences": len(edges),
        "routes_without_rules": len({item.route_id for item in production if item.element_type is ProductionElementType.BIDDING_ROUTE and not any(edge.route_id == item.route_id for edge in edges)}),
    }.items()))
    limitations = (
        "KnowledgeSource references do not establish source authority or bridge correctness.",
        "Route provenance is runtime-conditional because routes have no direct provenance field.",
        "Git and blob verification authenticate repository artifacts, not bridge theory.",
        "Exact heading-text mismatch is not treated as proof that a source article is invalid.",
        "Deferred capabilities are not production registrations.",
    )
    expected = {
        "production": 47,
        "routes": 45,
        "edges": 134,
        "rules": 92,
        "manifests": 11,
        "authorized": 11,
    }
    observed = {
        "production": len(production),
        "routes": sum(item.element_type is ProductionElementType.BIDDING_ROUTE for item in production),
        "edges": len(edges),
        "rules": len({edge.rule_id for edge in edges}),
        "manifests": len(manifests),
        "authorized": sum(item.verification_state is VerificationState.BLOB_VERIFIED for item in manifests),
    }
    return ProvenanceCoverageAudit(
        production,
        edges,
        source_artifacts,
        _deferred_capabilities(),
        primary_summary,
        source_summary,
        diagnostics,
        limitations,
        "PASS" if observed == expected else "FAIL",
    )


def _print_counts(title: str, counts: tuple[tuple[str, int], ...]) -> None:
    print(title)
    for key, value in counts:
        print(f"{key} = {value}")


def main() -> int:
    audit = run_audit()
    _print_counts("PRODUCTION PROVENANCE COVERAGE", audit.primary_summary)
    _print_counts("SOURCE ARTIFACT INVENTORY", audit.source_summary)
    print("LINK / RESOLUTION SUMMARY")
    for key, value in audit.primary_summary:
        if key.startswith(("link_", "resolution_")):
            print(f"{key} = {value}")
    print("VERIFICATION SUMMARY")
    for key, value in audit.primary_summary:
        if key.startswith(("artifact_", "verification_")):
            print(f"{key} = {value}")
    print("AUTHORITY / UNKNOWN SUMMARY")
    for key, value in audit.primary_summary:
        if key.startswith(("authority_", "coverage_")):
            print(f"{key} = {value}")
    print("DEFERRED CAPABILITY SOURCE STATUS")
    for item in audit.deferred_capabilities:
        print(f"{item.capability_id} = {item.classification}; registered = {str(item.production_registered).lower()}")
    print("LIMITATIONS")
    for limitation in audit.limitations:
        print(f"- {limitation}")
    _print_counts("DIAGNOSTIC OBSERVATIONS", audit.diagnostics)
    print("DISCLAIMER")
    print("Repository provenance coverage does not by itself establish bridge-theory correctness or source authority.")
    print(f"audit status = {audit.audit_status}")
    return 0 if audit.audit_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
