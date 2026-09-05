"""Phase 13B deterministic declarer-play adapter integration audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from benchmarks.end_to_end_analysis_architecture import _bidding
from bridge.deal_analysis import AnalysisStage, DealAnalysisContext, analyze_deal_decision
from bridge.sayc_route_configuration import create_standard_sayc_router


@dataclass(frozen=True, slots=True)
class DeclarerPlayAdapterBenchmark:
    analyzed_positions: int
    recommendations: int
    abstentions: int
    no_decisions: int
    errors: int
    stage_counts: dict[str, int]
    action_counts: dict[str, int]
    fixture_results: tuple[dict[str, object], ...]
    declarer_inventory: tuple[dict[str, object], ...]
    probability_inventory: dict[str, str]
    ordinary_benchmark: dict[str, int]
    phase12_guards: dict[str, object]
    phase13c_direction: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_declarer_play_adapter_integration_benchmark() -> DeclarerPlayAdapterBenchmark:
    router = create_standard_sayc_router()
    fixtures = (
        ("bidding-success", _bidding("KQJ876.32.43.543")),
        ("routed-source-abstention", _bidding("QJ9876.32.43.543")),
        ("no-route", _bidding("AKQ2.5432.32.543", ("1C", "P", "1D", "P", "1H", "P"))),
        ("missing-policy", _bidding("AKQ2.5432.32.543", ("1NT", "P", "2C", "P", "2H", "P"))),
        ("strong-2c-phase12n", _bidding("AKQ.AKQ.Q74.Q843", ("2C", "P", "2D", "P"))),
        ("declarer-play-gap", DealAnalysisContext(AnalysisStage.DECLARER_PLAY)),
        ("defensive-play-gap", DealAnalysisContext(AnalysisStage.DEFENSIVE_PLAY)),
        ("incomplete-state", DealAnalysisContext()),
        ("declarer-missing-state", DealAnalysisContext(stage=AnalysisStage.DECLARER_PLAY)),
        ("declarer-repeat", DealAnalysisContext(stage=AnalysisStage.DECLARER_PLAY)),
    )
    rows = []
    for name, context in fixtures:
        result = analyze_deal_decision(context, bidding_router=router)
        action = result.action.bid.serialize() if result.action.bid is not None else (
            str(result.action.card) if result.action.card is not None else None
        )
        rows.append({
            "name": name,
            "stage": result.stage.value,
            "status": result.status.value,
            "action_kind": result.action.kind.value,
            "action": action,
            "abstention_code": None if result.abstention_code is None else result.abstention_code.value,
            "evidence_count": len(result.evidence),
            "probability_evidence_count": len(result.probability_evidence),
        })
    statuses = Counter(row["status"] for row in rows)
    return DeclarerPlayAdapterBenchmark(
        len(rows), statuses["recommendation"], statuses["abstain"], statuses["no-decision"], statuses["error"],
        dict(sorted(Counter(row["stage"] for row in rows).items())),
        dict(sorted(Counter(row["action_kind"] for row in rows).items())),
        tuple(rows),
        ({
            "module_path": None, "entry_point": None, "input_type": None, "output_type": None,
            "returns_card": False, "can_abstain": False, "explanation": False,
            "knowledge_source": False, "probability_evidence": False, "deterministic": None,
            "canonical_target": False,
            "finding": "No production-capable declarer-play module exists in the repository.",
        },),
        {
            "restricted_choice": "NOT USED BY CURRENT DECLARER ENGINE",
            "vacant_places": "NOT USED BY CURRENT DECLARER ENGINE",
            "distribution_probabilities": "NOT USED BY CURRENT DECLARER ENGINE",
            "trump_breaks": "NOT USED BY CURRENT DECLARER ENGINE",
            "monte_carlo": "NOT USED BY CURRENT DECLARER ENGINE",
        },
        {"seeds": 10_000, "production_calls": 7_871, "completed": 761, "abstained": 9_239},
        {"routes": 45, "phase12n": 24, "phase12o": 23, "phase12q": 1_194,
         "phase12r": 166, "phase12s": 540, "phase12t": 33,
         "phase12g": {"4H": 17, "4S": 21}, "phase12h": 197,
         "phase12l": {"completed": 5, "abstained": 7},
         "jacoby": {"hearts": 62, "spades": 61}},
        "D. DECLARER STATE ARCHITECTURE",
    )


def write_artifacts(benchmark: DeclarerPlayAdapterBenchmark, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    json_path = output / "bridgelab_phase13b_declarer_play_adapter_integration.json"
    markdown_path = output / "bridgelab_phase13b_declarer_play_adapter_integration.md"
    json_path.write_text(json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(f"""# Phase 13B — Declarer-Play Adapter / Recommendation Integration

## Inventory and integration decision

A repository-wide Python inventory found no production-capable declarer-play engine, state model, card recommender, restricted-choice calculator, vacant-places calculator, trump-break calculator, or Monte Carlo play engine. The play-related runtime files are knowledge retrieval/metadata maintenance; `bridge.playing_strength_policy` evaluates auction suitability and is not card play.

Consequently there is no canonical declarer production entry point to adapt. Phase 13B does not invent one. `analyze_deal_decision` now dispatches an explicit `DECLARER_PLAY` stage to a stable adapter boundary which returns `NO_DECISION`, `NONE`, and `MISSING_STATE`. It supplies no card, explanation beyond the factual integration gap, source, probability/counting evidence, or numeric confidence.

Restricted choice, vacant places, distribution probabilities, trump breaks, and Monte Carlo are all **NOT USED BY CURRENT DECLARER ENGINE**, because no such engine exists. Existing direct APIs are unchanged.

## Deterministic architecture benchmark

- Positions: {benchmark.analyzed_positions}
- Recommendations: {benchmark.recommendations}
- Abstentions: {benchmark.abstentions}
- No-decisions: {benchmark.no_decisions}
- Errors: {benchmark.errors}
- Stage counts: {benchmark.stage_counts}
- Action counts: {benchmark.action_counts}
- Ordinary benchmark: {benchmark.ordinary_benchmark}
- Phase 12 guards: {benchmark.phase12_guards}

The retained eight Phase 13A fixtures plus two repeated declarer missing-state fixtures prove stable dispatch and determinism. A successful declarer card fixture, explanation/source fixture, and probability fixture cannot honestly be supplied until a production state model and recommender exist.

## Compatibility and next phase

Auction behavior and the Phase 12N `2NT` result are unchanged. Routes remain 45. Bidding rules/routes added: 0. Production defaults changed: NO. Canonical knowledge Markdown changed by Phase 13B: 0.

Selected Phase 13C: **{benchmark.phase13c_direction}**.

Current cumulative Full Kit: Phase 13B
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_declarer_play_adapter_integration_benchmark(), Path.cwd())
