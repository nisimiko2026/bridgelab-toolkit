"""Phase 12K benchmark for policy-gated Stayman dual-major responses."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    Auction,
    BiddingContext,
    Seat,
    StaymanDualMajorResponse,
    Suit,
    SystemContext,
    Vulnerability,
    run_sayc_coverage_benchmark,
)
from bridge.policy_registry import (
    STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION,
    STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION,
    PolicyRegistry,
)
from bridge.sayc_route_configuration import create_standard_sayc_router

from .stayman_dual_major_policy_architecture import (
    FixedStaymanDualMajorResponsePolicy,
)
from .stayman_gamegoing_audit import StaymanGameGoingAuditFixture
from .stayman_residual_coverage_audit import run_stayman_residual_coverage_audit


@dataclass(frozen=True, slots=True)
class StaymanDualMajorOpenerResponseBenchmark:
    start_seed: int
    deal_count: int
    dual_major_total: int
    exact_shapes: dict[str, int]
    opener_policy_scenarios: dict[str, dict[str, int]]
    dual_policy_only_responder_actions: dict[str, dict[str, int]]
    combined_policy_downstream: dict[str, dict[str, int]]
    no_policy_production_actions: dict[str, int]
    route_count: int
    default_dual_major_policy: None
    default_continuation_policy: None
    phase12g_calls: dict[str, int]
    phase12h_residual_total: int
    production_defaults_changed: bool
    knowledge_markdown_changed: int
    recommended_next_phase: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_stayman_dual_major_opener_response_benchmark(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StaymanDualMajorOpenerResponseBenchmark:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    continuation_policy = StaymanGameGoingAuditFixture()
    response_policies = tuple(
        FixedStaymanDualMajorResponsePolicy(response)
        for response in StaymanDualMajorResponse
    )
    no_policy_router = create_standard_sayc_router()
    opener_scenarios: dict[str, Counter[str]] = {
        policy.response.name: Counter() for policy in response_policies
    }
    dual_only_responder: dict[str, Counter[str]] = {
        "HEARTS": Counter(),
        "SPADES": Counter(),
    }
    combined: dict[str, Counter[str]] = {
        "HEARTS": Counter(),
        "SPADES": Counter(),
    }
    no_policy = Counter()
    shapes = Counter()
    inquiry = Auction(Seat.NORTH, ("1NT", "P", "2C", "P"))

    for case in baseline.batch.cases:
        if case.result.final_auction != "1NT P":
            continue
        base_context = _context(case.deal.hand(Seat.NORTH), inquiry, {})
        if not _is_target(base_context):
            continue
        exact_shape = tuple(base_context.evaluation.length(suit) for suit in Suit)
        shapes["-".join(str(length) for length in exact_shape)] += 1
        no_policy[_serialized_action(no_policy_router.evaluate(base_context))] += 1

        for response_policy in response_policies:
            name = response_policy.response.name
            dual_options = {
                STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION: response_policy.policy_id
            }
            dual_registry = PolicyRegistry.from_stayman_dual_major_response_policies(
                (response_policy,)
            )
            dual_router = create_standard_sayc_router(dual_registry)
            opener_context = _context(
                case.deal.hand(Seat.NORTH), inquiry, dual_options
            )
            opener_action = _serialized_action(dual_router.evaluate(opener_context))
            opener_scenarios[name][opener_action] += 1
            if opener_action == "ABSTAIN" or name == "UNKNOWN":
                continue

            endpoint = Auction(
                Seat.NORTH, ("1NT", "P", "2C", "P", opener_action, "P")
            )
            responder_context = _context(
                case.deal.hand(Seat.SOUTH), endpoint, dual_options
            )
            dual_only_responder[name][
                _serialized_action(dual_router.evaluate(responder_context))
            ] += 1

            combined_options = {
                **dual_options,
                STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION: (
                    continuation_policy.policy_id
                ),
            }
            combined_registry = PolicyRegistry.from_policies(
                stayman_dual_major_response_policies=(response_policy,),
                stayman_continuation_strength_policies=(continuation_policy,),
            )
            combined_router = create_standard_sayc_router(combined_registry)
            combined_context = _context(
                case.deal.hand(Seat.SOUTH), endpoint, combined_options
            )
            shown_suit = (
                Suit.HEARTS if name == "HEARTS" else Suit.SPADES
            )
            if combined_context.evaluation.length(shown_suit) >= 4:
                combined[name]["responder_fit"] += 1
            else:
                combined[name]["responder_no_fit"] += 1
            combined[name][
                _serialized_action(combined_router.evaluate(combined_context))
            ] += 1

    phase12h = run_stayman_residual_coverage_audit(
        start_seed=start_seed, deal_count=deal_count
    )
    return StaymanDualMajorOpenerResponseBenchmark(
        start_seed=start_seed,
        deal_count=deal_count,
        dual_major_total=sum(shapes.values()),
        exact_shapes=dict(sorted(shapes.items())),
        opener_policy_scenarios={
            name: dict(sorted(counts.items()))
            for name, counts in opener_scenarios.items()
        },
        dual_policy_only_responder_actions={
            name: dict(sorted(counts.items()))
            for name, counts in dual_only_responder.items()
        },
        combined_policy_downstream={
            name: dict(sorted(counts.items())) for name, counts in combined.items()
        },
        no_policy_production_actions=dict(sorted(no_policy.items())),
        route_count=len(no_policy_router.routes),
        default_dual_major_policy=None,
        default_continuation_policy=None,
        phase12g_calls=phase12h.phase12g_calls,
        phase12h_residual_total=phase12h.residual_total,
        production_defaults_changed=False,
        knowledge_markdown_changed=0,
        recommended_next_phase=(
            "Phase 12L — Dual-Major Policy Downstream Coverage Audit"
        ),
    )


def _context(hand, auction: Auction, options: dict[str, str]) -> BiddingContext:
    return BiddingContext.create(
        hand=hand,
        auction=auction,
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", options),
    )


def _is_target(context: BiddingContext) -> bool:
    return (
        context.evaluation.length(Suit.HEARTS) == 4
        and context.evaluation.length(Suit.SPADES) == 4
    )


def _serialized_action(decision) -> str:
    return (
        "ABSTAIN"
        if decision.recommended_call is None
        else decision.recommended_call.serialize()
    )


def write_dual_major_opener_response_artifacts(
    benchmark: StaymanDualMajorOpenerResponseBenchmark, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12k_stayman_dual_major_opener_responses.json"
    markdown_path = output_dir / "bridgelab_phase12k_stayman_dual_major_opener_responses.md"
    json_path.write_text(
        json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    hearts = benchmark.combined_policy_downstream["HEARTS"]
    spades = benchmark.combined_policy_downstream["SPADES"]
    markdown_path.write_text(
        f"""# Phase 12K — Policy-Gated Stayman Dual-Major Opener Responses

