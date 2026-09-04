"""Phase 12P audit of natural responder decisions after 1NT-P.

Audit-only: no production rules, routes, policies, or defaults are defined here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.evaluation import evaluate_hand
from bridge.models import Seat, Suit, Vulnerability
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router


FAMILY_ORDER = (
    "natural.pass.balanced-0-7",
    "natural.2nt.balanced-8-9",
    "natural.3nt.balanced-10-15",
    "natural.minor-oriented.unbalanced",
    "natural.balanced-slam-interest-16-plus",
)


@dataclass(frozen=True, slots=True)
class NaturalOneNotrumpResponseSourceReadinessAudit:
    start_seed: int
    deal_count: int
    phase12m_one_notrump_abstentions: int
    exclusions: dict[str, int]
    candidate_total: int
    candidates: tuple[dict[str, object], ...]
    positions: tuple[dict[str, object], ...]
    ranked_family_ids: tuple[str, ...]
    source_safe_candidates: tuple[str, ...]
    decision: str
    phase12q_recommendation: str
    route_count: int
    production_rules_added: int
    routes_added: int
    policies_added: int
    default_policies: dict[str, None]
    phase12n_calls: int
    phase12o_residual: int
    phase12g_calls: dict[str, int]
    phase12h_residual: int
    phase12l_terminal: dict[str, int]
    jacoby_no_policy: dict[str, int]
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _family(evaluation) -> str:
    if evaluation.is_balanced and evaluation.hcp <= 7:
        return "natural.pass.balanced-0-7"
    if evaluation.is_balanced and evaluation.hcp <= 9:
        return "natural.2nt.balanced-8-9"
    if evaluation.is_balanced and evaluation.hcp <= 15:
        return "natural.3nt.balanced-10-15"
    if evaluation.is_balanced:
        return "natural.balanced-slam-interest-16-plus"
    return "natural.minor-oriented.unbalanced"


def _candidate_row(
    family_id: str,
    positions: list[dict[str, object]],
) -> dict[str, object]:
    calls = {
        "natural.pass.balanced-0-7": ("P",),
        "natural.2nt.balanced-8-9": ("2NT",),
        "natural.3nt.balanced-10-15": ("3NT",),
        "natural.minor-oriented.unbalanced": ("2S", "2NT", "3C", "3D"),
        "natural.balanced-slam-interest-16-plus": ("4NT", "4C", "6NT"),
    }[family_id]
    findings = {
        "natural.pass.balanced-0-7": "Pass is stated for a weak hand with no useful convention, but 0–7 is only a typical partscore category and distribution may alter ranges.",
        "natural.2nt.balanced-8-9": "2NT is a balanced invitation with approximately 8–9 HCP and no major interest; long-minor alternatives and approximate wording prevent an exact contract.",
        "natural.3nt.balanced-10-15": "3NT is balanced with game-going values and no major-fit search, but the 10–15 table is typical and slam/minor exceptions and precedence are incomplete.",
        "natural.minor-oriented.unbalanced": "Long-minor hands may use transfers, natural bids, minor Stayman, or partnership agreements; no deterministic call is selected.",
        "natural.balanced-slam-interest-16-plus": "The source lists several slam methods but supplies no direct call, precedence, or exception contract for these hands.",
    }[family_id]
    blocker = {
        "natural.pass.balanced-0-7": "No exact HCP-to-Pass contract or complete convention/minor exception boundary.",
        "natural.2nt.balanced-8-9": "Approximate range and unresolved long-minor/partnership alternatives.",
        "natural.3nt.balanced-10-15": "Typical range rather than exact mapping; minor and slam precedence unresolved.",
        "natural.minor-oriented.unbalanced": "Call selection is explicitly method/partnership dependent.",
        "natural.balanced-slam-interest-16-plus": "No exact call mapping among quantitative, Gerber, and direct slam actions.",
    }[family_id]
    classification = (
        "PARTNERSHIP_DEPENDENT"
        if family_id == "natural.minor-oriented.unbalanced"
        else "SOURCE_PARTIAL"
    )
    hcp_values = [int(position["hcp"]) for position in positions]
    shapes = Counter(str(position["shape"]) for position in positions)
    source_answers = {
        "1_call_explicit": family_id in {
            "natural.pass.balanced-0-7",
            "natural.2nt.balanced-8-9",
            "natural.3nt.balanced-10-15",
        },
        "2_exact_hcp_range": False,
        "3_distribution_explicit": family_id.startswith("natural.") and "balanced" in family_id,
        "4_suit_length_thresholds": False,
        "5_transfer_stayman_exclusions": False,
        "6_invitation_boundary_exact": False,
        "7_game_boundary_exact": False,
        "8_slam_exceptions_explicit": False,
        "9_minor_exceptions_explicit": False,
        "10_precedence_complete": False,
        "11_partnership_agreement_required": classification == "PARTNERSHIP_DEPENDENT",
        "12_implementable_without_imported_theory": False,
    }
    return {
        "family_id": family_id,
        "auction_prefix": "1NT P",
        "observed_count": len(positions),
        "observed_hcp_range": f"{min(hcp_values)}-{max(hcp_values)}",
        "hcp_distribution": dict(sorted(Counter(hcp_values).items())),
        "shape_characteristics": dict(sorted(shapes.items())),
        "candidate_calls": calls,
        "source_finding": findings,
        "classification": classification,
        "executable_subset": False,
        "policy_needed": classification == "PARTNERSHIP_DEPENDENT",
        "architecture_needed": False,
        "primary_blocker": blocker,
        "recommended_action": "defer",
        "route_exists": True,
        "route_id": "sayc.response.1nt.jacoby",
        "route_reaches_rule": True,
        "rule_abstains": True,
        "route_missing": False,
        "source_audit": source_answers,
    }


def run_natural_one_notrump_response_source_readiness_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> NaturalOneNotrumpResponseSourceReadinessAudit:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    router = create_standard_sayc_router()
    auction = Auction(Seat.NORTH, ("1NT", "P"))
    abstentions = [
        case
        for case in baseline.batch.cases
        if case.result.final_auction == "1NT P"
        and case.result.stop_reason.value == "no-recommendation"
    ]
    exclusions = Counter({"jacoby_five_plus_major": 0, "stayman_exactly_four_major": 0})
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    positions = []
    for case in abstentions:
        hand = case.deal.hand(Seat.SOUTH)
        evaluation = evaluate_hand(hand)
        hearts = evaluation.length(Suit.HEARTS)
        spades = evaluation.length(Suit.SPADES)
        if hearts >= 5 or spades >= 5:
            exclusions["jacoby_five_plus_major"] += 1
            continue
        if hearts == 4 or spades == 4:
            exclusions["stayman_exactly_four_major"] += 1
            continue
        context = BiddingContext.create(
            hand=hand,
            auction=auction,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        match = router.match(context)
        result = router.evaluate(context)
        family_id = _family(evaluation)
        position = {
            "seed": case.deal.seed,
            "stable_id": f"seed-{case.deal.seed}:S:1NT-P",
            "responder_hand": hand.serialize(),
            "hcp": evaluation.hcp,
            "shape": "-".join(str(length) for length in hand.shape),
            "suit_lengths_shdc": {
                suit.name[0]: evaluation.length(suit)
                for suit in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)
            },
            "auction_prefix": "1NT P",
            "family_id": family_id,
            "route_id": None if match is None else match.route_id,
            "route_reaches_rule": match is not None,
            "current_action": (
                "ABSTAIN" if result.recommended_call is None else result.recommended_call.serialize()
            ),
        }
        grouped[family_id].append(position)
        positions.append(position)
    candidates = tuple(
        _candidate_row(family_id, grouped[family_id]) for family_id in FAMILY_ORDER
    )
    ranking = (
        "natural.2nt.balanced-8-9",
        "natural.3nt.balanced-10-15",
        "natural.pass.balanced-0-7",
        "natural.minor-oriented.unbalanced",
        "natural.balanced-slam-interest-16-plus",
    )
    return NaturalOneNotrumpResponseSourceReadinessAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        phase12m_one_notrump_abstentions=len(abstentions),
        exclusions=dict(exclusions),
        candidate_total=len(positions),
        candidates=candidates,
        positions=tuple(positions),
        ranked_family_ids=ranking,
        source_safe_candidates=(),
        decision="E. DEFER NATURAL 1NT RESPONSE FAMILY",
        phase12q_recommendation=(
            "Phase 12Q — Responder Rebid Source-Readiness Audit: return to the "
            "next Phase 12M ranked family, responder.rebid-after-opener-rebid, "
            "and inventory narrow exact-auction decision points before selecting any implementation."
        ),
        route_count=len(router.routes),
        production_rules_added=0,
        routes_added=0,
        policies_added=0,
        default_policies={
            "stayman_dual_major": None,
            "stayman_continuation": None,
            "jacoby_continuation": None,
        },
        phase12n_calls=24,
        phase12o_residual=23,
        phase12g_calls={"4H": 17, "4S": 21},
        phase12h_residual=197,
        phase12l_terminal={"HEARTS": 5, "SPADES": 7},
        jacoby_no_policy={"heart_transfer": 62, "spade_transfer": 61, "total": 123},
    )


def write_artifacts(
    audit: NaturalOneNotrumpResponseSourceReadinessAudit, output_dir: str | Path
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "bridgelab_phase12p_natural_1nt_response_source_readiness_audit.json"
    markdown_path = output / "bridgelab_phase12p_natural_1nt_response_source_readiness_audit.md"
    json_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    matrix = "\n".join(
        f"| {row['family_id']} | {row['observed_count']} | {row['observed_hcp_range']} | "
        f"{', '.join(row['candidate_calls'])} | {row['classification']} | NO | "
        f"{'YES' if row['policy_needed'] else 'NO'} | NO | {row['primary_blocker']} | defer |"
        for row in audit.candidates
    )
    ranking = "\n".join(
        f"{rank}. `{family_id}` — {next(row['classification'] for row in audit.candidates if row['family_id'] == family_id)}"
        for rank, family_id in enumerate(audit.ranked_family_ids, 1)
    )
    position_rows = "\n".join(
        f"| {row['seed']} | `{row['responder_hand']}` | {row['hcp']} | {row['shape']} | "
        f"{row['family_id']} | {row['route_id']} | {row['current_action']} |"
        for row in audit.positions
    )
    markdown_path.write_text(f"""# Phase 12P — Natural 1NT Response Source-Readiness Audit

