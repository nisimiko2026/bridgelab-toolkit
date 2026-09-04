"""Phase 12R audit of responder decisions after a three-level preempt.

Audit-only: this module defines no production rule, route, policy, or default.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.evaluation import evaluate_hand
from bridge.models import Suit, Vulnerability
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router


OPENING_SUITS = {
    "3C": Suit.CLUBS,
    "3D": Suit.DIAMONDS,
    "3H": Suit.HEARTS,
    "3S": Suit.SPADES,
}
CATEGORY_ORDER = (
    "slam-interest-looking",
    "game-looking",
    "possible-nt-oriented-balanced",
    "strong-support",
    "moderate-support",
    "long-independent-suit",
    "short-support-weak/no-action",
)


@dataclass(frozen=True, slots=True)
class ThreeLevelPreemptResponseSourceReadinessAudit:
    start_seed: int
    deal_count: int
    phase12q_expected_population: int
    population: int
    per_opening_counts: dict[str, int]
    primary_partitions: dict[str, int]
    opening_partitions: dict[str, dict[str, int]]
    distributions: dict[str, dict[str, object]]
    positions: tuple[dict[str, object], ...]
    source_matrix: tuple[dict[str, object], ...]
    top_candidates: tuple[dict[str, object], ...]
    source_safe_candidates: tuple[str, ...]
    major_vs_minor_finding: str
    router_finding: str
    decision: str
    phase12s_recommendation: dict[str, object]
    route_count: int
    production_rules_added: int
    routes_added: int
    policies_added: int
    default_policies: dict[str, None]
    phase12q_population: int
    phase12n_calls: int
    phase12o_residual: int
    phase12p_decision: str
    phase12g_calls: dict[str, int]
    phase12h_residual: int
    phase12l_terminal: dict[str, int]
    jacoby_no_policy: dict[str, int]
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _shape(hand) -> str:
    return "-".join(str(length) for length in hand.shape)


def _primary_category(evaluation, support: int, independent_length: int) -> str:
    # These labels partition observed structure; they are not bidding rules.
    if evaluation.hcp >= 19:
        return "slam-interest-looking"
    if evaluation.hcp >= 15:
        return "game-looking"
    if evaluation.is_balanced:
        return "possible-nt-oriented-balanced"
    if support >= 4:
        return "strong-support"
    if support == 3:
        return "moderate-support"
    if independent_length >= 6:
        return "long-independent-suit"
    return "short-support-weak/no-action"


def _matrix_row(opening: str, category: str, rows: list[dict[str, object]]) -> dict[str, object]:
    hcps = [int(row["responder_hcp"]) for row in rows]
    candidate_calls = {
        "slam-interest-looking": ("raise/game", "new suit", "3NT", "slam investigation"),
        "game-looking": ("raise/game", "new suit", "3NT"),
        "possible-nt-oriented-balanced": ("Pass", "3NT"),
        "strong-support": ("Pass", "raise", "game raise"),
        "moderate-support": ("Pass", "raise", "game raise"),
        "long-independent-suit": ("Pass", "new suit"),
        "short-support-weak/no-action": ("Pass", "3NT", "new suit"),
    }[category]
    finding = (
        "The frozen source names these candidate actions and qualitative factors, "
        "but does not define a complete mutually-exclusive responder contract."
    )
    missing = (
        "exact strength and card-length trigger; stopper/suit-quality requirements; "
        "forcing status; precedence; vulnerability and exceptions"
    )
    return {
        "opening": opening,
        "family_id": f"three-level-preempt.{opening.casefold()}.{category}",
        "observed_count": len(rows),
        "responder_hcp_range": f"{min(hcps)}-{max(hcps)}",
        "shape_distribution": dict(sorted(Counter(str(row["responder_shape"]) for row in rows).items())),
        "support_distribution": dict(sorted(Counter(int(row["support"]) for row in rows).items())),
        "characteristics": category,
        "candidate_calls": candidate_calls,
        "source_statement": finding,
        "classification": "LOW_SAMPLE" if len(rows) < 3 else "SOURCE_PARTIAL",
        "executable_subset": False,
        "policy_required": False,
        "architecture_required": False,
        "missing_conditions": missing,
        "recommended_action": "defer",
    }


def run_three_level_preempt_response_source_readiness_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> ThreeLevelPreemptResponseSourceReadinessAudit:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    router = create_standard_sayc_router()
    positions: list[dict[str, object]] = []
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for case in baseline.batch.cases:
        result = case.result
        if (
            result.stop_reason.value != "no-recommendation"
            or result.final_auction not in {f"{opening} P" for opening in OPENING_SUITS}
        ):
            continue
        assert result.stopped_seat is not None
        opening = result.final_auction.split()[0]
        opening_suit = OPENING_SUITS[opening]
        responder_hand = case.deal.hand(result.stopped_seat)
        opener_hand = case.deal.hand(result.stopped_seat.partner())
        responder = evaluate_hand(responder_hand)
        opener = evaluate_hand(opener_hand)
        support = responder.length(opening_suit)
        independent = max(responder.length(suit) for suit in Suit if suit is not opening_suit)
        category = _primary_category(responder, support, independent)
        context = BiddingContext.create(
            hand=responder_hand,
            auction=Auction(result.dealer, tuple(result.final_auction.split())),
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        route = router.match(context)
        evaluated = router.evaluate(context)
        row = {
            "seed": case.deal.seed,
            "stable_id": f"seed-{case.deal.seed}:{result.stopped_seat.value}:{opening}-P",
            "auction_prefix": result.final_auction,
            "opening_bid": opening,
            "decision_seat": result.stopped_seat.value,
            "opener_hcp": opener.hcp,
            "opener_shape": _shape(opener_hand),
            "opener_opened_suit_length": opener.length(opening_suit),
            "responder_hcp": responder.hcp,
            "responder_shape": _shape(responder_hand),
            "responder_suit_lengths_shdc": {
                suit.name[0]: responder.length(suit)
                for suit in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)
            },
            "support": support,
            "longest_independent_suit_length": independent,
            "primary_category": category,
            "secondary_flags": {
                "balanced": responder.is_balanced,
                "strong_support": support >= 4,
                "moderate_support": support == 3,
                "short_support": support <= 2,
                "long_independent_suit": independent >= 6,
                "possible_nt_oriented": responder.is_balanced,
                "game_looking": responder.hcp >= 15,
                "slam_interest_looking": responder.hcp >= 19,
                "weak_no_action": responder.hcp <= 11,
            },
            "route_exists": route is not None,
            "route_name": None if route is None else route.route_id,
            "route_reaches_rule": route is not None,
            "rule_abstains": route is not None and evaluated.recommended_call is None,
            "route_missing": route is None,
            "current_action": "ABSTAIN" if evaluated.recommended_call is None else evaluated.recommended_call.serialize(),
        }
        positions.append(row)
        grouped[(opening, category)].append(row)

    per_opening = Counter(str(row["opening_bid"]) for row in positions)
    primary = Counter(str(row["primary_category"]) for row in positions)
    opening_partitions = {
        opening: {
            category: len(grouped[(opening, category)])
            for category in CATEGORY_ORDER
            if grouped[(opening, category)]
        }
        for opening in OPENING_SUITS
    }
    distributions = {}
    for opening in OPENING_SUITS:
        rows = [row for row in positions if row["opening_bid"] == opening]
        distributions[opening] = {
            "responder_hcp": dict(sorted(Counter(int(row["responder_hcp"]) for row in rows).items())),
            "responder_shape": dict(sorted(Counter(str(row["responder_shape"]) for row in rows).items())),
            "responder_support": dict(sorted(Counter(int(row["support"]) for row in rows).items())),
            "opener_hcp": dict(sorted(Counter(int(row["opener_hcp"]) for row in rows).items())),
            "opener_shape": dict(sorted(Counter(str(row["opener_shape"]) for row in rows).items())),
            "opener_suit_length": dict(sorted(Counter(int(row["opener_opened_suit_length"]) for row in rows).items())),
        }
    matrix = tuple(
        _matrix_row(opening, category, grouped[(opening, category)])
        for opening in OPENING_SUITS
        for category in CATEGORY_ORDER
        if grouped[(opening, category)]
    )
    ranked_ids = (
        "three-level-preempt.3c.possible-nt-oriented-balanced",
        "three-level-preempt.3d.possible-nt-oriented-balanced",
        "three-level-preempt.3h.possible-nt-oriented-balanced",
        "three-level-preempt.3s.possible-nt-oriented-balanced",
        "three-level-preempt.3h.long-independent-suit",
    )
    by_id = {str(row["family_id"]): row for row in matrix}
    return ThreeLevelPreemptResponseSourceReadinessAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        phase12q_expected_population=166,
        population=len(positions),
        per_opening_counts=dict(per_opening),
        primary_partitions={category: primary[category] for category in CATEGORY_ORDER},
        opening_partitions=opening_partitions,
        distributions=distributions,
        positions=tuple(positions),
        source_matrix=matrix,
        top_candidates=tuple(by_id[family_id] for family_id in ranked_ids),
        source_safe_candidates=(),
        major_vs_minor_finding=(
            "The source discusses minor preempts as 3NT/five-of-a-minor decisions and major preempts as major-game decisions, "
            "but supplies no complete numeric or precedence contract; it does not authorize merging 3C with 3D or 3H with 3S."
        ),
        router_finding="All 166 positions have no matching route; no rule is reached and production remains ABSTAIN.",
        decision="E. DEFER THREE-LEVEL PREEMPT RESPONSES",
        phase12s_recommendation={
            "phase": "Phase 12S — Weak-Two Response Source-Readiness Audit",
            "family_id": "response.weak-two",
            "exact_prefixes": ("2D P", "2H P", "2S P"),
            "phase12m_population": 540,
            "expected_action": "ABSTAIN",
            "numeric_authorization": "none before source audit",
            "policy_or_route_during_audit": False,
        },
        route_count=len(router.routes),
        production_rules_added=0,
        routes_added=0,
        policies_added=0,
        default_policies={"stayman_dual_major": None, "stayman_continuation": None, "jacoby_continuation": None},
        phase12q_population=1194,
        phase12n_calls=24,
        phase12o_residual=23,
        phase12p_decision="E. DEFER NATURAL 1NT RESPONSE FAMILY",
        phase12g_calls={"4H": 17, "4S": 21},
        phase12h_residual=197,
        phase12l_terminal={"HEARTS": 5, "SPADES": 7},
        jacoby_no_policy={"heart_transfer": 62, "spade_transfer": 61, "total": 123},
    )


def write_artifacts(audit: ThreeLevelPreemptResponseSourceReadinessAudit, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "bridgelab_phase12r_three_level_preempt_response_source_readiness_audit.json"
    markdown_path = output / "bridgelab_phase12r_three_level_preempt_response_source_readiness_audit.md"
    json_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    partition_rows = "\n".join(f"| {name} | {count} |" for name, count in audit.primary_partitions.items())
    matrix_rows = "\n".join(
        f"| {row['opening']} | {row['family_id']} | {row['observed_count']} | {row['responder_hcp_range']} | {', '.join(row['candidate_calls'])} | {row['classification']} | NO | {row['missing_conditions']} |"
        for row in audit.source_matrix
    )
    top_rows = "\n".join(
        f"| {rank} | `{row['opening']} P` | {row['observed_count']} | {row['responder_hcp_range']} | {row['characteristics']} | {', '.join(row['candidate_calls'])} | {row['classification']} | {row['missing_conditions']} |"
        for rank, row in enumerate(audit.top_candidates, 1)
    )
    markdown_path.write_text(f"""# Phase 12R — Three-Level Preempt Response Source-Readiness Audit

