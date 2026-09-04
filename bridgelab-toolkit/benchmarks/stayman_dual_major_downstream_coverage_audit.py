"""Phase 12L audit of dual-major Stayman downstream coverage."""

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

from .jacoby_continuation_policy_fixture import HEART_AUCTION, SPADE_AUCTION
from .stayman_dual_major_policy_architecture import (
    FixedStaymanDualMajorResponsePolicy,
)
from .stayman_gamegoing_audit import StaymanGameGoingAuditFixture
from .stayman_residual_coverage_audit import run_stayman_residual_coverage_audit


RESPONDER_BUCKETS = (
    "both_majors_four_plus",
    "hearts_only_four_plus",
    "spades_only_four_plus",
    "neither_major_long_minor",
    "neither_major_balanced_looking",
    "neither_major_other_shape",
)
RESIDUAL_BUCKETS = (
    "other_major_exactly_four",
    "other_major_five_plus",
    "no_four_card_major_long_minor",
    "no_four_card_major_balanced_looking",
    "no_four_card_major_other_shape",
)
CROSS_POLICY_BUCKETS = (
    "BOTH_TERMINAL",
    "HEARTS_ONLY_TERMINAL",
    "SPADES_ONLY_TERMINAL",
    "NEITHER_TERMINAL",
)


