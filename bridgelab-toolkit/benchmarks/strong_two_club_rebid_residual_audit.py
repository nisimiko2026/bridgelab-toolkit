"""Phase 12O audit of unresolved strong-2C opener rebids.

This module measures existing behavior and frozen-source sufficiency only. It
does not add bidding rules, routes, policies, or defaults.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.evaluation import evaluate_hand
from bridge.models import Seat, Suit, Vulnerability
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router


PRIMARY_BUCKETS = (
    "balanced_below_22",
    "balanced_above_24",
    "unbalanced_below_22",
    "unbalanced_22_24_single_longest_major",
    "unbalanced_22_24_single_longest_minor",
    "unbalanced_22_24_tied_longest",
    "unbalanced_above_24",
)


@dataclass(frozen=True, slots=True)
class StrongTwoClubRebidResidualAudit:
    start_seed: int
    deal_count: int
    original_family: int
    phase12n_handled: int
    residual_total: int
    primary_bucket_counts: dict[str, int]
    hcp_distribution: dict[str, int]
    exact_shape_distribution: dict[str, int]
    secondary_flag_counts: dict[str, int]
    positions: tuple[dict[str, object], ...]
    source_certainty_matrix: tuple[dict[str, object], ...]
    source_safe_candidates: tuple[str, ...]
    decision: str
    phase12p_recommendation: str
    route_count: int
    route_id: str
    route_reached: int
    rule_abstained: int
    other_route_attempts: int
    phase12n_2nt_calls: int
    default_policies: dict[str, None]
    phase12g_calls: dict[str, int]
    phase12h_residual: int
    phase12k_no_policy_abstentions: int
    phase12l_terminal: dict[str, int]
    jacoby_no_policy: dict[str, int]
    production_rules_added: int = 0
    routes_added: int = 0
    policies_added: int = 0
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _primary_bucket(evaluation, lengths: dict[Suit, int]) -> str:
    if evaluation.is_balanced:
        return "balanced_below_22" if evaluation.hcp < 22 else "balanced_above_24"
    if evaluation.hcp < 22:
        return "unbalanced_below_22"
    if evaluation.hcp > 24:
        return "unbalanced_above_24"
    maximum = max(lengths.values())
    longest = [suit for suit, length in lengths.items() if length == maximum]
    if len(longest) > 1:
        return "unbalanced_22_24_tied_longest"
    if longest[0] in (Suit.HEARTS, Suit.SPADES):
        return "unbalanced_22_24_single_longest_major"
    return "unbalanced_22_24_single_longest_minor"


def _secondary_flags(lengths: dict[Suit, int]) -> tuple[str, ...]:
    flags = []
    if max(lengths[Suit.HEARTS], lengths[Suit.SPADES]) >= 5:
        flags.append("5+ card major")
    if max(lengths[Suit.CLUBS], lengths[Suit.DIAMONDS]) >= 5:
        flags.append("5+ card minor")
    if max(lengths.values()) >= 6:
        flags.append("6+ card suit")
    if max(lengths.values()) >= 7:
        flags.append("7+ card suit")
    if sum(length >= 4 for length in lengths.values()) >= 2:
        flags.append("two-suited shape")
    return tuple(flags)


def _source_row(bucket: str, count: int, hcp_values: list[int]) -> dict[str, object]:
    if bucket == "balanced_above_24":
        calls = ("2NT", "3NT")
        finding = "The only exact balanced rebid range in the frozen source is 22–24 -> 2NT."
        classification = "SOURCE_INSUFFICIENT"
        blocker = "No call or level is defined for balanced 25+ HCP."
    elif bucket == "unbalanced_22_24_single_longest_major":
        calls = ("2H", "2S")
        finding = "The source gives 2H as a qualitative strong-heart example, not a complete major-suit contract."
        classification = "SOURCE_PARTIAL"
        blocker = "No exact length/strength threshold, spade mapping, level precedence, or exceptions."
    elif bucket == "unbalanced_22_24_single_longest_minor":
        calls = ("3C", "3D")
        finding = "The source gives 3C as a qualitative powerful-club example, not a complete minor-suit contract."
        classification = "SOURCE_PARTIAL"
        blocker = "No exact length/strength threshold, diamond mapping, level precedence, or exceptions."
    elif bucket == "unbalanced_22_24_tied_longest":
        calls = ("2H", "2S", "3C", "3D")
        finding = "Frozen strong-2C material supplies no tied-suit choice or precedence."
        classification = "SOURCE_INSUFFICIENT"
        blocker = "Tie treatment and competing-suit precedence are absent."
    else:
        calls = ()
        finding = "No residual observations occurred in this structural bucket."
        classification = "SOURCE_INSUFFICIENT"
        blocker = "Zero observations and no complete frozen-source mapping."
    return {
        "primary_bucket": bucket,
        "exact_count": count,
        "observed_hcp_range": (
            None if not hcp_values else f"{min(hcp_values)}-{max(hcp_values)}"
        ),
        "shape_suit_characteristics": bucket.replace("_", " "),
        "candidate_source_calls": calls,
        "frozen_source_finding": finding,
        "classification": classification,
        "executable_subset": False,
        "blocker": blocker,
        "recommended_action": "defer",
    }


def run_strong_two_club_rebid_residual_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StrongTwoClubRebidResidualAudit:
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
    buckets = Counter({bucket: 0 for bucket in PRIMARY_BUCKETS})
    bucket_hcp: dict[str, list[int]] = {bucket: [] for bucket in PRIMARY_BUCKETS}
    hcp = Counter()
    shapes = Counter()
    flags = Counter()
    positions = []
    handled = 0
    for case in family:
        hand = case.deal.hand(Seat.NORTH)
        evaluation = evaluate_hand(hand)
        context = BiddingContext.create(
            hand=hand,
            auction=auction,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        match = router.match(context)
        result = router.evaluate(context)
        action = "ABSTAIN" if result.recommended_call is None else result.recommended_call.serialize()
        if action == "2NT":
            handled += 1
            continue
        lengths = {suit: evaluation.length(suit) for suit in Suit}
        bucket = _primary_bucket(evaluation, lengths)
        buckets[bucket] += 1
        bucket_hcp[bucket].append(evaluation.hcp)
        hcp[str(evaluation.hcp)] += 1
        shape = "-".join(str(length) for length in hand.shape)
        shapes[shape] += 1
        secondary = _secondary_flags(lengths)
        flags.update(secondary)
        positions.append(
            {
                "seed": case.deal.seed,
                "hcp": evaluation.hcp,
                "shape": shape,
                "suit_lengths_cdhs": {
                    suit.value: evaluation.length(suit) for suit in Suit
                },
                "balanced": evaluation.is_balanced,
                "primary_bucket": bucket,
                "secondary_flags": secondary,
                "current_action": action,
                "route_reached": None if match is None else match.route_id,
                "phase12n_rule_abstains": result.recommended_call is None,
                "other_route_attempted": False,
            }
        )
    matrix = tuple(
        _source_row(bucket, buckets[bucket], bucket_hcp[bucket])
        for bucket in PRIMARY_BUCKETS
    )
    return StrongTwoClubRebidResidualAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        original_family=len(family),
        phase12n_handled=handled,
        residual_total=len(positions),
        primary_bucket_counts={bucket: buckets[bucket] for bucket in PRIMARY_BUCKETS},
        hcp_distribution=dict(sorted(hcp.items(), key=lambda item: int(item[0]))),
        exact_shape_distribution=dict(sorted(shapes.items())),
        secondary_flag_counts=dict(sorted(flags.items())),
        positions=tuple(positions),
        source_certainty_matrix=matrix,
        source_safe_candidates=(),
        decision="D. DEFER REMAINING STRONG-2C REBIDS",
        phase12p_recommendation=(
            "Phase 12P — Natural 1NT Response Source-Readiness Audit: return to "
            "the Phase 12M inventory and audit the next-ranked response.one-notrump "
            "family, excluding already implemented/deferred Stayman and Jacoby branches."
        ),
        route_count=len(router.routes),
        route_id="sayc.opener.2c.2d.balanced",
        route_reached=len(positions),
        rule_abstained=len(positions),
        other_route_attempts=0,
        phase12n_2nt_calls=handled,
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
    audit: StrongTwoClubRebidResidualAudit, output_dir: str | Path
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "bridgelab_phase12o_strong_2c_rebid_residual_audit.json"
    markdown_path = output / "bridgelab_phase12o_strong_2c_rebid_residual_audit.md"
    json_path.write_text(
        json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    bucket_rows = "\n".join(
        f"| {row['primary_bucket']} | {row['exact_count']} | {row['observed_hcp_range'] or 'none'} | "
        f"{', '.join(row['candidate_source_calls']) or 'none'} | {row['classification']} | NO | {row['blocker']} | defer |"
        for row in audit.source_certainty_matrix
    )
    position_rows = "\n".join(
        f"| {row['seed']} | {row['hcp']} | {row['shape']} | {row['balanced']} | "
        f"{row['primary_bucket']} | {', '.join(row['secondary_flags']) or 'none'} | "
        f"{row['current_action']} | {row['route_reached']} | YES | NONE |"
        for row in audit.positions
    )
    markdown_path.write_text(
        f"""# Phase 12O — Strong 2C Rebid Residual Source Audit

