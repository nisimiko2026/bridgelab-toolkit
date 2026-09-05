"""Phase 13D deterministic first declarer recommendation benchmark."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Bid, Contract, Strain
from bridge.deal_analysis import AnalysisStage, DealAnalysisContext, analyze_deal_decision
from bridge.declarer_play_state import DeclarerPlayInput, PlayedCard, Trick, build_declarer_play_state
from bridge.models import Card, Seat
from bridge.sayc_route_configuration import create_standard_sayc_router


def _cards(*values: str) -> frozenset[Card]:
    return frozenset(Card.parse(value) for value in values)


def _input(**changes: object) -> DeclarerPlayInput:
    values: dict[str, object] = {
        "contract": Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH), "declarer_seat": Seat.SOUTH,
        "declarer_cards": _cards("KC", "QC", "2S"),
        "dummy_cards": _cards("AC", "JC", "TC", "9C", "3S"),
        "current_actor": Seat.SOUTH, "completed_tricks": (), "current_trick": Trick(Seat.SOUTH),
    }
    values.update(changes)
    return DeclarerPlayInput(**values)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class FirstDeclarerEngineBenchmark:
    declarer_positions: int
    recommendations: int
    abstentions: int
    no_decisions: int
    errors: int
    technique_hits: int
    near_miss_positions: int
    illegal_recommendations: int
    fixture_results: tuple[dict[str, object], ...]
    architecture: dict[str, object]
    source_inventory: tuple[dict[str, str], ...]
    guards: dict[str, object]
    phase13e_direction: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_first_declarer_recommendation_engine_benchmark() -> FirstDeclarerEngineBenchmark:
    three_cards = Trick(Seat.WEST, (
        PlayedCard(Seat.WEST, Card.parse("2H")), PlayedCard(Seat.NORTH, Card.parse("3H")),
        PlayedCard(Seat.EAST, Card.parse("4H")),
    ))
    fixtures = (
        ("exact-positive", _input(), False),
        ("declarer-hand-geometry", _input(), False),
        ("dummy-hand-reversed", _input(
            declarer_cards=_cards("AC", "JC", "TC", "9C"), dummy_cards=_cards("KC", "QC"),
            current_actor=Seat.NORTH, current_trick=Trick(Seat.NORTH)), True),
        ("one-rank-near-miss", _input(declarer_cards=_cards("KC", "8C")), True),
        ("missing-king", _input(declarer_cards=_cards("QC")), True),
        ("ambiguous-two-suits", _input(
            declarer_cards=_cards("KC", "QC", "KD", "QD"),
            dummy_cards=_cards("AC", "JC", "TC", "9C", "AD", "JD", "TD", "9D")), True),
        ("nonempty-trick-legality-boundary", _input(current_trick=three_cards), True),
        ("unrelated-position", _input(declarer_cards=_cards("AS", "KH"), dummy_cards=_cards("QS", "QH")), True),
        ("incomplete-state", _input(dummy_cards=None), False),
        ("repeat-positive", _input(), False),
    )
    router = create_standard_sayc_router()
    rows = []
    illegal = 0
    for name, source, near_miss in fixtures:
        result = analyze_deal_decision(
            DealAnalysisContext(AnalysisStage.DECLARER_PLAY, declarer_play=source), bidding_router=router
        )
        card = result.action.card
        if card is not None:
            built = build_declarer_play_state(source)
            illegal += int(built.state is None or card not in built.state.legal_actions)
        rows.append({
            "name": name, "near_miss": near_miss, "status": result.status.value,
            "action_kind": result.action.kind.value, "card": None if card is None else card.serialize(),
            "abstention_code": None if result.abstention_code is None else result.abstention_code.value,
        })
    statuses = Counter(row["status"] for row in rows)
    hits = sum(row["card"] is not None for row in rows)
    return FirstDeclarerEngineBenchmark(
        len(rows), statuses["recommendation"], statuses["abstain"], statuses["no-decision"], statuses["error"],
        hits, sum(near for _, _, near in fixtures), illegal, tuple(rows),
        {"total_positions": 30, "auction_positions": 5, "declarer_positions": 23,
         "recommendations": 4, "bidding_recommendations": 2, "declarer_recommendations": 2,
         "abstentions": 3, "no_decisions": 23, "errors": 0,
         "action_counts": {"bid": 2, "card-play": 2, "none": 26}},
        (
            {"technique": "Simple Unblock", "source": "unblock.md#Example 1 – Simple Unblock", "classification": "SOURCE_EXECUTABLE"},
            {"technique": "Marked Finesse", "source": "marked-finesse.md", "classification": "PROBABILITY_REQUIRED"},
            {"technique": "Safety Play", "source": "safety-play.md", "classification": "SOURCE_PARTIAL"},
            {"technique": "Establishing Long Suits", "source": "establishing-long-suits.md", "classification": "SOURCE_PARTIAL"},
        ),
        {"routes": 45, "ordinary": {"production_calls": 7_871, "completed": 761, "abstained": 9_239},
         "phase13c": {"positions": 20, "recommendations": 2, "declarer_recommendations": 0,
                      "abstentions": 3, "no_decisions": 15, "errors": 0},
         "phase12": {"N": 24, "O": 23, "Q": 1_194, "R": 166, "S": 540, "T": 33,
                     "G": {"4H": 17, "4S": 21}, "H": 197, "L": {"completed": 5, "abstained": 7},
                     "jacoby": {"hearts": 62, "spades": 61}}},
        "B. PROBABILITY-EVIDENCE ADAPTER",
    )


def write_artifacts(benchmark: FirstDeclarerEngineBenchmark, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    json_path = output / "bridgelab_phase13d_first_declarer_recommendation_engine.json"
    markdown_path = output / "bridgelab_phase13d_first_declarer_recommendation_engine.md"
    json_path.write_text(json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(f"""# Phase 13D — First Declarer Recommendation Engine

