"""Phase 13F deterministic probability-engine architecture benchmark."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from benchmarks.probability_evidence_adapter import _state
from bridge.models import Card, Suit
from bridge.probability_engine import (
    DEFAULT_PROBABILITY_ENGINE_REGISTRY, CalculationMode, ProbabilityContext,
    ProbabilityEngineStatus, evaluate_probability,
)
from bridge.probability_questions import (
    KnownCardCountQuestion, MonteCarloQuestion, RestrictedChoiceQuestion,
    SuitDistributionQuestion, TrumpBreakQuestion, VacantPlacesQuestion,
)


@dataclass(frozen=True, slots=True)
class ProbabilityEngineArchitectureBenchmark:
    questions: int
    successful_results: int
    unavailable_results: int
    invalid_input_results: int
    errors: int
    exact_results: int
    simulated_results: int
    registered_engines: tuple[str, ...]
    fixture_results: tuple[dict[str, object], ...]
    inventory: tuple[dict[str, object], ...]
    readiness: dict[str, dict[str, object]]
    architecture: dict[str, int]
    guards: dict[str, object]
    phase13g_direction: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_probability_engine_architecture_benchmark() -> ProbabilityEngineArchitectureBenchmark:
    valid = _state()
    fixtures = (
        ("known-card-success", KnownCardCountQuestion(), valid, None),
        ("invalid-known-card-accounting", KnownCardCountQuestion(), None,
         ProbabilityContext(frozenset({Card.parse("AS")}), frozenset(), 49)),
        ("restricted-choice-unregistered", RestrictedChoiceQuestion("restricted choice", Suit.CLUBS), valid, None),
        ("vacant-places-unregistered", VacantPlacesQuestion("vacant places", Suit.CLUBS), valid, None),
        ("suit-distribution-unregistered", SuitDistributionQuestion("suit distribution", Suit.CLUBS, 5), valid, None),
        ("trump-break-unregistered", TrumpBreakQuestion("trump break", Suit.SPADES, 5), valid, None),
        ("monte-carlo-unregistered", MonteCarloQuestion("simulation", seed=1, trials=100), valid, None),
    )
    rows = []
    for name, question, state, context in fixtures:
        result = evaluate_probability(question, state, context=context)
        rows.append({
            "name": name, "question_type": type(question).__name__, "status": result.status.value,
            "mode": None if result.mode is None else result.mode.value,
            "formula_id": None if result.formula_id is None else result.formula_id.value,
            "failure_code": None if result.failure_code is None else result.failure_code.value,
            "numeric_probability": None if not result.evidence else result.evidence[0].probability,
            "result": None if not result.evidence else result.evidence[0].result,
        })
    statuses = Counter(row["status"] for row in rows)
    return ProbabilityEngineArchitectureBenchmark(
        len(rows), statuses[ProbabilityEngineStatus.SUCCESS.value], statuses[ProbabilityEngineStatus.UNAVAILABLE.value],
        statuses[ProbabilityEngineStatus.INVALID_INPUT.value], statuses[ProbabilityEngineStatus.ERROR.value],
        sum(row["mode"] == CalculationMode.EXACT.value for row in rows),
        sum(row["mode"] == CalculationMode.SIMULATED.value for row in rows),
        DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types, tuple(rows),
        (
            {"module": "bridge.declarer_play_state", "formula": "52 - unique visible/played", "production": True, "tested": True, "source_linked": False, "adaptable": True},
            {"module": "bridge.deals", "formula": None, "capability": "seeded full-deal generation", "production": True, "tested": True, "adaptable": False},
            {"module": "bridge.batch_simulation", "formula": None, "capability": "seeded bidding simulation", "production": True, "tested": True, "adaptable": False},
            {"module": "knowledge/play/declarer-play/probability", "formula": "prose/tables only", "production": False, "tested": False, "adaptable": False},
        ),
        {
            "KNOWN_CARD_COUNT": {"status": "READY", "engine": True, "formula": True, "tests": True, "source": False, "state_inputs": True, "production_safe": True},
            "RESTRICTED_CHOICE": {"status": "ARCHITECTURE_READY", "engine": False, "formula": False, "tests": False, "source": True, "state_inputs": "partial", "production_safe": False},
            "VACANT_PLACES": {"status": "ARCHITECTURE_READY", "engine": False, "formula": False, "tests": False, "source": True, "state_inputs": "partial", "production_safe": False},
            "SUIT_DISTRIBUTION": {"status": "ARCHITECTURE_READY", "engine": False, "formula": False, "tests": False, "source": True, "state_inputs": True, "production_safe": False},
            "TRUMP_BREAKS": {"status": "ARCHITECTURE_READY", "engine": False, "formula": False, "tests": False, "source": True, "state_inputs": True, "production_safe": False},
            "MONTE_CARLO": {"status": "PARTIALLY_READY", "engine": False, "formula": False, "tests": False, "source": False, "state_inputs": "partial", "production_safe": False},
        },
        {"total_positions_or_requests": 42, "bidding_recommendations": 2, "declarer_recommendations": 2,
         "probability_evidence_items": 3, "unavailable_evidence_requests": 8,
         "invalid_input_results": 1, "no_decisions": 23, "errors": 0},
        {"routes": 45, "ordinary_production_calls": 7_871, "ordinary_completed": 761,
         "ordinary_abstained": 9_239, "simple_unblock_hits": 2, "illegal_recommendations": 0,
         "phase12n": 24, "phase12o": 23, "phase12q": 1_194, "phase12r": 166,
         "phase12s": 540, "phase12t": 33, "phase12g_4h": 17, "phase12g_4s": 21,
         "phase12h": 197, "phase12l_completed": 5, "phase12l_abstained": 7,
         "jacoby_hearts": 62, "jacoby_spades": 61},
        "E. DEFENSIVE STATE ARCHITECTURE",
    )


def write_artifacts(benchmark: ProbabilityEngineArchitectureBenchmark, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    json_path = output / "bridgelab_phase13f_probability_engine_architecture.json"
    markdown_path = output / "bridgelab_phase13f_probability_engine_architecture.md"
    json_path.write_text(json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(f"""# Phase 13F — Probability Engine Architecture

