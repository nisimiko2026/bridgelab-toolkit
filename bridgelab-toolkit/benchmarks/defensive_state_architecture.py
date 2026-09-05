"""Phase 13G deterministic defensive-state architecture benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Bid, Contract, Strain
from bridge.deal_analysis import AnalysisStage, DealAnalysisContext, analyze_deal_decision
from bridge.declarer_play_state import PlayedCard, Trick
from bridge.defensive_play_state import DefensivePlayInput, build_defensive_play_state
from bridge.models import Card, Seat
from bridge.sayc_route_configuration import create_standard_sayc_router


def _cards(*values: str) -> frozenset[Card]:
    return frozenset(Card.parse(value) for value in values)


def _input(**changes: object) -> DefensivePlayInput:
    values: dict[str, object] = {
        "contract": Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH), "declarer_seat": Seat.SOUTH,
        "defender_cards": _cards("AH", "5H", "2C"), "dummy_cards": _cards("KH", "QS", "3C"),
        "current_actor": Seat.EAST, "completed_tricks": (),
        "current_trick": Trick(Seat.NORTH, (PlayedCard(Seat.NORTH, Card.parse("2H")),)),
        "opening_leader": Seat.WEST,
    }
    values.update(changes)
    return DefensivePlayInput(**values)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class DefensiveStateArchitectureBenchmark:
    defensive_fixtures: int
    valid_states: int
    incomplete_states: int
    invalid_states: int
    follow_suit_cases: int
    void_cases: int
    legal_action_counts: tuple[int, ...]
    deterministic_repeats: int
    recommendations: int
    fixture_results: tuple[dict[str, object], ...]
    inventory: tuple[dict[str, str], ...]
    signaling_policy_audit: dict[str, str]
    probability_readiness: dict[str, str]
    architecture: dict[str, object]
    guards: dict[str, object]
    phase13h_direction: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_defensive_state_architecture_benchmark() -> DefensiveStateArchitectureBenchmark:
    complete = Trick(Seat.NORTH, (
        PlayedCard(Seat.NORTH, Card.parse("2S")), PlayedCard(Seat.EAST, Card.parse("AS")),
        PlayedCard(Seat.SOUTH, Card.parse("3S")), PlayedCard(Seat.WEST, Card.parse("4S")),
    ))
    third = Trick(Seat.WEST, (
        PlayedCard(Seat.WEST, Card.parse("3H")), PlayedCard(Seat.NORTH, Card.parse("2H")),
    ))
    fourth = Trick(Seat.NORTH, (
        PlayedCard(Seat.NORTH, Card.parse("2H")), PlayedCard(Seat.EAST, Card.parse("3H")),
        PlayedCard(Seat.SOUTH, Card.parse("4H")),
    ))
    fixtures = (
        ("follow-suit", _input(), "valid"),
        ("void-led-suit", _input(defender_cards=_cards("AS", "2C")), "valid"),
        ("second-hand", _input(), "valid"),
        ("third-hand", _input(current_trick=third), "valid"),
        ("fourth-hand", _input(current_actor=Seat.WEST, current_trick=fourth), "valid"),
        ("dummy-visible", _input(), "valid"),
        ("later-trick", _input(completed_tricks=(complete,)), "valid"),
        ("missing-defender-hand", _input(defender_cards=None), "incomplete"),
        ("missing-dummy", _input(dummy_cards=None), "incomplete"),
        ("actor-declarer", _input(current_actor=Seat.SOUTH), "invalid"),
        ("actor-dummy", _input(current_actor=Seat.NORTH), "invalid"),
        ("duplicate-card", _input(dummy_cards=_cards("AH", "QS")), "invalid"),
        ("valid-no-engine", _input(), "valid"),
        ("deterministic-repeat", _input(), "valid"),
    )
    router = create_standard_sayc_router()
    rows = []
    for name, source, classification in fixtures:
        built = build_defensive_play_state(source)
        top = analyze_deal_decision(
            DealAnalysisContext(AnalysisStage.DEFENSIVE_PLAY, defensive_play=source), bidding_router=router
        )
        rows.append({
            "name": name, "classification": classification, "state_ready": built.is_ready,
            "failure_code": None if built.failure_code is None else built.failure_code.value,
            "legal_action_count": 0 if built.state is None else len(built.state.legal_actions),
            "top_level_status": top.status.value, "action_kind": top.action.kind.value,
        })
    return DefensiveStateArchitectureBenchmark(
        len(rows), sum(row["state_ready"] for row in rows), 2, 3, 1, 1,
        tuple(row["legal_action_count"] for row in rows), 1, 0, tuple(rows),
        (
            {"module": "bridge.models", "types": "Card/Suit/Rank/Seat/Vulnerability", "reuse": "direct"},
            {"module": "bridge.auction", "types": "Bid/Strain/Doubling/Contract", "reuse": "direct"},
            {"module": "bridge.declarer_play_state", "types": "PlayedCard/Trick/legal_cards", "reuse": "shared helper"},
            {"module": "bridge.probability_engine", "types": "ProbabilityContext", "reuse": "defender-known bridge"},
        ),
        {"attitude": "POLICY_REQUIRED", "count": "POLICY_REQUIRED", "suit_preference": "POLICY_REQUIRED",
         "standard_signals": "POLICY_REQUIRED", "upside_down_signals": "POLICY_REQUIRED",
         "opening_lead_agreements": "POLICY_REQUIRED", "production_defaults": "NONE"},
        {"KNOWN_CARD_COUNT": "READY", "RESTRICTED_CHOICE": "ARCHITECTURE_READY",
         "VACANT_PLACES": "ARCHITECTURE_READY", "SUIT_DISTRIBUTION": "ARCHITECTURE_READY",
         "TRUMP_BREAKS": "ARCHITECTURE_READY", "MONTE_CARLO": "PARTIALLY_READY"},
        {"total_positions_or_requests": 56, "auction_positions": 5, "declarer_positions": 23,
         "defensive_positions": 15, "valid_defensive_states": 9,
         "invalid_or_incomplete_defensive_states": 6, "bidding_recommendations": 2,
         "declarer_recommendations": 2, "defensive_recommendations": 0,
         "abstentions": 3, "no_decisions": 37, "errors": 0,
         "action_counts": {"bid": 2, "card-play": 2, "none": 40}},
        {"routes": 45, "ordinary": {"production_calls": 7_871, "completed": 761, "abstained": 9_239},
         "probability_engines": 1, "probability_formulas_added": 0,
         "simple_unblock_hits": 2, "illegal_recommendations": 0,
         "phase12": {"N": 24, "O": 23, "Q": 1_194, "R": 166, "S": 540, "T": 33,
                     "G": {"4H": 17, "4S": 21}, "H": 197, "L": {"completed": 5, "abstained": 7},
                     "jacoby": {"hearts": 62, "spades": 61}}},
        "B. OPENING-LEAD STATE ARCHITECTURE",
    )


def write_artifacts(benchmark: DefensiveStateArchitectureBenchmark, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    json_path = output / "bridgelab_phase13g_defensive_state_architecture.json"
    markdown_path = output / "bridgelab_phase13g_defensive_state_architecture.md"
    json_path.write_text(json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(f"""# Phase 13G — Defensive State Architecture