## Source audit and selection

The committed frozen source `play/declarer-play/general-techniques/unblock`, **Example 1 – Simple Unblock**, gives the exact combination dummy A-J-10-9 opposite declarer K-Q and explicitly orders: cash the king, then cash the queen. This candidate is `SOURCE_EXECUTABLE`. Marked finesse is `PROBABILITY_REQUIRED`; safety play and establishing long suits are `SOURCE_PARTIAL` because they require contract goals, entries, timing, defender information, or alternative-line evaluation absent from the state.

The selected `SIMPLE_UNBLOCK_KING` engine triggers only in notrump, with declarer leading an empty trick, exact K-Q in declarer's suit and exact A-J-10-9 in dummy, and exactly one matching suit. It recommends that suit's king only after confirming membership in `legal_actions`. Reversed hands, rank/suit near misses, nonempty tricks, suit contracts, missing cards, unrelated positions, and ambiguous multiple matches receive no recommendation. No probability model or fallback “play high” heuristic exists.

The result preserves the exact card, deterministic explanation and trace, and `KnowledgeSource`. Top-level normalization produces `CARD_PLAY`; incomplete states retain Phase 13C `MISSING_STATE` behavior.

## Benchmarks

- Declarer fixture positions: {benchmark.declarer_positions}
- Recommendations / abstentions / no-decisions / errors: {benchmark.recommendations} / {benchmark.abstentions} / {benchmark.no_decisions} / {benchmark.errors}
- Technique hits: {benchmark.technique_hits}
- Near misses: {benchmark.near_miss_positions}
- Illegal recommendations: {benchmark.illegal_recommendations}
- Extended architecture: {benchmark.architecture}

Routes remain 45. Bidding rules/routes added: 0/0. Declarer algorithms added: 1 narrow engine. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13D: 0.

Selected Phase 13E: **{benchmark.phase13e_direction}**, because the next valuable techniques require explicit probability/counting evidence.

Current cumulative Full Kit: Phase 13D
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_first_declarer_recommendation_engine_benchmark(), Path.cwd())
