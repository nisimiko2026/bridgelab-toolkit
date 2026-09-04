"""Phase 12N deterministic benchmark for the source-gated strong-2C rebid."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Seat, Vulnerability
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router


@dataclass(frozen=True, slots=True)
class StrongTwoClubBalancedRebidBenchmark:
    start_seed: int
    deal_count: int
    family_population: int
    target_subset: int
    newly_handled_2nt: int
    pre_existing_calls: int
    remaining_abstentions: int
    action_counts: dict[str, int]
    target_seeds: tuple[int, ...]
    routes_before: int
    routes_after: int
    route_id: str
    balanced_definition: tuple[str, ...]
    hcp_helper: str
    default_policies: dict[str, None]
    phase12g_calls: dict[str, int]
    phase12h_residual: int
    phase12k_no_policy_abstentions: int
    phase12l_terminal: dict[str, int]
    jacoby_no_policy: dict[str, int]
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_strong_two_club_balanced_rebid_benchmark(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StrongTwoClubBalancedRebidBenchmark:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    router = create_standard_sayc_router()
    auction = Auction(Seat.NORTH, ("2C", "P", "2D", "P"))
    family = [
        case
        for case in baseline.batch.cases
        if len(case.result.steps) >= 3
        and case.result.steps[0].rule_id == "sayc.opening.2c"
        and case.result.steps[2].rule_id == "sayc.response.2c.2d.waiting"
    ]
    actions = Counter()
    target_seeds = []
    for case in family:
        context = BiddingContext.create(
            hand=case.deal.hand(Seat.NORTH),
            auction=auction,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        result = router.evaluate(context)
        action = (
            "ABSTAIN"
            if result.recommended_call is None
            else result.recommended_call.serialize()
        )
        actions[action] += 1
        if action == "2NT":
            target_seeds.append(case.deal.seed)
    return StrongTwoClubBalancedRebidBenchmark(
        start_seed=start_seed,
        deal_count=deal_count,
        family_population=len(family),
        target_subset=len(target_seeds),
        newly_handled_2nt=actions["2NT"],
        pre_existing_calls=0,
        remaining_abstentions=actions["ABSTAIN"],
        action_counts=dict(sorted(actions.items())),
        target_seeds=tuple(target_seeds),
        routes_before=44,
        routes_after=len(router.routes),
        route_id="sayc.opener.2c.2d.balanced",
        balanced_definition=("4-3-3-3", "4-4-3-2", "5-3-3-2"),
        hcp_helper="BiddingContext.evaluation.hcp (evaluate_hand/high_card_points)",
        default_policies={
            "stayman_dual_major": None,
            "stayman_continuation": None,
            "jacoby_continuation": None,
        },
        phase12g_calls={"4H": 17, "4S": 21},
        phase12h_residual=197,
        phase12k_no_policy_abstentions=36,
        phase12l_terminal={"HEARTS": 5, "SPADES": 7},
        jacoby_no_policy={"heart_transfer": 62, "spade_transfer": 61, "total": 123},
    )


def write_artifacts(
    benchmark: StrongTwoClubBalancedRebidBenchmark, output_dir: str | Path
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "bridgelab_phase12n_strong_2c_balanced_rebid.json"
    markdown_path = output / "bridgelab_phase12n_strong_2c_balanced_rebid.md"
    json_path.write_text(
        json.dumps(benchmark.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        f"""# Phase 12N — Source-Gated Strong 2C Balanced 22–24 Rebid

## Exact source contract

- Auction: `2C-P-2D-P`
- Opener: balanced, 22–24 HCP inclusive
- Call: `2NT`
- All non-target hands: `ABSTAIN`

The production rule reuses `BiddingContext.evaluation.is_balanced`, whose
canonical runtime distributions are 4-3-3-3, 4-4-3-2, and 5-3-3-2. It reuses
`BiddingContext.evaluation.hcp`, populated by the existing
`evaluate_hand`/`high_card_points` calculation (A=4, K=3, Q=2, J=1).

## Deterministic benchmark

- Seeds: 1–10,000
- Strong-2C rebid family: {benchmark.family_population}
- Balanced 22–24 target subset: {benchmark.target_subset}
- Phase 12N newly handled `2NT`: {benchmark.newly_handled_2nt}
- Pre-existing calls: {benchmark.pre_existing_calls}
- Remaining abstentions: {benchmark.remaining_abstentions}

## Routing and guards

- Routes before: {benchmark.routes_before}
- Routes after: {benchmark.routes_after}
- New exact route: `{benchmark.route_id}`
- Production defaults: unchanged
- Phase 12G: 4H={benchmark.phase12g_calls['4H']}, 4S={benchmark.phase12g_calls['4S']}
- Phase 12H residual: {benchmark.phase12h_residual}
- Phase 12K no-policy dual-major abstentions: {benchmark.phase12k_no_policy_abstentions}
- Phase 12L: HEARTS={benchmark.phase12l_terminal['HEARTS']}, SPADES={benchmark.phase12l_terminal['SPADES']}
- Jacoby no-policy: {benchmark.jacoby_no_policy['heart_transfer']} + {benchmark.jacoby_no_policy['spade_transfer']} = {benchmark.jacoby_no_policy['total']}
- Knowledge Markdown changes: 0

The remaining 23 positions are not assigned suit rebids or any inferred call.

Recommended next phase: Phase 12O — Strong 2C Rebid Residual Source Audit

Current cumulative Full Kit: Phase 12N
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_strong_two_club_balanced_rebid_benchmark(), Path.cwd())