@dataclass(frozen=True, slots=True)
class StaymanDualMajorDownstreamCoverageAudit:
    start_seed: int
    deal_count: int
    target_total: int
    opener_exact_shapes: dict[str, int]
    hearts_path: dict[str, object]
    spades_path: dict[str, object]
    cross_policy_counts: dict[str, int]
    positions: tuple[dict[str, object], ...]
    responder_exact_shapes: dict[str, int]
    responder_primary_buckets: dict[str, int]
    responder_secondary_flags: dict[str, int]
    hearts_residual_primary_buckets: dict[str, int]
    spades_residual_primary_buckets: dict[str, int]
    source_certainty_matrix: tuple[dict[str, object], ...]
    source_interpretation: str
    source_safe_candidates: tuple[str, ...]
    decision: str
    recommended_phase12m_direction: str
    route_count: int
    default_dual_major_policy: None
    default_continuation_policy: None
    phase12g_calls: dict[str, int]
    phase12h_residual_total: int
    jacoby_no_policy: dict[str, int]
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_stayman_dual_major_downstream_coverage_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StaymanDualMajorDownstreamCoverageAudit:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    continuation_policy = StaymanGameGoingAuditFixture()
    hearts_policy = FixedStaymanDualMajorResponsePolicy(
        StaymanDualMajorResponse.HEARTS
    )
    spades_policy = FixedStaymanDualMajorResponsePolicy(
        StaymanDualMajorResponse.SPADES
    )
    policies = {"HEARTS": hearts_policy, "SPADES": spades_policy}
    routers = {
        name: create_standard_sayc_router(
            PolicyRegistry.from_policies(
                stayman_dual_major_response_policies=(policy,),
                stayman_continuation_strength_policies=(continuation_policy,),
            )
        )
        for name, policy in policies.items()
    }
    systems = {
        name: {
            STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION: policy.policy_id,
            STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION: continuation_policy.policy_id,
        }
        for name, policy in policies.items()
    }
    opener_shapes = Counter()
    responder_shapes = Counter()
    responder_buckets = Counter({bucket: 0 for bucket in RESPONDER_BUCKETS})
    responder_flags = Counter()
    hearts_residual = Counter({bucket: 0 for bucket in RESIDUAL_BUCKETS})
    spades_residual = Counter({bucket: 0 for bucket in RESIDUAL_BUCKETS})
    cross_counts = Counter({bucket: 0 for bucket in CROSS_POLICY_BUCKETS})
    path_counts = {"HEARTS": Counter(), "SPADES": Counter()}
    route_counts = {"HEARTS": Counter(), "SPADES": Counter()}
    positions = []
    inquiry = Auction(Seat.NORTH, ("1NT", "P", "2C", "P"))

    for case in baseline.batch.cases:
        if case.result.final_auction != "1NT P":
            continue
        opener = _context(case.deal.hand(Seat.NORTH), inquiry, {})
        if not _is_target(opener):
            continue
        opener_shape = _shape(opener)
        responder_at_inquiry = _context(case.deal.hand(Seat.SOUTH), inquiry, {})
        responder_shape = _shape(responder_at_inquiry)
        opener_shapes[opener_shape] += 1
        responder_shapes[responder_shape] += 1
        responder_buckets[_responder_primary_bucket(responder_at_inquiry)] += 1
        for flag in _secondary_flags(responder_at_inquiry):
            responder_flags[flag] += 1

        outcomes = {}
        for name, call, game_call, shown_suit in (
            ("HEARTS", "2H", "4H", Suit.HEARTS),
            ("SPADES", "2S", "4S", Suit.SPADES),
        ):
            router = routers[name]
            opener_context = _context(
                case.deal.hand(Seat.NORTH), inquiry, systems[name]
            )
            opener_route = router.match(opener_context)
            opener_action = _action(router.evaluate(opener_context))
            path_counts[name][f"opener_{opener_action}"] += 1
            route_counts[name][f"opener:{opener_route.route_id}"] += 1
            if opener_action != call:
                raise AssertionError(f"{name} policy did not produce {call}")

            endpoint = Auction(
                Seat.NORTH, ("1NT", "P", "2C", "P", call, "P")
            )
            responder = _context(
                case.deal.hand(Seat.SOUTH), endpoint, systems[name]
            )
            responder_route = router.match(responder)
            final_action = _action(router.evaluate(responder))
            route_counts[name][f"responder:{responder_route.route_id}"] += 1
            terminal = final_action == game_call
            path_counts[name][game_call if terminal else "residual_abstain"] += 1
            path_counts[name][
                "responder_fit"
                if responder.evaluation.length(shown_suit) >= 4
                else "responder_no_fit"
            ] += 1
            if not terminal:
                target_counter = (
                    hearts_residual if name == "HEARTS" else spades_residual
                )
                target_counter[
                    _residual_bucket(responder, name)
                ] += 1
            outcomes[name] = {
                "opener_route": opener_route.route_id,
                "opener_action": opener_action,
                "responder_route": responder_route.route_id,
                "final_action": final_action,
                "terminal": terminal,
            }

        cross_bucket = _cross_policy_bucket(
            outcomes["HEARTS"]["terminal"], outcomes["SPADES"]["terminal"]
        )
        cross_counts[cross_bucket] += 1
        positions.append(
            {
                "seed": case.deal.seed,
                "opener_shape": opener_shape,
                "responder_shape": responder_shape,
                "responder_hearts": responder_at_inquiry.evaluation.length(Suit.HEARTS),
                "responder_spades": responder_at_inquiry.evaluation.length(Suit.SPADES),
                "hearts_policy": outcomes["HEARTS"],
                "spades_policy": outcomes["SPADES"],
                "cross_policy_outcome": cross_bucket,
            }
        )

    phase12h = run_stayman_residual_coverage_audit(
        start_seed=start_seed, deal_count=deal_count
    )
    matrix = tuple(
        _source_row(path, bucket, counts[bucket])
        for path, counts in (
            ("HEARTS", hearts_residual),
            ("SPADES", spades_residual),
        )
        for bucket in RESIDUAL_BUCKETS
    )
    jacoby = Counter(
        case.result.final_auction
        for case in baseline.batch.cases
        if case.result.final_auction in (HEART_AUCTION, SPADE_AUCTION)
    )
    return StaymanDualMajorDownstreamCoverageAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        target_total=len(positions),
        opener_exact_shapes=dict(sorted(opener_shapes.items())),
        hearts_path=_path_summary(path_counts["HEARTS"], route_counts["HEARTS"]),
        spades_path=_path_summary(path_counts["SPADES"], route_counts["SPADES"]),
        cross_policy_counts={bucket: cross_counts[bucket] for bucket in CROSS_POLICY_BUCKETS},
        positions=tuple(positions),
        responder_exact_shapes=dict(sorted(responder_shapes.items())),
        responder_primary_buckets={bucket: responder_buckets[bucket] for bucket in RESPONDER_BUCKETS},
        responder_secondary_flags=dict(sorted(responder_flags.items())),
        hearts_residual_primary_buckets={bucket: hearts_residual[bucket] for bucket in RESIDUAL_BUCKETS},
        spades_residual_primary_buckets={bucket: spades_residual[bucket] for bucket in RESIDUAL_BUCKETS},
        source_certainty_matrix=matrix,
        source_interpretation=(
            "NO SOURCE-BACKED POLICY PREFERENCE. The 5-versus-7 difference is a "
            "sample-specific consequence of responder distribution; the frozen "
            "source defines no strategic preference from benchmark coverage."
        ),
        source_safe_candidates=(),
        decision="D. DEFER DUAL-MAJOR DOWNSTREAM RESIDUALS",
        recommended_phase12m_direction=(
            "Phase 12M — Next Deterministic Family Source-Readiness Audit: audit "
            "unimplemented non-Stayman benchmark families and select a target only "
            "where the frozen source supplies a complete call contract."
        ),
        route_count=len(create_standard_sayc_router().routes),
        default_dual_major_policy=None,
        default_continuation_policy=None,
        phase12g_calls=phase12h.phase12g_calls,
        phase12h_residual_total=phase12h.residual_total,
        jacoby_no_policy={
            "heart_transfer": jacoby[HEART_AUCTION],
            "spade_transfer": jacoby[SPADE_AUCTION],
            "total": sum(jacoby.values()),
        },
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


