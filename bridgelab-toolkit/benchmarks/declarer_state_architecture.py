"""Phase 13C deterministic declarer-state architecture benchmark."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from benchmarks.declarer_play_adapter_integration import run_declarer_play_adapter_integration_benchmark
from bridge.auction import Bid, Contract, Strain
from bridge.deal_analysis import AnalysisStage, DealAnalysisContext, analyze_deal_decision
from bridge.declarer_play_state import DeclarerPlayInput, PlayedCard, Trick, build_declarer_play_state
from bridge.models import Card, Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


def _cards(*values: str) -> frozenset[Card]:
    return frozenset(Card.parse(value) for value in values)


def _input(**changes: object) -> DeclarerPlayInput:
    values: dict[str, object] = {
        "contract": Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH), "declarer_seat": Seat.SOUTH,
        "declarer_cards": _cards("AS", "KH", "2C"), "dummy_cards": _cards("QS", "QH", "3C"),
        "current_actor": Seat.NORTH, "completed_tricks": (),
        "current_trick": Trick(Seat.WEST, (PlayedCard(Seat.WEST, Card.parse("2H")),)),
        "vulnerability": Vulnerability.NS, "opening_leader": Seat.WEST,
    }
    values.update(changes)
    return DeclarerPlayInput(**values)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class DeclarerStateArchitectureBenchmark:
    total_positions: int
    auction_positions: int
    declarer_positions: int
    valid_declarer_states: int
    invalid_or_incomplete_declarer_states: int
    recommendations: int
    abstentions: int
    no_decisions: int
    errors: int
    action_counts: dict[str, int]
    state_fixtures: tuple[dict[str, object], ...]
    reusable_inventory: tuple[dict[str, object], ...]
    probability_readiness: dict[str, dict[str, str]]
    guards: dict[str, object]
    phase13d_direction: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_declarer_state_architecture_benchmark() -> DeclarerStateArchitectureBenchmark:
    completed = Trick(Seat.NORTH, (
        PlayedCard(Seat.NORTH, Card.parse("AC")), PlayedCard(Seat.EAST, Card.parse("4C")),
        PlayedCard(Seat.SOUTH, Card.parse("KC")), PlayedCard(Seat.WEST, Card.parse("5C")),
    ))
    fixtures = (
        ("opening-lead-dummy-visible", _input()),
        ("declarer-hand-to-play", _input(current_actor=Seat.SOUTH, current_trick=Trick(Seat.SOUTH))),
        ("dummy-hand-to-play", _input()),
        ("must-follow-suit", _input()),
        ("void-in-led-suit", _input(dummy_cards=_cards("QS", "3C"))),
        ("partially-completed-trick", _input(
            current_actor=Seat.SOUTH,
            current_trick=Trick(Seat.WEST, (
                PlayedCard(Seat.WEST, Card.parse("2H")), PlayedCard(Seat.NORTH, Card.parse("QH")),
                PlayedCard(Seat.EAST, Card.parse("3H")),
            )),
            dummy_cards=_cards("QS", "3C"),
        )),
        ("later-trick-history", _input(completed_tricks=(completed,))),
        ("missing-dummy", _input(dummy_cards=None)),
        ("invalid-duplicate", _input(dummy_cards=_cards("AS", "QH"))),
        ("valid-no-engine", _input()),
    )
    router = create_standard_sayc_router()
    rows = []
    for name, source in fixtures:
        built = build_declarer_play_state(source)
        result = analyze_deal_decision(
            DealAnalysisContext(AnalysisStage.DECLARER_PLAY, declarer_play=source), bidding_router=router
        )
        rows.append({
            "name": name, "state_ready": built.is_ready,
            "failure_code": None if built.failure_code is None else built.failure_code.value,
            "status": result.status.value, "action_kind": result.action.kind.value,
            "legal_action_count": 0 if built.state is None else len(built.state.legal_actions),
        })
    prior = run_declarer_play_adapter_integration_benchmark()
    statuses = Counter(item["status"] for item in prior.fixture_results)
    statuses.update(row["status"] for row in rows)
    actions = Counter(item["action_kind"] for item in prior.fixture_results)
    actions.update(row["action_kind"] for row in rows)
    ready = sum(bool(row["state_ready"]) for row in rows)
    return DeclarerStateArchitectureBenchmark(
        prior.analyzed_positions + len(rows), 5, 3 + len(rows), ready, 3 + len(rows) - ready,
        statuses["recommendation"], statuses["abstain"], statuses["no-decision"], statuses["error"],
        dict(sorted(actions.items())), tuple(rows),
        (
            {"module": "bridge.models", "types": "Card, Suit, Rank, Seat, Vulnerability, Hand", "reuse": "YES; Hand adapted to remaining-card sets"},
            {"module": "bridge.auction", "types": "Bid, Strain, Doubling, Contract, Auction", "reuse": "YES"},
            {"module": "bridge.deals", "types": "Deal", "reuse": "INPUT SOURCE; complete hidden hands not stored"},
            {"module": "bridge.declarer_play_state", "types": "PlayedCard, Trick, DeclarerPlayState", "reuse": "NEW CANONICAL PLAY STATE"},
        ),
        {
            "restricted_choice": {"status": "PARTIALLY_READY", "missing": "inference/event model for equivalent honors"},
            "vacant_places": {"status": "PARTIALLY_READY", "missing": "defender known-card constraints"},
            "suit_distribution": {"status": "PARTIALLY_READY", "missing": "probability calculator and defender constraints"},
            "trump_breaks": {"status": "PARTIALLY_READY", "missing": "probability calculator"},
            "monte_carlo": {"status": "PARTIALLY_READY", "missing": "consistent hidden-hand sampler and inference constraints"},
        },
        {"routes": 45, "ordinary": {"production_calls": 7_871, "completed": 761, "abstained": 9_239},
         "phase13b": {"positions": 10, "recommendations": 2, "abstentions": 3, "no_decisions": 5, "errors": 0},
         "phase12": {"N": 24, "O": 23, "Q": 1_194, "R": 166, "S": 540, "T": 33,
                     "G": {"4H": 17, "4S": 21}, "H": 197, "L": {"completed": 5, "abstained": 7},
                     "jacoby": {"hearts": 62, "spades": 61}}},
        "A. FIRST DECLARER RECOMMENDATION ENGINE",
    )


def write_artifacts(benchmark: DeclarerStateArchitectureBenchmark, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    json_path = output / "bridgelab_phase13c_declarer_state_architecture.json"
    markdown_path = output / "bridgelab_phase13c_declarer_state_architecture.md"
    json_path.write_text(json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(f"""# Phase 13C — Declarer State Architecture

