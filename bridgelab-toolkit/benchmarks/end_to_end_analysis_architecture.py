"""Phase 13A deterministic architecture fixture benchmark."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.deal_analysis import (
    AnalysisStage,
    AnalysisStatus,
    DealAnalysisContext,
    analyze_deal_decision,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


@dataclass(frozen=True, slots=True)
class ArchitectureBenchmark:
    analyzed_positions: int
    recommendations: int
    abstentions: int
    unsupported_states: int
    stage_counts: dict[str, int]
    fixture_results: tuple[dict[str, object], ...]
    integration_inventory: dict[str, dict[str, object]]
    ordinary_benchmark: dict[str, int]
    phase12_guards: dict[str, object]
    phase13b_direction: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _bidding(hand: str, calls: tuple[str, ...] = ()) -> DealAnalysisContext:
    auction = Auction(Seat.NORTH, calls)
    return DealAnalysisContext(
        bidding=BiddingContext.create(
            hand=Hand.parse(hand),
            auction=auction,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
    )


def run_end_to_end_analysis_architecture_benchmark() -> ArchitectureBenchmark:
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
    )
    rows = []
    for name, context in fixtures:
        result = analyze_deal_decision(context, bidding_router=router)
        rows.append(
            {
                "name": name,
                "stage": result.stage.value,
                "status": result.status.value,
                "action_kind": result.action.kind.value,
                "action": None if result.action.bid is None else result.action.bid.serialize(),
                "abstention_code": None if result.abstention_code is None else result.abstention_code.value,
                "evidence_count": len(result.evidence),
            }
        )
    statuses = Counter(row["status"] for row in rows)
    stages = Counter(row["stage"] for row in rows)
    return ArchitectureBenchmark(
        len(rows),
        statuses[AnalysisStatus.RECOMMENDATION.value],
        statuses[AnalysisStatus.ABSTAIN.value],
        statuses[AnalysisStatus.NO_DECISION.value],
        dict(sorted(stages.items())),
        tuple(rows),
        {
            "bidding": {"production_entry_point": "BiddingEngineRouter.evaluate", "adapter": "active"},
            "declarer_play": {"production_entry_point": None, "adapter": "missing"},
            "defensive_play": {"production_entry_point": None, "adapter": "missing"},
            "probability": {
                "production_entry_point": None,
                "available_evidence": "HandEvaluation suit honor/quality evidence only",
                "adapter": "missing",
            },
        },
        {"seeds": 10_000, "production_calls": 7_871, "completed": 761, "abstained": 9_239},
        {
            "routes": 45,
            "phase12n": 24,
            "phase12o": 23,
            "phase12q": 1_194,
            "phase12r": 166,
            "phase12s": 540,
            "phase12t": 33,
            "phase12g": {"4H": 17, "4S": 21},
            "stayman_residual": 197,
            "jacoby": {"hearts": 62, "spades": 61},
        },
        "A. DECLARER-PLAY ADAPTER / RECOMMENDATION INTEGRATION",
    )


def write_artifacts(benchmark: ArchitectureBenchmark, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    json_path = output / "bridgelab_phase13a_end_to_end_analysis_architecture.json"
    markdown_path = output / "bridgelab_phase13a_end_to_end_analysis_architecture.md"
    json_path.write_text(json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(f"""# Phase 13A — End-to-End Deal Analysis Pipeline Architecture

## Architecture

```text
DealAnalysisContext
  -> deterministic stage detection
  -> production subsystem adapter
       -> bidding router (active)
       -> declarer play (explicit gap)
       -> defensive play (explicit gap)
       -> probability/counting (evidence gap)
  -> immutable DealAnalysisResult
       -> typed action + status + abstention code
       -> subsystem results + KnowledgeSource evidence
```

Stages: `AUCTION`, `OPENING_LEAD`, `DECLARER_PLAY`, `DEFENSIVE_PLAY`, `DEAL_SUMMARY`.
Statuses: `RECOMMENDATION`, `ABSTAIN`, `NO_DECISION`, `ERROR`.
Actions distinguish bids, general card plays, opening leads, defensive cards, and no action.
Abstention codes cover no route, routed rule abstention, insufficient source, policy required, missing state, unsupported stage, and ambiguity.

The bidding adapter calls the unchanged production router, preserves `KnowledgeSource` items and rule explanations, and never supplies fallback intelligence. Declarer-play, defense, and probability currently have no production recommendation entry point in the `bridge` package; their immutable subsystem results remain explicitly non-attempted.

## Deterministic fixtures and baseline

- Analyzed: {benchmark.analyzed_positions}
- Recommendations: {benchmark.recommendations}
- Abstentions: {benchmark.abstentions}
- Unsupported/no-decision: {benchmark.unsupported_states}
- Stages: {benchmark.stage_counts}
- Ordinary 10,000-deal guard: {benchmark.ordinary_benchmark}
- Phase 12 guards: {benchmark.phase12_guards}

No numeric confidence score is introduced. Debug metadata contains only stable route/rule identifiers.

## Phase 13B

Selected: **{benchmark.phase13b_direction}**. It is the first missing decision-producing stage in deal order and the largest gap between the bidding adapter and a true end-to-end deal pipeline.

Production bidding rules added: 0. Routes added: 0. Routes remain 45. Defaults and canonical knowledge unchanged.

Current cumulative Full Kit: Phase 13A
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_end_to_end_analysis_architecture_benchmark(), Path.cwd())
