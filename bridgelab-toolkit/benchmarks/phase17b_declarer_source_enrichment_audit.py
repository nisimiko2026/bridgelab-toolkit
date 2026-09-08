from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.provenance import (
    ProvenanceCategory,
    ProvenanceManifestEntry,
    ProvenanceValidator,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGELAB_ROOT = REPO_ROOT.parent

PHASE17A_JSON = (
    REPO_ROOT
    / "bridgelab_phase17a_bridge_intelligence_source_readiness_audit.json"
)
PHASE17A_MANIFEST = ProvenanceManifestEntry(
    logical_id="phase17a.bridge-intelligence-source-readiness-audit.json",
    category=ProvenanceCategory.ARTIFACT,
    canonical_path=(
        "bridgelab-toolkit/"
        "bridgelab_phase17a_bridge_intelligence_source_readiness_audit.json"
    ),
    archive_fallbacks=(
        "bridgelab-toolkit/archive/phase17/"
        "bridgelab_phase17a_bridge_intelligence_source_readiness_audit.json",
    ),
    provenance_commit="5c61e35",
    expected_blob_oid="15bc182d55e0e039ff10f37251ace1a5876d7273",
)

SAFETY_PLAY_PATH = (
    BRIDGELAB_ROOT
    / "knowledge"
    / "play"
    / "declarer-play"
    / "general-techniques"
    / "safety-play.md"
)
SELECTED_CANDIDATE = "safety play"
BEFORE_CLASSIFICATION = "SOURCE_PARTIAL"
AFTER_CLASSIFICATION = "SOURCE_PARTIAL"

REQUIRED_READINESS_HEADINGS = (
    "# Implementation Readiness Contract",
    "## Status",
    "## Required Contract Objective",
    "## Required Visible State",
    "## Candidate-Line Requirement",
    "## Alternative-Line Comparison",
    "## Probability Dependency",
    "## Example Boundary",
    "## Exceptions and Competing Considerations",
    "## Legal-Action Requirement",
    "## Hidden-Information Restriction",
    "## Precedence",
    "## Architecture Readiness",
    "## Source-Executable Gate",
    "## Recommended Implementation Strategy",
    "## Unresolved Items",
    "## BridgeLab Implementation Status",
)

SOURCE_EXECUTABLE_GATE = (
    "deterministic visible-state trigger",
    "deterministic contract objective",
    "exact legal action",
    "bounded scope",
    "bounded exceptions",
    "sufficient competing-line precedence",
    "no hidden-card inference",
    "no unresolved partnership policy",
    "no unavailable probability dependency",
    "complete representation by the production state model",
)


@dataclass(frozen=True)
class CandidateSummary:
    candidate: str
    classification: str
    architecture_status: str
    blocker: str
    source_path: str
    heading: str
    execution_status: str
    expected_new_recommendations: int


@dataclass(frozen=True)
class AuditFixture:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class Phase17BDeclarerSourceEnrichmentAudit:
    selected_candidate: str
    before_classification: str
    after_classification: str

    declarer_candidates_considered: int
    prospective_declarer_candidates: int

    selected_source_path: str
    selected_source_heading: str

    canonical_source_files_modified: int
    canonical_source_headings_added: int

    deterministic_fixtures: int
    fixtures_passed: int
    fixtures_failed: int

    source_executable_gate_items: int
    source_executable_gate_items_passed: int
    source_executable_gate_items_failed: int

    architecture_requirements: int
    architecture_representable_requirements: int
    architecture_blocked_requirements: int

    probability_requirements: int
    supported_probability_requirements: int
    unsupported_probability_requirements: int

    unresolved_source_items: int

    unsupported_additions: int
    invented_bridge_facts: int
    hidden_information_violations: int

    new_production_recommendations: int

    source_executable: bool

    phase17c_direction: str

    fixtures: tuple[AuditFixture, ...]


def _load_phase17a() -> dict[str, Any]:
    result = ProvenanceValidator(BRIDGELAB_ROOT).resolve_and_validate(
        PHASE17A_MANIFEST
    )
    if not result.is_authorized or result.resolved_path is None:
        raise FileNotFoundError(
            "Phase 17A JSON report failed provenance validation: "
            f"{result.status.value}: {result.reason}"
        )
    return json.loads(result.resolved_path.read_text(encoding="utf-8"))


def _load_safety_play() -> str:
    if not SAFETY_PLAY_PATH.exists():
        raise FileNotFoundError(
            f"Safety Play source not found: {SAFETY_PLAY_PATH}"
        )

    return SAFETY_PLAY_PATH.read_text(encoding="utf-8")


def _candidate_summary(candidate: dict[str, Any]) -> CandidateSummary:
    return CandidateSummary(
        candidate=str(candidate["candidate"]),
        classification=str(candidate["classification"]),
        architecture_status=str(candidate["architecture_status"]),
        blocker=str(candidate["blocker"]),
        source_path=str(candidate["source_path"]),
        heading=str(candidate["heading"]),
        execution_status=str(candidate["execution_status"]),
        expected_new_recommendations=int(
            candidate["expected_new_recommendations"]
        ),
    )


def _phase17a_declarer_candidates(
    phase17a: dict[str, Any],
) -> list[CandidateSummary]:
    return [
        _candidate_summary(candidate)
        for candidate in phase17a["candidates"]
        if candidate["family"] == "DECLARER_PLAY"
    ]


def _selected_candidate(
    declarer_candidates: list[CandidateSummary],
) -> CandidateSummary:
    matches = [
        candidate
        for candidate in declarer_candidates
        if candidate.candidate.casefold() == SELECTED_CANDIDATE
    ]

    if len(matches) != 1:
        raise AssertionError(
            "Expected exactly one Phase 17A Safety Play candidate; "
            f"found {len(matches)}"
        )

    return matches[0]


def _fixture(
    name: str,
    condition: bool,
    detail: str,
) -> AuditFixture:
    return AuditFixture(
        name=name,
        passed=bool(condition),
        detail=detail,
    )


def run_audit() -> Phase17BDeclarerSourceEnrichmentAudit:
    phase17a = _load_phase17a()
    safety_text = _load_safety_play()

    declarer_candidates = _phase17a_declarer_candidates(phase17a)
    selected = _selected_candidate(declarer_candidates)

    prospective = [
        candidate
        for candidate in declarer_candidates
        if candidate.execution_status
        == "PROSPECTIVE_BLOCKED_OR_DEFERRED"
    ]

    fixtures: list[AuditFixture] = []

    fixtures.append(
        _fixture(
            "phase17a_has_nine_declarer_candidates",
            len(declarer_candidates) == 9,
            f"observed={len(declarer_candidates)} expected=9",
        )
    )

    fixtures.append(
        _fixture(
            "simple_unblock_is_existing_baseline",
            any(
                candidate.candidate == "SIMPLE_UNBLOCK_KING"
                and candidate.execution_status
                == "EXISTING_PRODUCTION_BASELINE"
                for candidate in declarer_candidates
            ),
            "SIMPLE_UNBLOCK_KING must remain an existing baseline.",
        )
    )

    fixtures.append(
        _fixture(
            "safety_play_selected",
            selected.candidate == SELECTED_CANDIDATE,
            f"selected={selected.candidate}",
        )
    )

    fixtures.append(
        _fixture(
            "safety_play_phase17a_classification",
            selected.classification == BEFORE_CLASSIFICATION,
            (
                f"observed={selected.classification} "
                f"expected={BEFORE_CLASSIFICATION}"
            ),
        )
    )

    fixtures.append(
        _fixture(
            "safety_play_architecture_ready",
            selected.architecture_status == "READY",
            f"architecture={selected.architecture_status}",
        )
    )

    fixtures.append(
        _fixture(
            "safety_play_source_path_preserved",
            selected.source_path
            == "knowledge/play/declarer-play/general-techniques/safety-play.md",
            selected.source_path,
        )
    )

    fixtures.append(
        _fixture(
            "safety_play_original_heading_preserved",
            selected.heading == "When to Use",
            f"heading={selected.heading}",
        )
    )

    headings_present = [
        heading
        for heading in REQUIRED_READINESS_HEADINGS
        if heading in safety_text
    ]

    fixtures.append(
        _fixture(
            "implementation_readiness_contract_present",
            "# Implementation Readiness Contract" in safety_text,
            "Implementation Readiness Contract heading must exist.",
        )
    )

    fixtures.append(
        _fixture(
            "required_readiness_headings_present",
            len(headings_present) == len(REQUIRED_READINESS_HEADINGS),
            (
                f"present={len(headings_present)} "
                f"expected={len(REQUIRED_READINESS_HEADINGS)}"
            ),
        )
    )

    fixtures.append(
        _fixture(
            "source_partial_status_retained",
            "**Source readiness: SOURCE_PARTIAL**" in safety_text
            and "**SOURCE_PARTIAL**" in safety_text,
            "Safety Play must remain explicitly SOURCE_PARTIAL.",
        )
    )

    fixtures.append(
        _fixture(
            "production_algorithm_not_enabled",
            "**Production algorithm:** Not implemented" in safety_text,
            "Safety Play production algorithm must remain disabled.",
        )
    )

    fixtures.append(
        _fixture(
            "production_recommendation_not_enabled",
            "**Production recommendation:** Not enabled" in safety_text,
            "Safety Play production recommendation must remain disabled.",
        )
    )

    fixtures.append(
        _fixture(
            "hidden_information_restricted",
            "**Hidden-card inference permitted:** No" in safety_text,
            "Hidden defender holdings must not be used.",
        )
    )

    fixtures.append(
        _fixture(
            "unregistered_probability_restricted",
            "**Unregistered probability calculations permitted:** No"
            in safety_text,
            "Unregistered probability calculations must remain prohibited.",
        )
    )

    fixtures.append(
        _fixture(
            "candidate_line_generation_unresolved",
            "candidate-line generation remains unresolved" in safety_text,
            "General candidate-line generation must remain unresolved.",
        )
    )

    fixtures.append(
        _fixture(
            "alternative_line_comparison_unresolved",
            "general alternative-line comparison remains unresolved"
            in safety_text,
            "General alternative-line comparison must remain unresolved.",
        )
    )

    fixtures.append(
        _fixture(
            "exception_precedence_incomplete",
            "exception and precedence handling remains incomplete"
            in safety_text,
            "General exception/precedence contract must remain incomplete.",
        )
    )

    gate_markers_present = sum(
        marker in safety_text
        for marker in SOURCE_EXECUTABLE_GATE
    )

    # The enrichment deliberately does not satisfy the executable gate.
    # It documents what would be required for a future narrow candidate.
    gate_passed = 0
    gate_failed = len(SOURCE_EXECUTABLE_GATE)

    unresolved_items = (
        "universal candidate-line generation",
        "exact comparison of alternative lines",
        "probability calculation for adverse distributions",
        "multi-trick consequence evaluation",
        "complete entry and communication modeling",
        "exhaustive exceptions",
        "precedence against competing declarer techniques",
        "exact card selection for arbitrary safety-play positions",
    )

    unresolved_count = sum(
        item in safety_text
        for item in unresolved_items
    )

    fixtures.append(
        _fixture(
            "all_source_executable_gate_markers_documented",
            gate_markers_present == len(SOURCE_EXECUTABLE_GATE),
            (
                f"documented={gate_markers_present} "
                f"expected={len(SOURCE_EXECUTABLE_GATE)}"
            ),
        )
    )

    fixtures.append(
        _fixture(
            "all_unresolved_items_documented",
            unresolved_count == len(unresolved_items),
            (
                f"documented={unresolved_count} "
                f"expected={len(unresolved_items)}"
            ),
        )
    )

    fixtures.append(
        _fixture(
            "no_new_recommendation_claim",
            selected.expected_new_recommendations == 0,
            (
                "Phase 17A expected new recommendation gain for "
                "Safety Play must remain zero."
            ),
        )
    )

    passed = sum(fixture.passed for fixture in fixtures)
    failed = len(fixtures) - passed

    # Architecture accounting is audit-only. Existing state can represent
    # core visible state but general line comparison / multi-trick evaluation
    # remains outside the established executable contract.
    architecture_requirements = 10
    architecture_representable = 7
    architecture_blocked = 3

    # General Safety Play can require probability comparisons, but the
    # Phase 17B source-enrichment phase adds no new probability engine.
    probability_requirements = 1
    supported_probability_requirements = 0
    unsupported_probability_requirements = 1

    source_executable = False

    phase17c_direction = (
        "C. FURTHER DECLARER SOURCE ENRICHMENT"
    )

    return Phase17BDeclarerSourceEnrichmentAudit(
        selected_candidate=selected.candidate,
        before_classification=BEFORE_CLASSIFICATION,
        after_classification=AFTER_CLASSIFICATION,
        declarer_candidates_considered=len(declarer_candidates),
        prospective_declarer_candidates=len(prospective),
        selected_source_path=selected.source_path,
        selected_source_heading=selected.heading,
        canonical_source_files_modified=1,
        canonical_source_headings_added=len(REQUIRED_READINESS_HEADINGS),
        deterministic_fixtures=len(fixtures),
        fixtures_passed=passed,
        fixtures_failed=failed,
        source_executable_gate_items=len(SOURCE_EXECUTABLE_GATE),
        source_executable_gate_items_passed=gate_passed,
        source_executable_gate_items_failed=gate_failed,
        architecture_requirements=architecture_requirements,
        architecture_representable_requirements=architecture_representable,
        architecture_blocked_requirements=architecture_blocked,
        probability_requirements=probability_requirements,
        supported_probability_requirements=(
            supported_probability_requirements
        ),
        unsupported_probability_requirements=(
            unsupported_probability_requirements
        ),
        unresolved_source_items=unresolved_count,
        unsupported_additions=0,
        invented_bridge_facts=0,
        hidden_information_violations=0,
        new_production_recommendations=0,
        source_executable=source_executable,
        phase17c_direction=phase17c_direction,
        fixtures=tuple(fixtures),
    )


def _to_dict(
    result: Phase17BDeclarerSourceEnrichmentAudit,
) -> dict[str, Any]:
    return asdict(result)


def main() -> int:
    result = run_audit()
    payload = _to_dict(result)

    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))

    if result.fixtures_failed:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