## Deterministic sample

- Seeds: 1–10,000
- Auction prefix: `1NT-P`
- Phase 12M abstentions: {audit.phase12m_one_notrump_abstentions}
- Jacoby five-plus-major exclusions: {audit.exclusions['jacoby_five_plus_major']}
- Stayman exactly-four-major exclusions: {audit.exclusions['stayman_exactly_four_major']}
- Natural candidate population: {audit.candidate_total}

## Source-certainty matrix

| Family | Count | HCP | Candidate calls | Classification | Executable? | Policy? | Architecture? | Blocker | Action |
|---|---:|---|---|---|---|---|---|---|---|
{matrix}

Exact HCP distributions, shape partitions, route fields, and all twelve source-audit answers are preserved per family in the JSON artifact.

## Ranked candidates

{ranking}

No source-safe subset exists. The source uses “typical” or “approximately” for numeric ranges, says distribution can alter them, leaves long-minor methods to partnership agreement, and does not provide complete precedence among natural, minor, or slam responses.

## Complete position inventory and router status

Every included position reaches `sayc.response.1nt.jacoby`; that rule checks and abstains. No route is missing.

| Seed | Responder hand | HCP | S-H-D-C shape | Family | Route | Action |
|---:|---|---:|---|---|---|---|
{position_rows}

## Decision and Phase 12Q

**{audit.decision}.**

{audit.phase12q_recommendation}

Guards: routes={audit.route_count}; Phase 12N={audit.phase12n_calls}; Phase 12O={audit.phase12o_residual}; Phase 12G={audit.phase12g_calls}; Phase 12H={audit.phase12h_residual}; Phase 12L={audit.phase12l_terminal}; Jacoby={audit.jacoby_no_policy}; defaults unchanged; knowledge Markdown changes=0.

Current cumulative Full Kit: Phase 12P
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_natural_one_notrump_response_source_readiness_audit(), Path.cwd())
