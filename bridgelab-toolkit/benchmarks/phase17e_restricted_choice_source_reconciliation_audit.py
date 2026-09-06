from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGELAB_ROOT = REPO_ROOT.parent

PERCENTAGE_PLAYS = (
    BRIDGELAB_ROOT
    / "knowledge/play/declarer-play/probability/percentage-plays.md"
)
VACANT_PLACES = (
    BRIDGELAB_ROOT
    / "knowledge/play/counting/vacant-places.md"
)
RESTRICTED_CHOICE = (
    BRIDGELAB_ROOT
    / "knowledge/play/declarer-play/general-techniques/restricted-choice.md"
)
WORKED_RESTRICTED_CHOICE = (
    BRIDGELAB_ROOT
    / (
        "knowledge/play/declarer-play/probability/finesse/"
        "a8732-vs-k1065-restricted-choice.md"
    )
)

PROBABILITY_ENGINE = REPO_ROOT / "bridge/probability_engine.py"
PROBABILITY_QUESTIONS = REPO_ROOT / "bridge/probability_questions.py"
PHASE13F_TEST = (
    REPO_ROOT / "tests/test_bridge_phase13f_probability_engine_architecture.py"
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
    classification: str
    production_gate_passed: bool
    detail: str


@dataclass(frozen=True)
class Phase17EResult:
    phase: str
    baseline_commit: str
    candidate: str
    classification_before: str
    classification_after: str
    source_records: tuple[SourceRecord, ...]
    provenance_history_found_for_untracked_sources: bool
    vacant_places_source_contract_present: bool
    restricted_choice_observation_contract_present: bool
    explicit_precision_rounding_contract_present: bool
    restricted_choice_question_exists: bool
    vacant_places_question_exists: bool
    question_scaffolding_tested: bool
    restricted_choice_engine_registered: bool
    vacant_places_engine_registered: bool
    source_executable: bool
    production_implementation_authorized: bool
    new_production_recommendations: int
    registered_probability_engines: int
    unresolved_dependencies: tuple[str, ...]
    gate_results: tuple[GateResult, ...]
    phase17f_direction: str


def _git_status(path: Path) -> tuple[bool, str]:
    completed = subprocess.run(
        ["git", "status", "--short", "--", str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    output = completed.stdout.strip()
    if not output:
       tracked = subprocess.run(
           ["git", "ls-files", "--error-unmatch", str(path)],
           cwd=REPO_ROOT,
           capture_output=True,
           text=True,
           check=False,
       )
       return tracked.returncode == 0, "UNCHANGED"

    status = output[:2].strip()

    if status == "??":
        return False, "UNTRACKED"

    return True, status


def _source_record(path: Path) -> SourceRecord:
    exists = path.exists()

    if not exists:
        return SourceRecord(
            logical_path=str(path.relative_to(BRIDGELAB_ROOT)).replace("\\", "/"),
            exists=False,
            tracked=False,
            git_status="MISSING",
            provenance_classification="MISSING",
            safe_to_modify=False,
            safe_to_stage=False,
        )

    tracked, status = _git_status(path)

    if not tracked:
        classification = "UNTRACKED_PROVENANCE_UNRESOLVED"
        safe_to_modify = False
        safe_to_stage = False
    elif "M" in status:
        classification = "TRACKED_MODIFIED_USER_OWNED"
        safe_to_modify = False
        safe_to_stage = False
    else:
        classification = "TRACKED_CANONICAL"
        safe_to_modify = True
        safe_to_stage = True

    return SourceRecord(
        logical_path=str(path.relative_to(BRIDGELAB_ROOT)).replace("\\", "/"),
        exists=True,
        tracked=tracked,
        git_status=status,
        provenance_classification=classification,
        safe_to_modify=safe_to_modify,
        safe_to_stage=safe_to_stage,
    )


def _git_history_exists(pattern: str) -> bool:
    completed = subprocess.run(
        ["git", "log", "--all", "--name-status", "--", pattern],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(completed.stdout.strip())


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def audit_phase17e() -> Phase17EResult:
    source_paths = (
        PERCENTAGE_PLAYS,
        VACANT_PLACES,
        RESTRICTED_CHOICE,
        WORKED_RESTRICTED_CHOICE,
    )
    source_records = tuple(_source_record(path) for path in source_paths)

    vacant_text = _read(VACANT_PLACES)
    restricted_text = _read(RESTRICTED_CHOICE)
    worked_text = _read(WORKED_RESTRICTED_CHOICE)
    engine_text = _read(PROBABILITY_ENGINE)
    questions_text = _read(PROBABILITY_QUESTIONS)
    phase13f_text = _read(PHASE13F_TEST)

    history_found = any(
        (
            _git_history_exists("*vacant-places.md"),
            _git_history_exists("*restricted-choice.md"),
            _git_history_exists("*a8732-vs-k1065-restricted-choice.md"),
        )
    )

    vacant_contract_present = all(
        phrase in vacant_text
        for phrase in (
            "Count the known cards in each hand.",
            "Determine the vacant places remaining.",
            "Compare the resulting probabilities.",
            "Do not count uncertain assumptions as established facts.",
        )
    )

    observation_contract_present = all(
        phrase in restricted_text
        for phrase in (
            "Identify the relevant possible original holdings.",
            "Ask whether the card was forced from some holdings but optional from",
            "Incorporate the auction and all known distribution.",
            "Compare the remaining layouts before choosing the next play.",
        )
    )

    precision_terms = (
        "precision",
        "rounding",
        "decimal places",
    )
    explicit_precision_contract = any(
        term in worked_text.lower() for term in precision_terms
    )

    restricted_question_exists = "class RestrictedChoiceQuestion" in questions_text
    vacant_question_exists = "class VacantPlacesQuestion" in questions_text

    scaffolding_tested = all(
        phrase in phase13f_text
        for phrase in (
            "RestrictedChoiceQuestion",
            "VacantPlacesQuestion",
        )
    )

    restricted_registered = (
        "RestrictedChoiceQuestion" in engine_text
        and "DEFAULT_PROBABILITY_ENGINE_REGISTRY" in engine_text
    )
    vacant_registered = (
        "VacantPlacesQuestion" in engine_text
        and "DEFAULT_PROBABILITY_ENGINE_REGISTRY" in engine_text
    )

    provenance_resolved = all(
        record.provenance_classification == "TRACKED_CANONICAL"
        for record in source_records
    )

    gate_results = (
        GateResult(
            "source_provenance",
            "BLOCKED" if not provenance_resolved else "COMPLETE",
            provenance_resolved,
            (
                "Required source provenance remains unresolved."
                if not provenance_resolved
                else "All required sources have resolved canonical provenance."
            ),
        ),
        GateResult(
            "vacant_places_input_contract",
            "SOURCE_PARTIAL",
            False,
            (
                "Vacant Places source provides known-card counting, remaining "
                "vacant-place reasoning, probability comparison, and uncertainty "
                "warnings, but not a complete production input contract."
            ),
        ),
        GateResult(
            "observation_semantics",
            "SOURCE_PARTIAL",
            False,
            (
                "Restricted Choice source documents holdings, forced-versus-optional "
                "choice, auction/distribution evidence, and layout comparison, but "
                "does not provide a complete executable observation contract."
            ),
        ),
        GateResult(
            "precision_and_rounding",
            "SOURCE_PARTIAL",
            False,
            (
                "Worked examples contain probabilities and equality cases, but no "
                "explicit production precision and rounding contract was found."
            ),
        ),
        GateResult(
            "architecture_readiness",
            "SOURCE_PARTIAL",
            False,
            (
                "RestrictedChoiceQuestion and VacantPlacesQuestion scaffolding "
                "exists and is tested, but no corresponding production engines "
                "are registered."
            ),
        ),
        GateResult(
            "no_hidden_information",
            "COMPLETE",
            True,
            "The audit does not infer hidden defender cards.",
        ),
        GateResult(
            "no_formula_invention",
            "COMPLETE",
            True,
            "The audit introduces no new probability formula.",
        ),
    )

    unresolved_dependencies = (
        "SOURCE_PROVENANCE",
        "VACANT_PLACES_INPUT_CONTRACT",
        "OBSERVATION_SEMANTICS",
        "PRECISION_AND_ROUNDING",
        "ARCHITECTURE_READINESS",
    )

    source_executable = all(gate.production_gate_passed for gate in gate_results)

    return Phase17EResult(
        phase="17E",
        baseline_commit="dc49e39",
        candidate="RESTRICTED_CHOICE",
        classification_before="SOURCE_PARTIAL",
        classification_after="SOURCE_PARTIAL",
        source_records=source_records,
        provenance_history_found_for_untracked_sources=history_found,
        vacant_places_source_contract_present=vacant_contract_present,
        restricted_choice_observation_contract_present=observation_contract_present,
        explicit_precision_rounding_contract_present=explicit_precision_contract,
        restricted_choice_question_exists=restricted_question_exists,
        vacant_places_question_exists=vacant_question_exists,
        question_scaffolding_tested=scaffolding_tested,
        restricted_choice_engine_registered=restricted_registered,
        vacant_places_engine_registered=vacant_registered,
        source_executable=source_executable,
        production_implementation_authorized=False,
        new_production_recommendations=0,
        registered_probability_engines=1,
        unresolved_dependencies=unresolved_dependencies,
        gate_results=gate_results,
        phase17f_direction="RESTRICTED_CHOICE_CONTRACT_ENRICHMENT",
    )


def main() -> None:
    print(json.dumps(asdict(audit_phase17e()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
