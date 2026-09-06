from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SAFETY_PLAY_SOURCE = (
    REPO_ROOT.parent
    / "knowledge"
    / "play"
    / "declarer-play"
    / "general-techniques"
    / "safety-play.md"
)

PERCENTAGE_PLAYS_SOURCE = (
    REPO_ROOT.parent
    / "knowledge"
    / "play"
    / "declarer-play"
    / "probability"
    / "percentage-plays.md"
)

COMBINATION_COUNTS_SOURCE = (
    REPO_ROOT.parent
    / "knowledge"
    / "play"
    / "declarer-play"
    / "probability"
    / "combination-counts.md"
)


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class Phase17CAudit:
    phase: str
    selected_candidate: str
    classification_before: str
    classification_after: str
    source_executable: bool
    production_implementation_authorized: bool
    new_production_recommendations: int
    registered_probability_engines_required: tuple[str, ...]
    unregistered_probability_dependencies: tuple[str, ...]
    source_paths: tuple[str, ...]
    gate_results: tuple[GateResult, ...]
    blockers: tuple[str, ...]
    phase17d_direction: str


def _read_required(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required source not found: {path}")
    return path.read_text(encoding="utf-8")


def run_phase17c_safety_play_blocker_audit() -> Phase17CAudit:
    safety = _read_required(SAFETY_PLAY_SOURCE)
    percentage = _read_required(PERCENTAGE_PLAYS_SOURCE)
    combinations = _read_required(COMBINATION_COUNTS_SOURCE)

    safety_lower = safety.lower()
    percentage_lower = percentage.lower()
    combinations_lower = combinations.lower()

    source_partial_documented = "source_partial" in safety_lower
    precedence_incomplete = (
        "precedence" in safety_lower
        and "incomplete" in safety_lower
    )
    exact_legal_card_required = (
        "exact legal card" in safety_lower
        or "select an exact legal card" in safety_lower
    )
    posterior_dependency = "posterior probabilities" in percentage_lower
    vacant_places_dependency = "vacant places" in percentage_lower
    restricted_choice_dependency = "restricted choice" in percentage_lower
    combination_material_present = (
        "combination" in combinations_lower
        or "probability" in combinations_lower
    )

    gates = (
        GateResult(
            "exact_visible_holding",
            False,
            "No verified narrowly bounded Safety Play holding was found "
            "that independently defines a production trigger.",
        ),
        GateResult(
            "exact_contract_objective",
            False,
            "General Safety Play objectives are documented, but no single "
            "bounded position supplies a complete production objective.",
        ),
        GateResult(
            "exact_acting_hand_and_lead",
            False,
            "The reviewed material does not establish one complete bounded "
            "acting-hand/lead contract.",
        ),
        GateResult(
            "exact_legal_card",
            False,
            "The source requires an exact legal card for any future "
            "recommendation but does not supply one general Safety Play card.",
        ),
        GateResult(
            "adverse_layouts_bounded",
            False,
            "Combination-count material discusses layouts, but the reviewed "
            "Safety Play source does not bind them to one exact card action.",
        ),
        GateResult(
            "alternative_line_defined",
            False,
            "Competing lines are identified qualitatively rather than as one "
            "fully specified deterministic comparison.",
        ),
        GateResult(
            "comparison_criterion_complete",
            False,
            "The correct percentage play depends on current posterior "
            "probabilities and contextual objectives.",
        ),
        GateResult(
            "probability_contract_available",
            False,
            "Vacant Places and Restricted Choice may be required, while the "
            "needed production probability contracts are not registered here.",
        ),
        GateResult(
            "exceptions_and_precedence_complete",
            False,
            "The canonical Safety Play source explicitly leaves exception "
            "and precedence handling incomplete.",
        ),
        GateResult(
            "no_hidden_information_or_invention",
            True,
            "The audit requires visible information only and does not infer "
            "hidden cards or invent missing bridge rules.",
        ),
    )

    blockers = (
        "No verified exact holding-to-card Safety Play contract.",
        "Exception and precedence handling remains incomplete.",
        "Alternative-line selection may require conditional probability.",
        "Percentage-play source requires current posterior probabilities.",
        "Vacant Places may be required.",
        "Restricted Choice may be required.",
        "Combination counts alone do not select an exact legal card.",
    )

    assert source_partial_documented
    assert precedence_incomplete
    assert exact_legal_card_required
    assert posterior_dependency
    assert vacant_places_dependency
    assert restricted_choice_dependency
    assert combination_material_present

    return Phase17CAudit(
        phase="17C",
        selected_candidate="NARROW_SAFETY_PLAY_POSITION",
        classification_before="SOURCE_PARTIAL",
        classification_after="SOURCE_PARTIAL",
        source_executable=False,
        production_implementation_authorized=False,
        new_production_recommendations=0,
        registered_probability_engines_required=("KNOWN_CARD_COUNT",),
        unregistered_probability_dependencies=(
            "VACANT_PLACES",
            "RESTRICTED_CHOICE",
            "CONDITIONAL_PERCENTAGE_PLAY",
        ),
        source_paths=(
            "knowledge/play/declarer-play/general-techniques/safety-play.md",
            "knowledge/play/declarer-play/probability/percentage-plays.md",
            "knowledge/play/declarer-play/probability/combination-counts.md",
        ),
        gate_results=gates,
        blockers=blockers,
        phase17d_direction="PROBABILITY_SOURCE_ENRICHMENT",
    )


def main() -> None:
    audit = run_phase17c_safety_play_blocker_audit()
    print(json.dumps(asdict(audit), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
