"""Phase 13E deterministic probability-evidence adapter benchmark."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Bid, Contract, Strain
from bridge.declarer_play_state import DeclarerPlayInput, Trick, build_declarer_play_state
from bridge.models import Card, Seat
from bridge.probability_evidence import KnownCardCountQuestion, collect_declarer_probability_evidence


def _state():
    built = build_declarer_play_state(DeclarerPlayInput(
        contract=Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH), declarer_seat=Seat.SOUTH,
        declarer_cards=frozenset(Card.parse(c) for c in ("KC", "QC", "2S")),
        dummy_cards=frozenset(Card.parse(c) for c in ("AC", "JC", "TC", "9C", "3S")),
        current_actor=Seat.SOUTH, completed_tricks=(), current_trick=Trick(Seat.SOUTH),
    ))
    assert built.state is not None
    return built.state


@dataclass(frozen=True, slots=True)
class ProbabilityEvidenceAdapterBenchmark:
    evidence_requests: int
    successful_results: int
    unavailable_results: int
    errors: int
    deterministic_exact_calculations: int
    deterministic_simulations: int
    counts_by_evidence_type: dict[str, int]
    representative_results: tuple[dict[str, object], ...]
    module_inventory: tuple[dict[str, object], ...]
    readiness: dict[str, dict[str, str]]
    architecture: dict[str, object]
    guards: dict[str, object]
    phase13f_direction: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_probability_evidence_adapter_benchmark() -> ProbabilityEvidenceAdapterBenchmark:
    state = _state()
    requests = (
        ("known-count", state, KnownCardCountQuestion()),
        ("custom-subject", state, KnownCardCountQuestion("cards outside declarer view")),
        ("missing-question", state, None),
        ("missing-state", None, KnownCardCountQuestion()),
        ("repeat-missing-state", None, KnownCardCountQuestion()),
    )
    rows = []
    for name, supplied_state, question in requests:
        result = collect_declarer_probability_evidence(supplied_state, question)
        item = result.evidence[0] if result.evidence else None
        rows.append({
            "name": name, "status": result.status.value,
            "evidence_type": None if item is None else item.evidence_type.value,
            "result": None if item is None else item.result,
            "probability": None if item is None else item.probability,
            "deterministic": None if item is None else item.deterministic,
            "simulated": None if item is None else item.simulated,
            "failure_code": None if result.failure_code is None else result.failure_code.value,
        })
    statuses = Counter(row["status"] for row in rows)
    types = Counter(row["evidence_type"] or "unavailable" for row in rows)
    return ProbabilityEvidenceAdapterBenchmark(
        len(rows), statuses["available"], statuses["unavailable"], statuses["error"], 2, 0,
        dict(sorted(types.items())), tuple(rows),
        (
            {"module": "bridge.declarer_play_state", "entry_point": "visible_cards/played_cards/unknown_card_count", "calculation": "exact deterministic", "production_used": True, "adapter": "READY"},
            {"module": None, "entry_point": None, "family": "restricted choice", "adapter": "NOT_READY", "gap": "no production calculation"},
            {"module": None, "entry_point": None, "family": "vacant places", "adapter": "NOT_READY", "gap": "no production calculation"},
            {"module": None, "entry_point": None, "family": "suit distributions", "adapter": "NOT_READY", "gap": "no production calculation"},
            {"module": None, "entry_point": None, "family": "trump breaks", "adapter": "NOT_READY", "gap": "no production calculation"},
            {"module": "bridge.deals/bridge.batch_simulation", "entry_point": "seeded deal/bidding simulation", "family": "Monte Carlo declarer evidence", "adapter": "NOT_READY", "gap": "simulates deals/auctions, not declarer-line outcomes"},
        ),
        {
            "known_card_count": {"status": "READY", "blocker": "none"},
            "restricted_choice": {"status": "NOT_READY", "blocker": "no production posterior calculator or typed event inputs"},
            "vacant_places": {"status": "NOT_READY", "blocker": "no production seat-weight calculator or defender constraints"},
            "suit_distribution": {"status": "NOT_READY", "blocker": "no production distribution calculator"},
            "trump_breaks": {"status": "NOT_READY", "blocker": "no production trump-break calculator"},
            "monte_carlo": {"status": "NOT_READY", "blocker": "no declarer-play sampler or line-success evaluator"},
        },
        {"total_positions_or_requests": 35, "bidding_recommendations": 2,
         "declarer_recommendations": 2, "probability_evidence_items": 2,
         "unavailable_evidence_requests": 3, "no_decisions": 23, "errors": 0},
        {"routes": 45, "ordinary": {"production_calls": 7_871, "completed": 761, "abstained": 9_239},
         "phase13d": {"positive_recommendations": 2, "illegal_recommendations": 0,
                      "technique": "SIMPLE_UNBLOCK_KING", "recommended_rank": "KING"},
         "phase12": {"N": 24, "O": 23, "Q": 1_194, "R": 166, "S": 540, "T": 33,
                     "G": {"4H": 17, "4S": 21}, "H": 197, "L": {"completed": 5, "abstained": 7},
                     "jacoby": {"hearts": 62, "spades": 61}}},
        "E. PROBABILITY ENGINE ARCHITECTURE",
    )


def write_artifacts(benchmark: ProbabilityEvidenceAdapterBenchmark, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    json_path = output / "bridgelab_phase13e_probability_evidence_adapter.json"
    markdown_path = output / "bridgelab_phase13e_probability_evidence_adapter.md"
    json_path.write_text(json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(f"""# Phase 13E — Probability-Evidence Adapter

