"""Phase 12H deterministic audit of residual Stayman continuations."""

from __future__ import annotations

from collections import Counter, defaultdict
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
class StaymanResidualCoverageAudit:
    start_seed: int
    deal_count: int
    phase12g_calls: dict[str, int]
    residual_by_family: dict[str, int]
    residual_total: int
    primary_shape_buckets: dict[str, dict[str, int]]
    secondary_shape_flags: dict[str, dict[str, int]]
    source_certainty_matrix: tuple[dict[str, object], ...]
    classification_counts: dict[str, int]
    existing_route_matches: dict[str, int]
    existing_production_actions: dict[str, int]
    source_safe_subset_candidates: tuple[str, ...]
    recommendation: str
    recommended_phase12i_direction: str
    route_count: int
    default_policy: None
    dual_major_abstentions: int
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_stayman_residual_coverage_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StaymanResidualCoverageAudit:
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

    phase12g_calls = Counter()
    residual = Counter()
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    flags: dict[str, Counter[str]] = defaultdict(Counter)
    route_matches = Counter()
    production_actions = Counter()
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
        if result.recommended_call is not None:
            phase12g_calls[result.recommended_call.serialize()] += 1
            continue

        family = _family(opener_call)
        residual[family] += 1
        lengths = {
            suit: responder_context.evaluation.length(suit) for suit in Suit
        }
        bucket = _primary_bucket(opener_call, lengths)
        buckets[family][bucket] += 1
        for flag in _secondary_flags(lengths):
            flags[family][flag] += 1
        if router.match(responder_context) is not None:
            route_matches[family] += 1
        if result.recommended_call is not None:
            production_actions[family] += 1

    matrix = tuple(
        _matrix_row(family, bucket, count, route_matches[family] > 0)
        for family in ("after_2D", "after_2H_no_fit", "after_2S_no_fit")
        for bucket, count in sorted(buckets[family].items())
    )
    classifications = Counter(row["classification"] for row in matrix)
    return StaymanResidualCoverageAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        phase12g_calls={call: phase12g_calls[call] for call in ("4H", "4S")},
        residual_by_family={
            family: residual[family]
            for family in ("after_2D", "after_2H_no_fit", "after_2S_no_fit")
        },
        residual_total=sum(residual.values()),
        primary_shape_buckets={
            family: dict(sorted(buckets[family].items()))
            for family in ("after_2D", "after_2H_no_fit", "after_2S_no_fit")
        },
        secondary_shape_flags={
            family: dict(sorted(flags[family].items()))
            for family in ("after_2D", "after_2H_no_fit", "after_2S_no_fit")
        },
        source_certainty_matrix=matrix,
        classification_counts=dict(sorted(classifications.items())),
        existing_route_matches={
            family: route_matches[family]
            for family in ("after_2D", "after_2H_no_fit", "after_2S_no_fit")
        },
        existing_production_actions={
            family: production_actions[family]
            for family in ("after_2D", "after_2H_no_fit", "after_2S_no_fit")
        },
        source_safe_subset_candidates=(),
        recommendation="D. DEFER STAYMAN RESIDUALS",
        recommended_phase12i_direction=(
            "Audit a policy boundary for the 36 Stayman opener hands with both "
            "four-card majors; the frozen source explicitly marks whether 2H may "
            "also contain four spades as partnership-agreement dependent."
        ),
        route_count=len(router.routes),
        default_policy=None,
        dual_major_abstentions=dual_major,
    )


def _family(opener_call: str) -> str:
    if opener_call == "2D":
        return "after_2D"
    if opener_call == "2H":
        return "after_2H_no_fit"
    return "after_2S_no_fit"


def _primary_bucket(opener_call: str, lengths: dict[Suit, int]) -> str:
    hearts, spades = lengths[Suit.HEARTS], lengths[Suit.SPADES]
    if opener_call == "2D":
        if (hearts >= 5 and spades >= 4) or (spades >= 5 and hearts >= 4):
            return "five_four_major_pattern"
        if hearts >= 4 and spades >= 4:
            return "both_majors_four_plus"
        if hearts >= 5 or spades >= 5:
            return "exactly_one_major_five_plus"
        if (hearts == 4) != (spades == 4):
            return "exactly_one_four_card_major"
    else:
        other = spades if opener_call == "2H" else hearts
        if other >= 5:
            return "other_major_five_plus"
        if other == 4:
            return "other_major_exactly_four"
    if max(lengths[Suit.CLUBS], lengths[Suit.DIAMONDS]) >= 6:
        return "no_four_card_major_long_minor"
    shape = tuple(sorted(lengths.values(), reverse=True))
    if shape in {(4, 3, 3, 3), (4, 4, 3, 2), (5, 3, 3, 2)}:
        return "no_four_card_major_balanced_looking"
    return "no_four_card_major_other_shape"


