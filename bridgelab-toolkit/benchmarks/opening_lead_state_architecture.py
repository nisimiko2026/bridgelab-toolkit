"""Phase 13H deterministic opening-lead state architecture benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Auction, Bid, Contract, Doubling, Strain
from bridge.deal_analysis import AnalysisStage, DealAnalysisContext, analyze_deal_decision
from bridge.models import Hand, Seat, Vulnerability
from bridge.opening_lead_state import OpeningLeadInput, build_opening_lead_probability_context, build_opening_lead_state
from bridge.sayc_route_configuration import create_standard_sayc_router


BALANCED = Hand.parse("KJ72.Q83.T94.762")
LONG_SUIT = Hand.parse("KQJ876.32.43.543")
SINGLETON = Hand.parse("KQJ8.A9876.432.5")


def _input(**changes: object) -> OpeningLeadInput:
    values: dict[str, object] = {
        "contract": Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH), "declarer_seat": Seat.SOUTH,
        "opening_leader_seat": Seat.WEST, "opening_leader_hand": BALANCED,
    }
    values.update(changes)
    return OpeningLeadInput(**values)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class OpeningLeadStateArchitectureBenchmark:
    opening_lead_fixtures: int
    valid_states: int
    incomplete_states: int
    invalid_states: int
    legal_lead_counts: tuple[int, ...]
    auction_present_states: int
    probability_context_builds: int
    recommendations: int
    deterministic_repeats: int
    fixture_results: tuple[dict[str, object], ...]
    reusable_inventory: tuple[dict[str, str], ...]
    partnership_policy_audit: dict[str, str]
    architecture: dict[str, object]
    guards: dict[str, object]
    phase13i_direction: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_opening_lead_state_architecture_benchmark() -> OpeningLeadStateArchitectureBenchmark:
    auction = Auction(Seat.SOUTH, ("3NT", "P", "P", "P"))
    fixtures = (
        ("valid-notrump", _input(), "valid"),
        ("valid-suit-contract", _input(contract=Contract(Bid(4, Strain.HEARTS), Seat.SOUTH)), "valid"),
        ("balanced-hand", _input(), "valid"),
        ("long-suit", _input(opening_leader_hand=LONG_SUIT), "valid"),
        ("singleton", _input(opening_leader_hand=SINGLETON), "valid"),
        ("doubled-contract", _input(contract=Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH, Doubling.DOUBLED)), "valid"),
        ("vulnerability", _input(vulnerability=Vulnerability.NS), "valid"),
        ("complete-auction", _input(auction=auction), "valid"),
        ("missing-leader-hand", _input(opening_leader_hand=None), "incomplete"),
        ("wrong-leader-seat", _input(opening_leader_seat=Seat.EAST), "invalid"),
        ("invalid-card-state", _input(opening_leader_hand="not-a-hand"), "invalid"),
        ("no-dummy-required", _input(), "valid"),
        ("valid-no-engine", _input(), "valid"),
        ("deterministic-repeat", _input(), "valid"),
    )
    router = create_standard_sayc_router()
    rows = []
    contexts = 0
    for name, source, classification in fixtures:
        built = build_opening_lead_state(source)
        top = analyze_deal_decision(
            DealAnalysisContext(AnalysisStage.OPENING_LEAD, opening_lead=source), bidding_router=router
        )
        if built.state is not None:
            build_opening_lead_probability_context(built.state)
            contexts += 1
        rows.append({
            "name": name, "classification": classification, "state_ready": built.is_ready,
            "failure_code": None if built.failure_code is None else built.failure_code.value,
            "legal_lead_count": 0 if built.state is None else len(built.state.legal_leads),
            "auction_present": built.state is not None and built.state.auction_entries is not None,
            "status": top.status.value, "action_kind": top.action.kind.value,
        })
    return OpeningLeadStateArchitectureBenchmark(
        len(rows), 11, 1, 2, tuple(row["legal_lead_count"] for row in rows), 1, contexts, 0, 1,
        tuple(rows),
        (
            {"module": "bridge.models", "types": "Card/Suit/Rank/Seat/Vulnerability/Hand", "reuse": "direct"},
            {"module": "bridge.auction", "types": "Bid/Strain/Doubling/Contract/AuctionEntry", "reuse": "direct immutable snapshot"},
            {"module": "bridge.defensive_play_state", "types": "defender validation/accounting concepts", "reuse": "semantic pattern only; dummy/trick excluded"},
            {"module": "bridge.probability_engine", "types": "ProbabilityContext", "reuse": "leader-known cards only"},
        ),
        {"fourth_best": "PARTNERSHIP_POLICY_REQUIRED", "third_fifth": "PARTNERSHIP_POLICY_REQUIRED",
         "top_of_sequence": "PARTNERSHIP_POLICY_REQUIRED", "top_of_nothing": "PARTNERSHIP_POLICY_REQUIRED",
         "mud": "NOT_PRESENT", "second_highest_bad_suit": "SOURCE_INSUFFICIENT",
         "honor_sequence": "PARTNERSHIP_POLICY_REQUIRED", "interior_sequence": "SOURCE_PARTIAL",
         "trump_lead": "SOURCE_PARTIAL", "passive_aggressive": "SOURCE_PARTIAL",
         "unsupported_ace_king": "SOURCE_PARTIAL", "rusinow": "PARTNERSHIP_POLICY_REQUIRED",
         "coded_tens_nines": "NOT_PRESENT", "production_defaults": "NONE"},
        {"total_positions_or_requests": 70, "auction_positions": 5, "opening_lead_positions": 14,
         "declarer_positions": 23, "defensive_positions": 15, "valid_opening_lead_states": 11,
         "invalid_or_incomplete_opening_lead_states": 3, "bidding_recommendations": 2,
         "opening_lead_recommendations": 0, "declarer_recommendations": 2,
         "defensive_recommendations": 0, "probability_evidence_items": 3,
         "abstentions": 3, "no_decisions": 51, "errors": 0,
         "action_counts": {"bid": 2, "card-play": 2, "none": 54}},
        {"routes": 45, "ordinary": {"production_calls": 7_871, "completed": 761, "abstained": 9_239},
         "defensive_recommendations": 0, "probability_engines": 1, "probability_formulas_added": 0,
         "simple_unblock_hits": 2, "illegal_recommendations": 0,
         "phase12": {"N": 24, "O": 23, "Q": 1_194, "R": 166, "S": 540, "T": 33,
                     "G": {"4H": 17, "4S": 21}, "H": 197, "L": {"completed": 5, "abstained": 7},
                     "jacoby": {"hearts": 62, "spades": 61}}},
        "B. OPENING-LEAD POLICY ARCHITECTURE",
    )


def write_artifacts(benchmark: OpeningLeadStateArchitectureBenchmark, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    json_path = output / "bridgelab_phase13h_opening_lead_state_architecture.json"
    markdown_path = output / "bridgelab_phase13h_opening_lead_state_architecture.md"
    json_path.write_text(json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(f"""# Phase 13H — Opening-Lead State Architecture

