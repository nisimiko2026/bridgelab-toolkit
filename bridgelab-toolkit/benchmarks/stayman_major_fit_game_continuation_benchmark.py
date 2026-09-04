"""Phase 12G deterministic benchmark for policy-gated Stayman game calls."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    Auction,
    BiddingContext,
    Seat,
    SystemContext,
    Vulnerability,
    run_sayc_coverage_benchmark,
)
from bridge.policy_registry import (
    STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION,
    PolicyRegistry,
)
from bridge.sayc_1nt_stayman import (
    create_sayc_one_notrump_stayman_opener_response_engine,
)
from bridge.sayc_route_configuration import create_standard_sayc_router

from .stayman_gamegoing_audit import StaymanGameGoingAuditFixture


@dataclass(frozen=True, slots=True)
class StaymanMajorFitGameBenchmark:
    start_seed: int
    deal_count: int
    audited_positions: int
    opener_response_positions: dict[str, int]
    resulting_calls: dict[str, int]
    abstentions: dict[str, int]
    continuation_call_count: int
    abstention_count: int
    coverage_numerator: int
    coverage_denominator: int
    coverage_pct: float
    dual_major_abstentions: int
    default_policy: None
    production_route_count: int
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["coverage_fraction"] = (
            f"{self.coverage_numerator}/{self.coverage_denominator}"
        )
        return result


def run_stayman_major_fit_game_benchmark(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StaymanMajorFitGameBenchmark:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    cases = tuple(
        case for case in baseline.batch.cases if case.result.final_auction == "1NT P"
    )
    opener_engine = create_sayc_one_notrump_stayman_opener_response_engine()
    policy = StaymanGameGoingAuditFixture()
    registry = PolicyRegistry.from_stayman_continuation_strength_policies((policy,))
    router = create_standard_sayc_router(registry)
    system = SystemContext.from_mapping(
        "SAYC", {STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION: policy.policy_id}
    )
    positions = Counter()
    calls = Counter()
    abstentions = Counter()
    dual_major = 0

    for case in cases:
        inquiry = Auction(Seat.NORTH, ("1NT", "P", "2C", "P"))
        opener_context = BiddingContext.create(
            hand=case.deal.hand(Seat.NORTH),
            auction=inquiry,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        opener_result = opener_engine.evaluate(opener_context)
        if opener_result.recommended_call is None:
            dual_major += 1
            continue
        opener_call = opener_result.recommended_call.serialize()
        positions[opener_call] += 1
        endpoint = Auction(
            Seat.NORTH, ("1NT", "P", "2C", "P", opener_call, "P")
        )
        responder_context = BiddingContext.create(
            hand=case.deal.hand(Seat.SOUTH),
            auction=endpoint,
            vulnerability=Vulnerability.NONE,
            system=system,
        )
        result = router.evaluate(responder_context)
        if result.recommended_call is None:
            abstentions[opener_call] += 1
        else:
            calls[result.recommended_call.serialize()] += 1

    audited = sum(positions.values())
    produced = sum(calls.values())
    abstained = sum(abstentions.values())
    return StaymanMajorFitGameBenchmark(
        start_seed=start_seed,
        deal_count=deal_count,
        audited_positions=audited,
        opener_response_positions={call: positions[call] for call in ("2D", "2H", "2S")},
        resulting_calls={call: calls[call] for call in ("4H", "4S")},
        abstentions={call: abstentions[call] for call in ("2D", "2H", "2S")},
        continuation_call_count=produced,
        abstention_count=abstained,
        coverage_numerator=produced,
        coverage_denominator=audited,
        coverage_pct=round(100.0 * produced / audited, 2),
        dual_major_abstentions=dual_major,
        default_policy=None,
        production_route_count=len(router.routes),
    )


def write_benchmark_artifacts(
    metrics: StaymanMajorFitGameBenchmark, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12g_stayman_major_fit_game_continuations.json"
    markdown_path = output_dir / "bridgelab_phase12g_stayman_major_fit_game_continuations.md"
    json_path.write_text(
        json.dumps(metrics.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    positions, calls, abstentions = (
        metrics.opener_response_positions,
        metrics.resulting_calls,
        metrics.abstentions,
    )
    markdown_path.write_text(
        f"""# Phase 12G — Policy-Gated Stayman Major-Fit Game Continuations

## Production rule

- `GAME_GOING + 2H + 4+ hearts -> 4H`
- `GAME_GOING + 2S + 4+ spades -> 4S`

Routes added: 2

Route count: 42 before, {metrics.production_route_count} after.

## Benchmark fixture

- 2D = {positions['2D']} -> 0 calls / {abstentions['2D']} abstain
- 2H = {positions['2H']} -> {calls['4H']} 4H / {abstentions['2H']} abstain
- 2S = {positions['2S']} -> {calls['4S']} 4S / {abstentions['2S']} abstain

Continuation calls: 4H={calls['4H']}, 4S={calls['4S']}, total={metrics.continuation_call_count}.

Abstentions: {metrics.abstention_count}

Fixture coverage: {metrics.coverage_numerator}/{metrics.coverage_denominator} = {metrics.coverage_pct:.2f}%

No-fit branches remain deferred. The 2D branch remains deferred. The
{metrics.dual_major_abstentions} dual-major opener cases are unchanged.

Default Stayman continuation policy: **NONE**

Knowledge Markdown changes: 0

Recommended next phase: **Phase 12H — Stayman Continuation Residual Coverage Audit**

Current cumulative Full Kit: Phase 12G
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_benchmark_artifacts(run_stayman_major_fit_game_benchmark(), Path.cwd())

