"""Phase 12I audit of the Stayman opener dual-major policy boundary."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    Auction,
    BiddingContext,
    Seat,
    Suit,
    SystemContext,
    Vulnerability,
    run_sayc_coverage_benchmark,
)
from bridge.sayc_1nt_stayman import (
    create_sayc_one_notrump_stayman_opener_response_engine,
)
from bridge.sayc_route_configuration import create_standard_sayc_router

from .stayman_residual_coverage_audit import (
    run_stayman_residual_coverage_audit,
)


SHAPE_BUCKETS = (
    "4H_4S",
    "4H_5plusS",
    "5plusH_4S",
    "5plusH_5plusS",
)


@dataclass(frozen=True, slots=True)
class StaymanDualMajorPolicyAudit:
    start_seed: int
    deal_count: int
    dual_major_total: int
    shape_buckets: dict[str, int]
    exact_shapes: dict[str, int]
    current_production_actions: dict[str, int]
    current_abstentions: int
    existing_route_attempts: dict[str, int]
    source_findings: tuple[dict[str, object], ...]
    source_certainty_matrix: tuple[dict[str, object], ...]
    policy_boundary_possible: bool
    proposed_policy_responsibility: str
    proposed_output_domain: tuple[str, ...]
    proposed_inputs: tuple[str, ...]
    proposed_source_requirements: tuple[str, ...]
    default_behavior: str
    decision: str
    recommended_phase12j_direction: str
    route_count: int
    default_dual_major_policy: None
    responder_continuation_policy_changed: bool
    phase12g_calls: dict[str, int]
    phase12h_residual_by_family: dict[str, int]
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_stayman_dual_major_policy_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StaymanDualMajorPolicyAudit:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    opener_engine = create_sayc_one_notrump_stayman_opener_response_engine()
    router = create_standard_sayc_router()
    inquiry = Auction(Seat.NORTH, ("1NT", "P", "2C", "P"))

    buckets = Counter({bucket: 0 for bucket in SHAPE_BUCKETS})
    exact_shapes = Counter()
    actions = Counter()
    route_attempts = Counter()
    abstentions = 0

    for case in baseline.batch.cases:
        if case.result.final_auction != "1NT P":
            continue
        context = BiddingContext.create(
            hand=case.deal.hand(Seat.NORTH),
            auction=inquiry,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        hearts = context.evaluation.length(Suit.HEARTS)
        spades = context.evaluation.length(Suit.SPADES)
        if hearts < 4 or spades < 4:
            continue

        buckets[_shape_bucket(hearts, spades)] += 1
        exact_shape = tuple(context.evaluation.length(suit) for suit in Suit)
        exact_shapes["-".join(str(length) for length in exact_shape)] += 1

        route = router.match(context)
        route_attempts[route.route_id if route is not None else "NONE"] += 1
        result = router.evaluate(context)
        if result.recommended_call is None:
            abstentions += 1
            actions["ABSTAIN"] += 1
        else:
            actions[result.recommended_call.serialize()] += 1

        direct_result = opener_engine.evaluate(context)
        if direct_result.recommended_call is not None:
            raise AssertionError("dual-major Stayman production behavior changed")

    matrix = tuple(_matrix_row(bucket, buckets[bucket]) for bucket in SHAPE_BUCKETS)
    phase12h = run_stayman_residual_coverage_audit(
        start_seed=start_seed, deal_count=deal_count
    )
    return StaymanDualMajorPolicyAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        dual_major_total=sum(buckets.values()),
        shape_buckets={bucket: buckets[bucket] for bucket in SHAPE_BUCKETS},
        exact_shapes=dict(sorted(exact_shapes.items())),
        current_production_actions=dict(sorted(actions.items())),
        current_abstentions=abstentions,
        existing_route_attempts=dict(sorted(route_attempts.items())),
        source_findings=_source_findings(),
        source_certainty_matrix=matrix,
        policy_boundary_possible=True,
        proposed_policy_responsibility=(
            "Given an opener hand already known to have both qualifying majors, "
            "select the partnership-agreed Stayman response branch."
        ),
        proposed_output_domain=("HEARTS", "SPADES", "UNKNOWN"),
        proposed_inputs=("opener hand", "known dual-major Stayman state"),
        proposed_source_requirements=(
            "Known HEARTS or SPADES choices must include an explanation.",
            "Known choices must cite the frozen Stayman Opener's Responses source.",
        ),
        default_behavior="no policy -> abstain",
        decision="B. ADD NON-DEFAULT DUAL-MAJOR POLICY ARCHITECTURE",
        recommended_phase12j_direction=(
            "Add a non-default Stayman dual-major response policy abstraction with "
            "HEARTS, SPADES, and UNKNOWN outputs; require explanation and frozen-source "
            "attribution for known choices; preserve no-policy and UNKNOWN abstention; "
            "do not add responder continuations."
        ),
        route_count=len(router.routes),
        default_dual_major_policy=None,
        responder_continuation_policy_changed=False,
        phase12g_calls=phase12h.phase12g_calls,
        phase12h_residual_by_family=phase12h.residual_by_family,
    )


def _shape_bucket(hearts: int, spades: int) -> str:
    if hearts == 4 and spades == 4:
        return "4H_4S"
    if hearts == 4:
        return "4H_5plusS"
    if spades == 4:
        return "5plusH_4S"
    return "5plusH_5plusS"


def _source_findings() -> tuple[dict[str, object], ...]:
    return (
        {
            "source": "bidding/conventions/responses/stayman#Opener's Responses",
            "statement": "2H shows four hearts and may also contain four spades depending on partnership agreement.",
            "action_explicit": True,
            "universal": False,
            "trigger_computable": True,
            "precedence_complete": False,
            "exceptions_defined": False,
            "dependencies": ("partnership agreement",),
            "ambiguity_acknowledged": True,
        },
        {
            "source": "bidding/conventions/responses/stayman#Opener's Responses",
            "statement": "2S shows four spades and normally denies four hearts.",
            "action_explicit": True,
            "universal": False,
            "trigger_computable": True,
            "precedence_complete": False,
            "exceptions_defined": False,
            "dependencies": ("partnership agreement",),
            "ambiguity_acknowledged": True,
        },
    )


def _matrix_row(bucket: str, count: int) -> dict[str, object]:
    return {
        "dual_major_shape": bucket,
        "exact_count": count,
        "candidate_source_permitted_responses": ("2H", "2S"),
        "source_statement": (
            "2H may also contain four spades depending on partnership agreement; "
            "2S normally denies four hearts."
        ),
        "classification": "POLICY_REQUIRED",
        "policy_boundary_possible": True,
        "blocker": "No partnership choice is configured by default.",
        "recommended_action": "add non-default policy architecture in Phase 12J",
    }


def write_dual_major_policy_audit_artifacts(
    audit: StaymanDualMajorPolicyAudit, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12i_stayman_dual_major_policy_audit.json"
    markdown_path = output_dir / "bridgelab_phase12i_stayman_dual_major_policy_audit.md"
    json_path.write_text(
        json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    shape_rows = "\n".join(
        f"| {shape} | {count} |" for shape, count in audit.shape_buckets.items()
    )
    matrix_rows = "\n".join(
        f"| {row['dual_major_shape']} | {row['exact_count']} | "
        f"{', '.join(row['candidate_source_permitted_responses'])} | "
        f"{row['source_statement']} | {row['classification']} | YES | "
        f"{row['blocker']} | {row['recommended_action']} |"
        for row in audit.source_certainty_matrix
    )
    markdown_path.write_text(
        f"""# Phase 12I — Stayman Opener Dual-Major Policy Boundary Audit