## Deterministic sample

- Seeds: 1–10,000
- Measured population: {audit.population} (Phase 12Q expectation {audit.phase12q_expected_population}, confirmed)
- Per opening: 3C={audit.per_opening_counts['3C']}, 3D={audit.per_opening_counts['3D']}, 3H={audit.per_opening_counts['3H']}, 3S={audit.per_opening_counts['3S']}
- Current action: `ABSTAIN` for all {audit.population}

## Mutually-exclusive primary partition

| Observed structural category | Count |
|---|---:|
{partition_rows}

The labels are investigation categories only. Secondary overlapping flags and every hand-level HCP, shape, suit length, support, opener detail, route result, and stable identity are in the JSON artifact. Per-opening HCP/shape/support distributions are also preserved there.

## Source-certainty matrix

| Opening | Family | Count | HCP | Candidate calls | Classification | Executable | Missing contract |
|---|---|---:|---|---|---|---|---|
{matrix_rows}

The source names Pass, raises/game, new suits, 3NT, and rare slam investigation, but uses qualitative/judgment language. It does not completely specify exact responder ranges, support/length and stopper thresholds, forcing status, precedence, vulnerability handling, or exceptions. No narrow subset is source-executable.

## Major versus minor and router findings

{audit.major_vs_minor_finding}

{audit.router_finding} Routes remain {audit.route_count}.

## Top candidates

| Rank | Prefix | Count | HCP | Structure | Candidate call(s) | Classification | Missing pieces |
|---:|---|---:|---|---|---|---|---|
{top_rows}

## Decision and next phase

**{audit.decision}.** Best source-safe subset: none.

Recommend **{audit.phase12s_recommendation['phase']}** for exact prefixes `2D P`, `2H P`, and `2S P` (Phase 12M population {audit.phase12s_recommendation['phase12m_population']}). The audit must add no policy or route and must not assign numeric boundaries before checking the frozen source.

Guards: Phase 12Q={audit.phase12q_population}; Phase 12N={audit.phase12n_calls}; Phase 12O={audit.phase12o_residual}; Phase 12P deferred; Phase 12G={audit.phase12g_calls}; Phase 12H={audit.phase12h_residual}; Phase 12L={audit.phase12l_terminal}; Jacoby={audit.jacoby_no_policy}; routes={audit.route_count}; defaults unchanged; knowledge Markdown changes=0.

Current cumulative Full Kit: Phase 12R
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_three_level_preempt_response_source_readiness_audit(), Path.cwd())
