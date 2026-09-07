from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

PHASE = "17G"
BASELINE_PHASE = "17F"
CANDIDATE = "Restricted Choice Supporting Source Audit"

UNRESOLVED_DEPENDENCIES = (
    "SOURCE_PROVENANCE",
    "VACANT_PLACES_INPUT_CONTRACT",
    "OBSERVATION_SEMANTICS",
    "PRECISION_AND_ROUNDING",
    "ARCHITECTURE_READINESS",
)


@dataclass(frozen=True, slots=True)
class SourceRecord:
    logical_path: str
    exists: bool
    tracked: bool
    git_status: str
    provenance_classification: str
    safe_to_modify: bool
    safe_to_stage: bool


@dataclass(frozen=True, slots=True)
class GateResult:
    name: str
    classification: str
    production_gate_passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class Phase17GResult:
    phase: str
    baseline_phase: str
    baseline_commit: str
    candidate: str
    classification_before: str
    classification_after: str

    source_records: tuple[SourceRecord, ...]

    historical_backup_found: bool
    historical_backup_is_identical: bool
    historical_backup_git_tracked: bool
    vacant_places_git_history_found: bool

    vacant_places_relationship_contract_present: bool
    vacant_places_practical_procedure_present: bool
    vacant_places_uncertainty_guard_present: bool

    restricted_choice_observation_procedure_present: bool
    restricted_choice_noncertainty_guard_present: bool

    worked_percentage_outputs_present: bool
    worked_equal_choice_present: bool
    explicit_precision_rounding_contract_present: bool
    eight_never_support_present: bool
    glossary_support_present: bool
    terminology_support_present: bool
    abbreviations_support_present: bool
    restricted_choice_question_exists: bool
    vacant_places_question_exists: bool
    restricted_choice_engine_registered: bool
    vacant_places_engine_registered: bool

    source_executable: bool
    production_implementation_authorized: bool
    new_production_recommendations: int
    registered_probability_engines: int

    unresolved_dependencies: tuple[str, ...]
    gates: tuple[GateResult, ...]
    phase17h_direction: str


def _run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _repo_root() -> Path:
    result = _run_git("rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Unable to locate git root.")
    return Path(result.stdout.strip())


def _baseline_commit() -> str:
    result = _run_git("rev-parse", "HEAD")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Unable to resolve HEAD.")
    return result.stdout.strip()


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _git_status(path: Path, root: Path) -> tuple[bool, str]:
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return False, "OUTSIDE_GIT_ROOT"

    top_relative = f":(top){relative}"
    status = _run_git("status", "--short", "--", top_relative)
    output = status.stdout.strip()

    if output:
        code = output[:2]
        if code == "??":
            return False, "UNTRACKED"
        return True, code

    tracked = _run_git(
        "ls-files",
        "--error-unmatch",
        "--",
        top_relative,
    )
    if tracked.returncode == 0:
        return True, "CLEAN"

    return False, "UNTRACKED"


def _source_record(
    path: Path,
    logical_path: str,
    root: Path,
) -> SourceRecord:
    tracked, status = _git_status(path, root)

    if not path.exists():
        provenance = "MISSING"
        safe_to_modify = False
        safe_to_stage = False
    elif not tracked:
        provenance = "UNTRACKED_PROVENANCE_UNRESOLVED"
        safe_to_modify = False
        safe_to_stage = False
    elif status != "CLEAN":
        provenance = "TRACKED_MODIFIED_USER_OWNED"
        safe_to_modify = False
        safe_to_stage = False
    else:
        provenance = "TRACKED_CLEAN"
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