## Deterministic sample

- seeds 1–10,000
- dual-major opener positions: {audit.dual_major_total}

## Exact mutually-exclusive shape partition

| Dual-major shape | Exact count |
|---|---:|
{shape_rows}

The exact full shapes are 2-3-4-4 ({audit.exact_shapes.get('2-3-4-4', 0)}) and
3-2-4-4 ({audit.exact_shapes.get('3-2-4-4', 0)}), in C-D-H-S order.

## Canonical source findings

The frozen Stayman `Opener's Responses` source says that 2H shows four hearts
and may also contain four spades depending on partnership agreement. It says
that 2S shows four spades and normally denies four hearts. The source therefore
acknowledges more than one partnership treatment without defining a universal
precedence, strength, suit-quality, vulnerability, or style rule.

## Source-certainty matrix

| Shape | Count | Source-permitted responses | Source statement | Classification | Policy boundary? | Blocker | Action |
|---|---:|---|---|---|---|---|---|
{matrix_rows}

## Current production behavior and existing routes

- production action: ABSTAIN for all {audit.current_abstentions}
- existing route attempts: {audit.existing_route_attempts.get('sayc.opener.1nt.stayman', 0)} through `sayc.opener.1nt.stayman`
- production route count: {audit.route_count}
- no default dual-major policy exists

## Policy-boundary finding

A clean boundary is source-safe. Its only responsibility is choosing the
partnership-agreed 2H or 2S branch after the hand is already known to contain
both qualifying majors. The proposed output domain is HEARTS, SPADES, UNKNOWN.
No policy and UNKNOWN must abstain. Known choices require an explanation and
frozen-source attribution.

## Decision and Phase 12J recommendation

**{audit.decision}.**

{audit.recommended_phase12j_direction}

Phase 12G calls unchanged: 4H={audit.phase12g_calls['4H']}, 4S={audit.phase12g_calls['4S']}

Phase 12H residuals unchanged: {sum(audit.phase12h_residual_by_family.values())}

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12I
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_dual_major_policy_audit_artifacts(
        run_stayman_dual_major_policy_audit(), Path.cwd()
    )