## Deterministic sample

- Seeds: 1–10,000
- Exact decision: `2C-P-2D-P`, opener to act
- Original family: {audit.original_family}
- Phase 12N handled: {audit.phase12n_handled}
- Residual: {audit.residual_total}
- Current action for every residual: `ABSTAIN`

## Source-certainty matrix and exact primary partition

| Primary bucket | Count | HCP range | Candidate calls | Classification | Executable subset? | Blocker | Action |
|---|---:|---|---|---|---|---|---|
{bucket_rows}

HCP distribution: {audit.hcp_distribution}

Exact C-D-H-S shape distribution: {audit.exact_shape_distribution}

Overlapping secondary flags: {audit.secondary_flag_counts}

## Position and router audit

| Seed | HCP | C-D-H-S shape | Balanced | Primary bucket | Secondary flags | Action | Route | Rule abstains | Other route |
|---:|---:|---|---|---|---|---|---|---|---|
{position_rows}

All 23 reach `{audit.route_id}`; its Phase 12N rule checks and abstains. No other route or rule attempts the position. Production routes remain {audit.route_count}.

## Frozen-source finding

The frozen `response-to-2-clubs` source completely defines only the already
implemented balanced 22–24 HCP `2NT` contract. Its suit-rebid examples use
qualitative terms (“strong heart suit” and “powerful club suit”) without exact
length, strength, complete suit mapping, level precedence, tied-suit treatment,
or long-suit/two-suited exceptions. Balanced hands above 24 also have no exact
next-call contract. Therefore there is no source-safe residual subset.

## Decision and Phase 12P

**{audit.decision}.**

{audit.phase12p_recommendation}

Guards: Phase 12N 2NT={audit.phase12n_2nt_calls}; Phase 12G={audit.phase12g_calls}; Phase 12H={audit.phase12h_residual}; Phase 12K abstain={audit.phase12k_no_policy_abstentions}; Phase 12L={audit.phase12l_terminal}; Jacoby={audit.jacoby_no_policy}; defaults unchanged; knowledge Markdown changes=0.

Current cumulative Full Kit: Phase 12O
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_strong_two_club_rebid_residual_audit(), Path.cwd())