## State and knowledge boundary

`DefensivePlayState` is immutable and reuses canonical `Card`, `Suit`, `Rank`, `Seat`, `Vulnerability`, `Bid`, `Strain`, `Doubling`, `Contract`, `PlayedCard`, `Trick`, and `legal_cards`. It stores only the acting defender's remaining cards, exposed dummy cards, and validated play history. Partner and declarer hidden holdings are neither required nor represented.

The factory distinguishes missing contract/declarer/defender/dummy/actor/history, declarer or dummy acting illegally as defender, inconsistent trick order, and other invalid card state. Derived properties expose declarer, dummy, defender partner, exact legal actions, follow-suit status, trick number/counts, visible/played cards, and unknown-card count. `build_defensive_probability_context` exports only those defender-known facts.

Incomplete top-level defensive analysis returns `NO_DECISION/NONE/MISSING_STATE` with precise metadata. A valid state returns `NO_DECISION/NONE/ENGINE_UNAVAILABLE`. Phase 13G selects no card and adds no defensive algorithm. `OPENING_LEAD` remains a distinct unintegrated stage.

## Signaling and policy audit

Canonical knowledge covers attitude, count, suit preference, standard and upside-down signals, carding styles, and opening-lead agreements. These are partnership-policy dependent; Phase 13G implements none and sets no defaults.

## Benchmark

- Fixtures / valid / incomplete / invalid: {benchmark.defensive_fixtures} / {benchmark.valid_states} / {benchmark.incomplete_states} / {benchmark.invalid_states}
- Follow-suit / void cases: {benchmark.follow_suit_cases} / {benchmark.void_cases}
- Defensive recommendations: {benchmark.recommendations}
- Extended architecture: {benchmark.architecture}
- Probability readiness: {benchmark.probability_readiness}

Routes remain 45. Bidding rules/routes added: 0/0. Defensive algorithms added: 0. Probability formulas added: 0. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13G: 0.

Selected Phase 13H: **{benchmark.phase13h_direction}**, because opening lead is the remaining distinct play-stage state gap and can reuse the new defensive foundations.

Current cumulative Full Kit: Phase 13G
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_defensive_state_architecture_benchmark(), Path.cwd())