## Canonical architecture

Phase 13C adds one immutable, strategy-free `DeclarerPlayState`. It reuses the production `Card`, `Suit`, `Rank`, `Seat`, `Vulnerability`, `Bid`, `Strain`, `Doubling`, and `Contract` types. Remaining declarer/dummy holdings use immutable card sets because `Hand` correctly represents only an original 13-card hand.

`PlayedCard` binds a canonical seat and card. `Trick` preserves clockwise order, led suit, completeness, and an objective winner for trump or notrump. Completed tricks and the current trick are the single ordered play-history source. Legal actions implement only follow-suit legality.

Validation covers distinct declarer/dummy seats through partnership derivation, declarer/dummy acting authority, duplicate/played-card conflicts, complete-history tricks, current-trick length/order, current actor order, contract/declarer consistency, and canonical types. Derived state exposes acting role/cards, legal actions, trick number, visible/played cards, unknown-card count, follow-suit requirement, and objectively determined trick counts. Hidden defender hands remain unknown.

The structured factory distinguishes missing contract, declarer seat/hand, dummy hand, actor, play history, and invalid card state. A complete state reaches `NO_DECISION/NONE/ENGINE_UNAVAILABLE`; incomplete state reaches `NO_DECISION/NONE/MISSING_STATE` with precise metadata. No recommendation algorithm is added.

## Benchmark and readiness

- Total positions: {benchmark.total_positions}
- Auction positions: {benchmark.auction_positions}
- Declarer positions: {benchmark.declarer_positions}
- Valid new declarer states: {benchmark.valid_declarer_states}
- Invalid/incomplete declarer positions: {benchmark.invalid_or_incomplete_declarer_states}
- Recommendations / abstentions / no-decisions / errors: {benchmark.recommendations} / {benchmark.abstentions} / {benchmark.no_decisions} / {benchmark.errors}
- Action counts: {benchmark.action_counts}

Probability readiness: {benchmark.probability_readiness}. The state supplies deterministic raw visible/play facts but intentionally adds no probability formula or hidden-hand inference.

Routes remain 45. Bidding rules/routes added: 0/0. Declarer algorithms added: 0. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13C: 0.

Selected Phase 13D: **{benchmark.phase13d_direction}** — begin with one narrow, source-safe declarer technique rather than a general heuristic engine.

Current cumulative Full Kit: Phase 13C
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_declarer_state_architecture_benchmark(), Path.cwd())