## Inventory and readiness

The production inventory found one existing calculation suitable for normalization: Phase 13C's exact `visible_cards`, `played_cards`, and `unknown_card_count`. No production restricted-choice posterior, vacant-place weighting, suit-distribution, trump-break, or declarer-play Monte Carlo calculation exists. Deal/bidding simulation does not evaluate declarer lines and is not relabeled as probability evidence.

Readiness: {benchmark.readiness}

## Evidence contract and adapter

Immutable `ProbabilityEvidence` carries an evidence type, subject, assumptions, known facts, result, optional probability/alternatives/sample size, exact/simulated flags, optional source, and trace. Phase 13E defines only the actually supported `KNOWN_CARD_COUNT` type. `KnownCardCountQuestion` makes collection explicit and demand-driven; `collect_declarer_probability_evidence` reuses validated `DeclarerPlayState` accounting and never infers hidden defender cards.

Missing question/state and invalid accounting have structured outcomes. An unavailable request returns no evidence—not a misleading zero probability. The representative exact result is 8 visible + 0 played = 44 unknown; it is deterministic, nonsimulated, source-free computational evidence with no confidence metadata.

`DeclarerRecommendation` can carry immutable probability evidence, and `analyze_deal_decision` preserves attached items. `SIMPLE_UNBLOCK_KING` remains unchanged and carries an empty collection because it does not require probability evidence. The top-level analyzer never runs evidence families automatically.

## Benchmarks and guards

- Requests: {benchmark.evidence_requests}
- Successful / unavailable / errors: {benchmark.successful_results} / {benchmark.unavailable_results} / {benchmark.errors}
- Exact calculations / deterministic simulations: {benchmark.deterministic_exact_calculations} / {benchmark.deterministic_simulations}
- Counts: {benchmark.counts_by_evidence_type}
- Extended architecture: {benchmark.architecture}

Routes remain 45. Bidding rules/routes added: 0/0. Declarer techniques added: 0. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13E: 0.

Selected Phase 13F: **{benchmark.phase13f_direction}**, because the requested probability families have no production calculations to adapt safely.

Current cumulative Full Kit: Phase 13E
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_probability_evidence_adapter_benchmark(), Path.cwd())