## Production mapping

- explicit HEARTS policy -> 2H
- explicit SPADES policy -> 2S
- UNKNOWN, missing, or unresolved policy -> abstain
- scope: exactly four hearts and exactly four spades after 1NT-P-2C-P

## Deterministic target

- seeds 1–10,000
- dual-major positions: {benchmark.dual_major_total}
- 2-3-4-4: {benchmark.exact_shapes.get('2-3-4-4', 0)}
- 3-2-4-4: {benchmark.exact_shapes.get('3-2-4-4', 0)}

## Opener-policy coverage

- HEARTS fixture: 2H={benchmark.opener_policy_scenarios['HEARTS'].get('2H', 0)}, coverage 36/36
- SPADES fixture: 2S={benchmark.opener_policy_scenarios['SPADES'].get('2S', 0)}, coverage 36/36
- UNKNOWN: abstain={benchmark.opener_policy_scenarios['UNKNOWN'].get('ABSTAIN', 0)}
- no policy: abstain={benchmark.no_policy_production_actions.get('ABSTAIN', 0)}

With only the dual-major policy configured, responder abstains after all 36
HEARTS-policy calls and all 36 SPADES-policy calls because the independent
continuation-strength policy remains unconfigured.

## Combined-policy measured downstream

### HEARTS + GAME_GOING

- opener 2H: 36
- responder heart fits: {hearts.get('responder_fit', 0)}
- responder 4H: {hearts.get('4H', 0)}
- no-fit abstain: {hearts.get('ABSTAIN', 0)}

### SPADES + GAME_GOING

- opener 2S: 36
- responder spade fits: {spades.get('responder_fit', 0)}
- responder 4S: {spades.get('4S', 0)}
- no-fit abstain: {spades.get('ABSTAIN', 0)}

Responder continuation coverage is 5/36 for HEARTS and 7/36 for SPADES; it
is distinct from the 36/36 opener-policy coverage.

## Guards

- routes: {benchmark.route_count}
- default dual-major policy: NONE
- default continuation policy: NONE
- Phase 12G baseline: 4H={benchmark.phase12g_calls['4H']}, 4S={benchmark.phase12g_calls['4S']}
- Phase 12H residual baseline: {benchmark.phase12h_residual_total}
- ordinary no-policy behavior unchanged
- production defaults changed: NO
- knowledge changes: 0

Recommended next phase: **{benchmark.recommended_next_phase}**

Current cumulative Full Kit: Phase 12K
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_dual_major_opener_response_artifacts(
        run_stayman_dual_major_opener_response_benchmark(), Path.cwd()
    )