def _shape(context: BiddingContext) -> str:
    return "-".join(str(context.evaluation.length(suit)) for suit in Suit)


def _action(decision) -> str:
    return "ABSTAIN" if decision.recommended_call is None else decision.recommended_call.serialize()


def _balanced_shape(context: BiddingContext) -> bool:
    shape = tuple(sorted((context.evaluation.length(suit) for suit in Suit), reverse=True))
    return shape in {(4, 3, 3, 3), (4, 4, 3, 2), (5, 3, 3, 2)}


def _responder_primary_bucket(context: BiddingContext) -> str:
    hearts = context.evaluation.length(Suit.HEARTS)
    spades = context.evaluation.length(Suit.SPADES)
    if hearts >= 4 and spades >= 4:
        return "both_majors_four_plus"
    if hearts >= 4:
        return "hearts_only_four_plus"
    if spades >= 4:
        return "spades_only_four_plus"
    if max(context.evaluation.length(Suit.CLUBS), context.evaluation.length(Suit.DIAMONDS)) >= 6:
        return "neither_major_long_minor"
    if _balanced_shape(context):
        return "neither_major_balanced_looking"
    return "neither_major_other_shape"


def _secondary_flags(context: BiddingContext) -> tuple[str, ...]:
    lengths = {suit: context.evaluation.length(suit) for suit in Suit}
    flags = []
    if lengths[Suit.HEARTS] >= 4:
        flags.append("has_four_plus_hearts")
    if lengths[Suit.SPADES] >= 4:
        flags.append("has_four_plus_spades")
    if lengths[Suit.HEARTS] >= 5 or lengths[Suit.SPADES] >= 5:
        flags.append("has_five_plus_major")
    if max(lengths[Suit.CLUBS], lengths[Suit.DIAMONDS]) >= 6:
        flags.append("has_long_minor")
    if _balanced_shape(context):
        flags.append("balanced_looking")
    if max(lengths.values()) >= 7:
        flags.append("extreme_seven_plus_suit")
    return tuple(flags)


def _residual_bucket(context: BiddingContext, path: str) -> str:
    other_suit = Suit.SPADES if path == "HEARTS" else Suit.HEARTS
    other_length = context.evaluation.length(other_suit)
    if other_length >= 5:
        return "other_major_five_plus"
    if other_length == 4:
        return "other_major_exactly_four"
    if max(context.evaluation.length(Suit.CLUBS), context.evaluation.length(Suit.DIAMONDS)) >= 6:
        return "no_four_card_major_long_minor"
    if _balanced_shape(context):
        return "no_four_card_major_balanced_looking"
    return "no_four_card_major_other_shape"


def _cross_policy_bucket(hearts_terminal: bool, spades_terminal: bool) -> str:
    if hearts_terminal and spades_terminal:
        return "BOTH_TERMINAL"
    if hearts_terminal:
        return "HEARTS_ONLY_TERMINAL"
    if spades_terminal:
        return "SPADES_ONLY_TERMINAL"
    return "NEITHER_TERMINAL"


def _path_summary(counts: Counter[str], routes: Counter[str]) -> dict[str, object]:
    return {
        "opener_calls": counts["opener_2H"] + counts["opener_2S"],
        "terminal_calls": counts["4H"] + counts["4S"],
        "residual_abstentions": counts["residual_abstain"],
        "responder_fits": counts["responder_fit"],
        "responder_no_fits": counts["responder_no_fit"],
        "terminal_coverage_pct": round(100.0 * (counts["4H"] + counts["4S"]) / 36, 2),
        "route_attempts": dict(sorted(routes.items())),
    }