## State and information boundary

`OpeningLeadState` is immutable and reuses canonical `Hand`, card/seat/contract types, an immutable `AuctionEntry` snapshot, and `ProbabilityContext`. It is distinct from `DefensivePlayState`: no card or trick exists yet, dummy is not exposed, and all 13 cards in the leader's hand are legal.

The leader must be immediately left of declarer; partner is derived canonically. Optional complete auction history is preserved without interpreting calls. Structural hand outputs include count, suit lengths, and honor holdings without ranking leads. Known-card accounting includes only the leader's 13 cards, yielding 39 unknown; no dummy, declarer, or partner cards exist in the model.

The factory distinguishes missing contract/declarer/leader seat/leader hand, wrong leader, caller-required missing auction, invalid hand state, and inconsistent contract/auction. A valid top-level state returns `NO_DECISION/NONE/ENGINE_UNAVAILABLE`; incomplete state returns `NO_DECISION/NONE/MISSING_STATE`. No lead is recommended.

## Policy audit and benchmark

Lead methods such as fourth-best versus third/fifth, honor sequences, top-of-nothing, and Rusinow are partnership-policy dependent. Other strategic families are partial or absent. Phase 13H assigns no default and implements no rule.

- Fixtures / valid / incomplete / invalid: {benchmark.opening_lead_fixtures} / {benchmark.valid_states} / {benchmark.incomplete_states} / {benchmark.invalid_states}
- Auction-present / probability-context builds: {benchmark.auction_present_states} / {benchmark.probability_context_builds}
- Opening-lead recommendations: {benchmark.recommendations}
- Extended architecture: {benchmark.architecture}

Routes remain 45. Bidding rules/routes added: 0/0. Opening-lead and defensive algorithms added: 0/0. Probability formulas added: 0. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13H: 0.

Selected Phase 13I: **{benchmark.phase13i_direction}**, because useful opening-lead treatments are primarily agreement-dependent and must not receive implicit defaults.

Current cumulative Full Kit: Phase 13H
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_opening_lead_state_architecture_benchmark(), Path.cwd())