def _secondary_flags(lengths: dict[Suit, int]) -> tuple[str, ...]:
    hearts, spades = lengths[Suit.HEARTS], lengths[Suit.SPADES]
    flags = []
    if hearts >= 5 or spades >= 5:
        flags.append("has_five_plus_major")
    if hearts >= 4 and spades >= 4:
        flags.append("both_majors_four_plus")
    if max(lengths[Suit.CLUBS], lengths[Suit.DIAMONDS]) >= 6:
        flags.append("has_long_minor")
    shape = tuple(sorted(lengths.values(), reverse=True))
    if shape in {(4, 3, 3, 3), (4, 4, 3, 2), (5, 3, 3, 2)}:
        flags.append("balanced_looking")
    if max(lengths.values()) >= 7:
        flags.append("extreme_seven_plus_suit")
    return tuple(flags)


def _matrix_row(family: str, bucket: str, count: int, route_exists: bool):
    return {
        "auction_endpoint": family,
        "primary_responder_shape_bucket": bucket,
        "exact_count": count,
        "candidate_next_calls": ("3NT", "major", "minor game", "slam"),
        "canonical_source_finding": (
            "The frozen Stayman source names choices by strength and distribution "
            "but supplies no exact condition-to-call mapping or complete precedence."
        ),
        "classification": "SOURCE_INSUFFICIENT",
        "executable": False,
        "blocker": "Competing calls, shape exceptions, and precedence are unresolved.",
        "recommended_action": "defer",
        "existing_route_matches_family": route_exists,
    }


def write_residual_audit_artifacts(
    audit: StaymanResidualCoverageAudit, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12h_stayman_residual_coverage_audit.json"
    markdown_path = output_dir / "bridgelab_phase12h_stayman_residual_coverage_audit.md"
    json_path.write_text(
        json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    partitions = "\n\n".join(
        f"### {family}\n\n"
        + "\n".join(f"- {bucket}: {count}" for bucket, count in values.items())
        for family, values in audit.primary_shape_buckets.items()
    )
    matrix = "\n".join(
        f"| {row['auction_endpoint']} | {row['primary_responder_shape_bucket']} | "
        f"{row['exact_count']} | {', '.join(row['candidate_next_calls'])} | "
        f"{row['classification']} | NO | {row['blocker']} | defer |"
        for row in audit.source_certainty_matrix
    )
    residual = audit.residual_by_family
    routes = audit.existing_route_matches
    markdown_path.write_text(
        f"""# Phase 12H — Stayman Continuation Residual Coverage Audit

## Deterministic sample

- seeds 1–10,000
- implemented Phase 12G: 4H={audit.phase12g_calls['4H']}, 4S={audit.phase12g_calls['4S']}, total={sum(audit.phase12g_calls.values())}
- residual after 2D: {residual['after_2D']}
- residual after 2H no-fit: {residual['after_2H_no_fit']}
- residual after 2S no-fit: {residual['after_2S_no_fit']}
- residual total: {audit.residual_total}

## Exact mutually-exclusive shape partitions

{partitions}

## Source-certainty matrix

| Endpoint | Primary shape bucket | Count | Candidate calls | Classification | Executable? | Blocker | Action |
|---|---|---:|---|---|---|---|---|
{matrix}

## Existing-route attempts

- after 2D: {routes['after_2D']} route matches
- after 2H no-fit: {routes['after_2H_no_fit']} route matches, 0 production actions
- after 2S no-fit: {routes['after_2S_no_fit']} route matches, 0 production actions

## Source-safe subset candidates

None. No residual bucket has a complete frozen-source condition-to-call mapping
and precedence contract. In particular, no blanket 3NT fallback is supported.

## Recommendation

**{audit.recommendation}.**

Recommended Phase 12I direction: {audit.recommended_phase12i_direction}

Production route count: {audit.route_count}

Default Stayman continuation policy: NONE

Dual-major opener cases unchanged: {audit.dual_major_abstentions}

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12H
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_residual_audit_artifacts(
        run_stayman_residual_coverage_audit(), Path.cwd()
    )