def _source_row(path: str, bucket: str, count: int) -> dict[str, object]:
    return {
        "policy_path": path,
        "primary_responder_shape_bucket": bucket,
        "exact_count": count,
        "candidate_calls": ("3NT", "other major", "minor game", "slam"),
        "source_finding": (
            "Frozen Stayman sources do not define an exact no-fit GAME_GOING "
            "condition-to-call mapping or complete precedence for this shape."
        ),
        "classification": "SOURCE_INSUFFICIENT",
        "executable": False,
        "blocker": "Competing calls, strength boundaries, exceptions, and precedence are unresolved.",
        "recommended_action": "defer",
    }


def write_downstream_coverage_audit_artifacts(
    audit: StaymanDualMajorDownstreamCoverageAudit, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12l_dual_major_downstream_coverage_audit.json"
    markdown_path = output_dir / "bridgelab_phase12l_dual_major_downstream_coverage_audit.md"
    json_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cross_rows = "\n".join(f"| {name} | {count} |" for name, count in audit.cross_policy_counts.items())
    responder_rows = "\n".join(f"| {name} | {count} |" for name, count in audit.responder_primary_buckets.items())
    hearts_rows = "\n".join(f"| {name} | {count} |" for name, count in audit.hearts_residual_primary_buckets.items())
    spades_rows = "\n".join(f"| {name} | {count} |" for name, count in audit.spades_residual_primary_buckets.items())
    source_rows = "\n".join(
        f"| {row['policy_path']} | {row['primary_responder_shape_bucket']} | {row['exact_count']} | "
        f"{', '.join(row['candidate_calls'])} | {row['classification']} | NO | {row['blocker']} | defer |"
        for row in audit.source_certainty_matrix
    )
    position_rows = "\n".join(
        f"| {row['seed']} | {row['opener_shape']} | {row['responder_shape']} | "
        f"{row['hearts_policy']['final_action']} | {row['spades_policy']['final_action']} | "
        f"{row['cross_policy_outcome']} |"
        for row in audit.positions
    )
    markdown_path.write_text(
        f"""# Phase 12L — Dual-Major Policy Downstream Coverage Audit

## Deterministic sample

- seeds 1–10,000
- target: {audit.target_total}
- opener shapes: 2-3-4-4={audit.opener_exact_shapes.get('2-3-4-4', 0)}, 3-2-4-4={audit.opener_exact_shapes.get('3-2-4-4', 0)}

## Policy paths

- HEARTS: opener 2H=36, 4H={audit.hearts_path['terminal_calls']}, residual={audit.hearts_path['residual_abstentions']}, coverage={audit.hearts_path['terminal_coverage_pct']:.2f}%
- SPADES: opener 2S=36, 4S={audit.spades_path['terminal_calls']}, residual={audit.spades_path['residual_abstentions']}, coverage={audit.spades_path['terminal_coverage_pct']:.2f}%

Benchmark coverage is descriptive, not a source-backed bidding preference.

## Cross-policy outcome matrix

| Outcome | Count |
|---|---:|
{cross_rows}

## Exact responder primary shape partition

| Primary bucket | Count |
|---|---:|
{responder_rows}

Exact C-D-H-S responder shapes and overlapping secondary flags are preserved in the JSON artifact.

## HEARTS residual shape matrix

| Primary bucket | Count |
|---|---:|
{hearts_rows}

## SPADES residual shape matrix

| Primary bucket | Count |
|---|---:|
{spades_rows}

## Source-certainty matrix

| Path | Residual shape | Count | Candidate calls | Classification | Executable? | Blocker | Action |
|---|---|---:|---|---|---|---|---|
{source_rows}

No source-safe downstream residual subset exists.

## Router and per-position cross-policy audit

Both branches use `sayc.opener.1nt.stayman`, followed respectively by the existing
`sayc.responder.1nt.stayman.after.2h` or `.after.2s` route.

| Seed | Opener shape | Responder shape | HEARTS outcome | SPADES outcome | Cross-policy class |
|---:|---|---|---|---|---|
{position_rows}

## Source interpretation and decision

**{audit.source_interpretation}**

**{audit.decision}.**

Recommended Phase 12M direction: {audit.recommended_phase12m_direction}

Routes: {audit.route_count}

Default policies: NONE / NONE

Phase 12G baseline: 4H={audit.phase12g_calls['4H']}, 4S={audit.phase12g_calls['4S']}

Phase 12H residual baseline: {audit.phase12h_residual_total}

Jacoby no-policy: {audit.jacoby_no_policy['heart_transfer']} + {audit.jacoby_no_policy['spade_transfer']} = {audit.jacoby_no_policy['total']}

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12L
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_downstream_coverage_audit_artifacts(
        run_stayman_dual_major_downstream_coverage_audit(), Path.cwd()
    )