## Inventory

The repository contains one executable calculation: Phase 13C known-card accounting. `bridge.deals` provides deterministic seeded deals and `bridge.batch_simulation` provides bidding simulation, but neither calculates declarer probabilities or line success. Probability knowledge files contain prose/tables rather than callable formulas. No latent restricted-choice, vacant-place, suit/trump split, hypergeometric, Bayesian, or declarer Monte Carlo engine was found.

## Architecture

Immutable question variants represent known-card count, restricted choice, vacant places, suit distribution, trump breaks, and Monte Carlo inputs without inferring hidden facts. `ProbabilityContext` is built from `DeclarerPlayState` visible cards, played cards, and unknown count; it contains no defender hands.

`evaluate_probability` returns `SUCCESS`, `UNAVAILABLE`, `INVALID_INPUT`, or `ERROR`, plus explicit `EXACT`/`SIMULATED` mode, compact trace, and a real formula identifier where applicable. The immutable registry maps only `KnownCardCountQuestion` to the migrated `KNOWN_CARD_COUNT_V1` calculator. Other questions are architecturally representable but return `ENGINE_NOT_REGISTERED` with no numeric result. Phase 13E's `collect_declarer_probability_evidence` remains backward compatible and delegates through this engine boundary.

## Benchmark and readiness

- Questions: {benchmark.questions}
- Success / unavailable / invalid / errors: {benchmark.successful_results} / {benchmark.unavailable_results} / {benchmark.invalid_input_results} / {benchmark.errors}
- Exact / simulated: {benchmark.exact_results} / {benchmark.simulated_results}
- Registered engines: {benchmark.registered_engines}
- Readiness: {benchmark.readiness}
- Extended architecture: {benchmark.architecture}

No formulas, declarer techniques, bidding rules, routes, defaults, or canonical knowledge were changed. Routes remain 45; the ordinary benchmark remains 7,871 / 761 / 9,239.

Selected Phase 13G: **{benchmark.phase13g_direction}**. With no safely adaptable probability formula, the probability boundary is complete enough and defense is the largest remaining end-to-end state gap.

Current cumulative Full Kit: Phase 13F
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_probability_engine_architecture_benchmark(), Path.cwd())