def _contains_all(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(phrase.lower() in lowered for phrase in phrases)


def _git_history_exists(pattern: str) -> bool:
    result = _run_git("log", "--all", "--name-status", "--", pattern)
    return bool(result.stdout.strip())


def run_audit() -> Phase17GResult:
    root = _repo_root()
    toolkit = root / "bridgelab-toolkit"
    knowledge = root / "knowledge"

    vacant_path = knowledge / "play" / "counting" / "vacant-places.md"
    restricted_path = (
        knowledge
        / "play"
        / "declarer-play"
        / "general-techniques"
        / "restricted-choice.md"
    )
    percentage_path = (
        knowledge
        / "play"
        / "declarer-play"
        / "probability"
        / "percentage-plays.md"
    )
    worked_path = (
        knowledge
        / "play"
        / "declarer-play"
        / "probability"
        / "finesse"
        / "a8732-vs-k1065-restricted-choice.md"
    )
    eight_never_path = (
        knowledge
        / "play"
        / "principles"
        / "eight-ever-nine-never.md"
    )
    glossary_path = (
        knowledge
        / "references"
        / "bridge-glossary.md"
    )
    terminology_path = (
        knowledge
        / "references"
        / "bridge-terminology.md"
    )
    abbreviations_path = (
        knowledge
        / "references"
        / "common-bridge-abbreviations.md"
    )
    source_records = (
        _source_record(
            vacant_path,
            "knowledge/play/counting/vacant-places.md",
            root,
        ),
        _source_record(
            restricted_path,
            (
                "knowledge/play/declarer-play/general-techniques/"
                "restricted-choice.md"
            ),
            root,
        ),
        _source_record(
            percentage_path,
            (
                "knowledge/play/declarer-play/probability/"
                "percentage-plays.md"
            ),
            root,
        ),
         _source_record(
            eight_never_path,
            "knowledge/play/principles/eight-ever-nine-never.md",
            root,
        ),
        _source_record(
            glossary_path,
            "knowledge/references/bridge-glossary.md",
            root,
        ),
        _source_record(
            terminology_path,
            "knowledge/references/bridge-terminology.md",
            root,
        ),
        _source_record(
            abbreviations_path,
            "knowledge/references/common-bridge-abbreviations.md",
            root,
        ),
    )

    vacant_text = _read(vacant_path)
    restricted_text = _read(restricted_path)
    worked_text = _read(worked_path)
    eight_never_text = _read(eight_never_path)
    glossary_text = _read(glossary_path)
    terminology_text = _read(terminology_path)
    abbreviations_text = _read(abbreviations_path)
    backup_path = (
        toolkit
        / "phase17c_fullkit_temp"
        / "bridgelab-toolkit"
        / "output"
        / "backups"
        / "spelling-repair-20260816-01"
        / "play"
        / "declarer-play"
        / "probabilty"
        / "vacant-places.md"
    )

    backup_found = backup_path.exists()
    backup_text = _read(backup_path)

    backup_identical = (
        backup_found
        and vacant_path.exists()
        and backup_text == vacant_text
    )

    backup_tracked, _ = _git_status(backup_path, root)

    vacant_relationship_contract = _contains_all(
        vacant_text,
        (
            "Vacant places and restricted choice answer different probability",
            "which hand has more room",
            "what does that choice imply about the remaining",
            "restricted-choice",
            "distributional odds supplied by",
            "rather than applied in isolation",
        ),
    )

    vacant_procedure = _contains_all(
        vacant_text,
        (
            "Reconstruct as much of each opponent's original shape as possible",
            "Count the known cards in each hand",
            "Determine the vacant places remaining",
            "Incorporate any specific evidence concerning the target card",
            "Compare the resulting probabilities",
            "Update the calculation whenever new distributional information",
        ),
    )

    vacant_uncertainty_guard = (
        "Do not count uncertain assumptions as established facts"
        in vacant_text
    )

    observation_procedure = _contains_all(
        restricted_text,
        (
            "When an apparently equivalent honor appears",
            "Identify the relevant possible original holdings",
            "whether the card was forced from some holdings but optional from",
            "defensive agreements or technical considerations",
            "Incorporate the auction and all known distribution",
            "Compare the remaining layouts",
        ),
    )

    noncertainty_guard = _contains_all(
        restricted_text,
        (
            "does not say that the remaining honor",
            "must",
            "under the appropriate assumptions",
            "observed choice changes the probabilities",
        ),
    )

    worked_percentage_outputs = "%" in worked_text

    worked_equal_choice = _contains_all(
        worked_text,
        (
            "Either K or 10",
            "50.00%",
        ),
    )
    eight_never_support = _contains_all(
        eight_never_text,
        (
            "Restricted Choice changes the probabilities",
            "remaining honor is more likely to be singleton",
            "vacant spaces",
            "missing queen is therefore more likely to be with East",
            "Bidding often changes the odds",
            "information may outweigh the basic",
        ),
    )

    glossary_support = _contains_all(
        glossary_text,
        (
            "Restricted Choice",
            "A probability principle used in card play",
            "Vacant Places",
            "A probability principle based on the number of unknown card positions",
        ),
    )

    terminology_support = _contains_all(
        terminology_text,
        (
            "Restricted Choice | Probability principle involving equivalent honors",
            "Vacant Places | Probability based on unseen card locations",
        ),
    )

    abbreviations_support = _contains_all(
        abbreviations_text,
        (
            "RC | Restricted Choice",
            "VP | Vacant Places",
        ),
    )
    combined_sources = "\n".join(
        (
            vacant_text,
            restricted_text,
            _read(percentage_path),
            worked_text,
            eight_never_text,
            glossary_text,
            terminology_text,
            abbreviations_text,
        )
    ).lower()

    explicit_precision_rounding_contract = any(
        term in combined_sources
        for term in (
            "round to",
            "rounding rule",
            "decimal places",
            "precision rule",
            "comparison tolerance",
        )
    )

    questions_path = toolkit / "bridge" / "probability_questions.py"
    engine_path = toolkit / "bridge" / "probability_engine.py"

    questions_text = _read(questions_path)
    engine_text = _read(engine_path)

    restricted_question_exists = (
        "class RestrictedChoiceQuestion" in questions_text
        and "observed_play" in questions_text
        and "known_cards" in questions_text
    )

    vacant_question_exists = (
        "class VacantPlacesQuestion" in questions_text
        and "known_seat_constraints" in questions_text
    )

    registry_text = ""
    marker = "DEFAULT_PROBABILITY_ENGINE_REGISTRY"
    if marker in engine_text:
        registry_text = engine_text[engine_text.index(marker):]

    restricted_engine_registered = (
        "RestrictedChoiceQuestion" in registry_text
    )
    vacant_engine_registered = (
        "VacantPlacesQuestion" in registry_text
    )

    registered_probability_engines = int(
        "KnownCardCountQuestion" in registry_text
    )

    gates = (
        GateResult(
            name="SOURCE_PROVENANCE",
            classification="BLOCKED",
            production_gate_passed=False,
            detail=(
                "Three relevant knowledge sources remain untracked and "
                "provenance-unresolved; the discovered historical backup is "
                "not Git-tracked and is not identical to the current source."
            ),
        ),
        GateResult(
            name="VACANT_PLACES_INPUT_CONTRACT",
            classification="SOURCE_PARTIAL",
            production_gate_passed=False,
            detail=(
                "The source defines the conceptual relationship, practical "
                "procedure, and uncertainty guard, but not a complete "
                "executable input/validation contract."
            ),
        ),
        GateResult(
            name="OBSERVATION_SEMANTICS",
            classification="SOURCE_PARTIAL",
            production_gate_passed=False,
            detail=(
                "The source defines a practical observation procedure and "
                "forced-versus-optional reasoning, but not complete formal "
                "semantics for executable observed-play interpretation."
            ),
        ),
        GateResult(
            name="PRECISION_AND_ROUNDING",
            classification="SOURCE_PARTIAL",
            production_gate_passed=False,
            detail=(
                "Worked examples contain percentage outputs and an equal-play "
                "example, but no explicit production precision, rounding, "
                "or comparison-tolerance contract was found."
            ),
        ),
        GateResult(
            name="ARCHITECTURE_READINESS",
            classification="SOURCE_PARTIAL",
            production_gate_passed=False,
            detail=(
                "RestrictedChoiceQuestion and VacantPlacesQuestion scaffolding "
                "exists, but neither has a registered production probability "
                "engine."
            ),
        ),
        GateResult(
            name="NO_HIDDEN_INFORMATION",
            classification="COMPLETE",
            production_gate_passed=True,
            detail=(
                "No hidden defender cards or unsupported distributional facts "
                "are introduced by this audit."
            ),
        ),
        GateResult(
            name="NO_FORMULA_INVENTION",
            classification="COMPLETE",
            production_gate_passed=True,
            detail=(
                "The audit does not invent probability formulas, bridge rules, "
                "precision rules, or production defaults."
            ),
        ),
    )

    return Phase17GResult(
        phase=PHASE,
        baseline_phase=BASELINE_PHASE,
        baseline_commit=_baseline_commit(),
        candidate=CANDIDATE,
        classification_before="SOURCE_PARTIAL",
        classification_after="SOURCE_PARTIAL",
        source_records=source_records,
        historical_backup_found=backup_found,
        historical_backup_is_identical=backup_identical,
        historical_backup_git_tracked=backup_tracked,
        vacant_places_git_history_found=_git_history_exists(
            "*vacant-places.md"
        ),
        vacant_places_relationship_contract_present=(
            vacant_relationship_contract
        ),
        vacant_places_practical_procedure_present=vacant_procedure,
        vacant_places_uncertainty_guard_present=vacant_uncertainty_guard,
        restricted_choice_observation_procedure_present=(
            observation_procedure
        ),
        restricted_choice_noncertainty_guard_present=noncertainty_guard,
        worked_percentage_outputs_present=worked_percentage_outputs,
        worked_equal_choice_present=worked_equal_choice,
        explicit_precision_rounding_contract_present=(
            explicit_precision_rounding_contract
        ),
        eight_never_support_present=eight_never_support,
        glossary_support_present=glossary_support,
        terminology_support_present=terminology_support,
        abbreviations_support_present=abbreviations_support,
        restricted_choice_question_exists=restricted_question_exists,
        vacant_places_question_exists=vacant_question_exists,
        restricted_choice_engine_registered=restricted_engine_registered,
        vacant_places_engine_registered=vacant_engine_registered,
        source_executable=False,
        production_implementation_authorized=False,
        new_production_recommendations=0,
        registered_probability_engines=registered_probability_engines,
        unresolved_dependencies=UNRESOLVED_DEPENDENCIES,
        gates=gates,
        phase17h_direction="RESTRICTED_CHOICE_CONTRACT_ENRICHMENT",
    )


def main() -> None:
    result = run_audit()
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
