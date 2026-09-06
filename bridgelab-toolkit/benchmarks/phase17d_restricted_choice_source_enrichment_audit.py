from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGELAB_ROOT = REPO_ROOT.parent

PERCENTAGE_PLAYS = (
    BRIDGELAB_ROOT
    / "knowledge"
    / "play"
    / "declarer-play"
    / "probability"
    / "percentage-plays.md"
)

VACANT_PLACES = (
    BRIDGELAB_ROOT
    / "knowledge"
    / "play"
    / "counting"
    / "vacant-places.md"
)

RESTRICTED_CHOICE_GENERAL = (
    BRIDGELAB_ROOT
    / "knowledge"
    / "play"
    / "declarer-play"
    / "general-techniques"
    / "restricted-choice.md"
)

RESTRICTED_CHOICE_WORKED = (
    BRIDGELAB_ROOT
    / "knowledge"
    / "play"
    / "declarer-play"
    / "probability"
    / "finesse"
    / "a8732-vs-k1065-restricted-choice.md"
)


@dataclass(frozen=True)
class SourceRecord:
    logical_path: str
    exists: bool
    tracked: bool
    git_status: str
    provenance_classification: str
    safe_to_modify: bool
    safe_to_stage: bool


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class Phase17DResult:
    phase: str
    candidate: str
    source_records: tuple[SourceRecord, ...]
    formula_present_in_worked_source: bool
    worked_source_contains_exact_action_rule: bool
    source_executable: bool
    production_implementation_authorized: bool
    new_production_recommendations: int
    registered_probability_engines: int
    unresolved_dependencies: tuple[str, ...]
    gate_results: tuple[GateResult, ...]
    phase17e_direction: str


def _git_status(path: Path) -> tuple[bool, str]:
    import subprocess

    completed = subprocess.run(
        [
            "git",
            "status",
            "--short",
            "--",
            str(path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    raw = completed.stdout.strip()

    if not raw:
        return True, "CLEAN_TRACKED_OR_UNCHANGED"

    status = raw[:2].strip()

    if status == "??":
        return False, "UNTRACKED"

    return True, status


def _source_record(
    path: Path,
    logical_path: str,
) -> SourceRecord:
    tracked, status = _git_status(path)

    if not path.exists():
        provenance = "MISSING"
        safe_to_modify = False
        safe_to_stage = False

    elif status == "UNTRACKED":
        provenance = "UNTRACKED_PROVENANCE_UNRESOLVED"
        safe_to_modify = False
        safe_to_stage = False

    elif status == "M":
        provenance = "TRACKED_MODIFIED_USER_OWNED"
        safe_to_modify = False
        safe_to_stage = False

    else:
        provenance = "TRACKED_CANONICAL"
        safe_to_modify = True
        safe_to_stage = True

    return SourceRecord(
        logical_path=logical_path,
        exists=path.exists(),
        tracked=tracked,
        git_status=status,
        provenance_classification=provenance,
        safe_to_modify=safe_to_modify,
        safe_to_stage=safe_to_stage,
    )


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)

    return path.read_text(encoding="utf-8")


def run_phase17d_restricted_choice_source_enrichment_audit() -> Phase17DResult:
    records = (
        _source_record(
            PERCENTAGE_PLAYS,
            "knowledge/play/declarer-play/probability/percentage-plays.md",
        ),
        _source_record(
            VACANT_PLACES,
            "knowledge/play/counting/vacant-places.md",
        ),
        _source_record(
            RESTRICTED_CHOICE_GENERAL,
            "knowledge/play/declarer-play/general-techniques/restricted-choice.md",
        ),
        _source_record(
            RESTRICTED_CHOICE_WORKED,
            (
                "knowledge/play/declarer-play/probability/finesse/"
                "a8732-vs-k1065-restricted-choice.md"
            ),
        ),
    )

    percentage = _read(PERCENTAGE_PLAYS)
    worked = _read(RESTRICTED_CHOICE_WORKED)

    formula_present = (
        "P(Q West | J played)" in worked
        and "P(Q East | J played)" in worked
        and "W / (W + E/2)" in worked
        and "(E/2) / (W + E/2)" in worked
    )

    exact_action_rule = (
        "Q more likely West" in worked
        and "play 10" in worked
        and "Q more likely East" in worked
        and "play K" in worked
    )

    posterior_dependency = (
        "posterior probabilities" in percentage.lower()
    )

    protected_sources_present = any(
        not record.safe_to_stage
        for record in records
    )

    gates = (
        GateResult(
            "worked_formula_present",
            formula_present,
            "Worked source contains the explicit bounded equations.",
        ),
        GateResult(
            "worked_action_rule_present",
            exact_action_rule,
            "Worked source contains a bounded subsequent-card rule.",
        ),
        GateResult(
            "posterior_dependency_documented",
            posterior_dependency,
            "Percentage-play source requires current posterior probabilities.",
        ),
        GateResult(
            "source_provenance_resolved",
            not protected_sources_present,
            "All required source files must have resolved provenance.",
        ),
        GateResult(
            "vacant_places_contract_complete",
            False,
            "Vacant Places input semantics are not yet established as a "
            "production contract.",
        ),
        GateResult(
            "observation_semantics_complete",
            False,
            "Observed-card and forced-choice boundaries are not yet fully "
            "specified for production.",
        ),
        GateResult(
            "precision_contract_complete",
            False,
            "Exact output precision and rounding contract remain unresolved.",
        ),
        GateResult(
            "architecture_proven_ready",
            False,
            "Architecture readiness has not yet been proven for every required "
            "Restricted Choice input.",
        ),
        GateResult(
            "no_hidden_information",
            True,
            "Audit uses source-visible / observed facts only.",
        ),
        GateResult(
            "no_formula_invention",
            True,
            "No new probability formula is introduced.",
        ),
    )

    source_executable = all(
        gate.passed
        for gate in gates
    )

    # Provenance is currently unresolved for required source material.
    # Therefore implementation must not be authorized in Phase 17D.
    production_authorized = False

    if source_executable:
        phase17e = "IMPLEMENT_RESTRICTED_CHOICE_PROBABILITY_ENGINE"
    elif protected_sources_present:
        phase17e = "FURTHER_RESTRICTED_CHOICE_SOURCE_ENRICHMENT"
    else:
        phase17e = "VACANT_PLACES_SOURCE_ENRICHMENT"

    return Phase17DResult(
        phase="17D",
        candidate="RESTRICTED_CHOICE",
        source_records=records,
        formula_present_in_worked_source=formula_present,
        worked_source_contains_exact_action_rule=exact_action_rule,
        source_executable=source_executable,
        production_implementation_authorized=production_authorized,
        new_production_recommendations=0,
        registered_probability_engines=1,
        unresolved_dependencies=(
            "SOURCE_PROVENANCE",
            "VACANT_PLACES_INPUT_CONTRACT",
            "OBSERVATION_SEMANTICS",
            "PRECISION_AND_ROUNDING",
            "ARCHITECTURE_READINESS",
        ),
        gate_results=gates,
        phase17e_direction=phase17e,
    )


def main() -> None:
    result = run_phase17d_restricted_choice_source_enrichment_audit()
    print(
        json.dumps(
            asdict(result),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()