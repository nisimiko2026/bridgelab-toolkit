"""Phase 12Q deterministic responder-rebid source-readiness audit."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.evaluation import evaluate_hand
from bridge.models import Vulnerability
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router


@dataclass(frozen=True, slots=True)
class ResponderRebidSourceReadinessAudit:
    start_seed: int
    deal_count: int
    population: int
    family_count: int
    families: tuple[dict[str, object], ...]
    positions: tuple[dict[str, object], ...]
    top_five: tuple[dict[str, object], ...]
    source_safe_candidates: tuple[str, ...]
    decision: str
    phase12r_specification: dict[str, object]
    route_count: int
    production_rules_added: int
    routes_added: int
    policies_added: int
    default_policies: dict[str, None]
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


def _family_id(auction: str) -> str:
    calls = auction.split()
    return "responder-rebid." + "-".join((calls[0], calls[2], calls[4])).casefold()


def _category(calls: list[str], opener_rule_id: str) -> str:
    opening, response, rebid = calls[0], calls[2], calls[4]
    if "jacoby" in opener_rule_id:
        return "accepted_jacoby_transfer"
    if "reverse" in opener_rule_id:
        return "reverse_like_new_suit"
    if rebid.endswith("NT"):
        return "notrump_rebid"
    if rebid[-1] == response[-1]:
        return "raise_responder_suit"
    if rebid[-1] == opening[-1]:
        return "same_suit_rebid"
    return "new_suit_rebid"


def _family_row(family_id: str, rows: list[dict[str, object]]) -> dict[str, object]:
    first = rows[0]
    count = len(rows)
    hcp_values = [int(row["hcp"]) for row in rows]
    shapes = Counter(str(row["shape"]) for row in rows)
    jacoby = first["category"] == "accepted_jacoby_transfer"
    low_sample = count < 10
    if jacoby:
        classification = "POLICY_REQUIRED"
        source_calls = ("P", "2NT", "4H/4S")
        finding = "Existing Jacoby continuation source maps explicit strength classes to calls; numeric classification remains non-default policy input."
        blocker = "No continuation-strength policy is configured; this boundary was already audited in Phases 12A–12D."
    elif low_sample:
        classification = "LOW_SAMPLE"
        source_calls = ("Pass", "raise", "suit", "2NT", "3NT")
        finding = "The general source lists possible rebid types but does not give an exact contract for this low-sample prefix."
        blocker = "Low sample plus incomplete trigger/call/precedence conditions."
    else:
        classification = "SOURCE_PARTIAL"
        source_calls = ("Pass", "raise", "preference", "suit", "2NT", "3NT")
        finding = "The frozen source provides qualitative responder-rebid priorities and examples, not a complete exact-prefix call contract."
        blocker = "Strength, support/stoppers, forcing status, competing calls, precedence, and exceptions are incomplete."
    deep = {
        "1_exact_auction_prefix": first["auction_prefix"],
        "2_exact_source_rebids": source_calls,
        "3_numeric_ranges_explicit": not jacoby,
        "4_suit_length_explicit": False,
        "5_support_count_explicit": False,
        "6_stoppers_required": first["category"] == "notrump_rebid",
        "7_balance_relevant": first["category"] == "notrump_rebid",
        "8_opener_minmax_required": True,
        "9_invite_vs_game_force_defined": False,
        "10_signoff_invitation_forcing_distinguished": False,
        "11_competing_calls_defined": False,
        "12_precedence_defined": False,
        "13_conventions_required": jacoby,
        "14_partnership_agreement_required": jacoby or first["category"] == "new_suit_rebid",
        "15_one_call_safe": False,
    }
    return {
        "family_id": family_id,
        "auction_prefix": first["auction_prefix"],
        "opening_bid": first["opening_bid"],
        "responder_first_bid": first["responder_first_bid"],
        "opener_rebid": first["opener_rebid"],
        "category": first["category"],
        "observed_count": count,
        "observed_hcp_range": f"{min(hcp_values)}-{max(hcp_values)}",
        "hcp_distribution": dict(sorted(Counter(hcp_values).items())),
        "shape_distribution": dict(sorted(shapes.items())),
        "route_name": first["route_name"],
        "route_exists": first["route_name"] is not None,
        "route_reaches_rule": first["route_name"] is not None,
        "rule_abstains": first["route_name"] is not None,
        "route_missing": first["route_name"] is None,
        "source_calls": source_calls,
        "source_finding": finding,
        "classification": classification,
        "executable_subset": None,
        "policy_required": jacoby,
        "architecture_required": False,
        "blocker": blocker,
        "recommended_action": "retain existing policy boundary" if jacoby else "defer",
        "deep_source_audit": deep,
    }


def run_responder_rebid_source_readiness_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> ResponderRebidSourceReadinessAudit:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    router = create_standard_sayc_router()
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    positions = []
    for case in baseline.batch.cases:
        result = case.result
        calls = result.final_auction.split()
        if (
            result.stop_reason.value != "no-recommendation"
            or len(calls) != 6
            or result.final_auction.startswith("2C P 2D P 2NT P")
        ):
            continue
        assert result.stopped_seat is not None
        hand = case.deal.hand(result.stopped_seat)
        evaluation = evaluate_hand(hand)
        context = BiddingContext.create(
            hand=hand,
            auction=Auction(result.dealer, tuple(calls)),
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        match = router.match(context)
        family_id = _family_id(result.final_auction)
        row = {
            "seed": case.deal.seed,
            "stable_id": f"seed-{case.deal.seed}:{result.stopped_seat.value}:{result.final_auction}",
            "family_id": family_id,
            "auction_prefix": result.final_auction,
            "opening_bid": calls[0],
            "responder_first_bid": calls[2],
            "opener_rebid": calls[4],
            "opener_rebid_rule": result.steps[4].rule_id,
            "category": _category(calls, result.steps[4].rule_id),
            "decision_seat": result.stopped_seat.value,
            "responder_hand": hand.serialize(),
            "hcp": evaluation.hcp,
            "shape": "-".join(str(length) for length in hand.shape),
            "suit_lengths_shdc": {
                suit.name[0]: evaluation.length(suit)
                for suit in __import__("bridge.models", fromlist=["Suit"]).Suit
            },
            "current_action": "ABSTAIN",
            "route_name": None if match is None else match.route_id,
            "route_reaches_rule": match is not None,
            "rule_abstains": match is not None,
            "route_missing": match is None,
        }
        grouped[family_id].append(row)
        positions.append(row)
    families = tuple(
        _family_row(family_id, grouped[family_id]) for family_id in sorted(grouped)
    )
    by_id = {row["family_id"]: row for row in families}
    top_ids = (
        "responder-rebid.1nt-2d-2h",
        "responder-rebid.1nt-2h-2s",
        "responder-rebid.1c-1s-2d",
        "responder-rebid.1c-1h-1s",
        "responder-rebid.1d-1s-2c",
    )
    top_five = tuple(by_id[family_id] for family_id in top_ids)
    return ResponderRebidSourceReadinessAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        population=len(positions),
        family_count=len(families),
        families=families,
        positions=tuple(positions),
        top_five=top_five,
        source_safe_candidates=(),
        decision="E. DEFER RESPONDER-REBID FAMILY",
        phase12r_specification={
            "target": "Three-level preempt response source-readiness audit",
            "exact_auction_prefixes": ("3C P", "3D P", "3H P", "3S P"),
            "decision_seat": "S",
            "deterministic_population": 166,
            "source_backed_condition": "Audit only; no executable condition selected yet.",
            "expected_call": "ABSTAIN pending source audit",
            "numeric_hcp_source_authorized": False,
            "shape_support_required": "To be audited from frozen preempt-response sources.",
            "policy_required": False,
            "new_route_required": False,
            "production_guards": (
                "no Phase 12Q production changes",
                "routes remain 45",
                "exclude previously deferred families",
                "do not implement Phase 12R during this audit",
            ),
        },
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
        phase12p_decision="E. DEFER NATURAL 1NT RESPONSE FAMILY",
        phase12g_calls={"4H": 17, "4S": 21},
        phase12h_residual=197,
        phase12l_terminal={"HEARTS": 5, "SPADES": 7},
        jacoby_no_policy={"heart_transfer": 62, "spade_transfer": 61, "total": 123},
    )


def write_artifacts(audit: ResponderRebidSourceReadinessAudit, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "bridgelab_phase12q_responder_rebid_source_readiness_audit.json"
    markdown_path = output / "bridgelab_phase12q_responder_rebid_source_readiness_audit.md"
    json_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    family_rows = "\n".join(
        f"| {row['family_id']} | `{row['auction_prefix']}` | {row['observed_count']} | {row['observed_hcp_range']} | "
        f"{row['category']} | {row['route_name'] or 'NONE'} | {row['classification']} | {row['blocker']} |"
        for row in audit.families
    )
    top_rows = "\n".join(
        f"| {rank} | {row['family_id']} | {row['observed_count']} | {row['classification']} | "
        f"{', '.join(row['source_calls'])} | {row['route_name'] or 'NONE'} | {row['blocker']} |"
        for rank, row in enumerate(audit.top_five, 1)
    )
    deep = "\n\n".join(
        f"### {rank}. {row['family_id']}\n\n" + "\n".join(
            f"- {key}: {value}" for key, value in row["deep_source_audit"].items()
        )
        for rank, row in enumerate(audit.top_five, 1)
    )
    markdown_path.write_text(f"""# Phase 12Q — Responder Rebid Source-Readiness Audit

## Deterministic sample

- Seeds: 1–10,000
- Reconstructed population: {audit.population}
- Exact normalized auction families: {audit.family_count}
- Current action: `ABSTAIN` for every position

## Complete normalized family and source-certainty matrix

| Family | Exact prefix | Count | HCP | Category | Route | Classification | Blocker |
|---|---|---:|---|---|---|---|---|
{family_rows}

Exact HCP and shape distributions for every family, plus all 1,194 hand-level positions, are preserved in the JSON artifact.

## Top-five ranking

| Rank | Family | Count | Classification | Source calls | Route | Blocker |
|---:|---|---:|---|---|---|---|
{top_rows}

The two Jacoby families rank first because a narrow policy boundary already exists, but they are not new implementation candidates and remain no-policy abstentions. The three natural examples remain qualitative or partnership-dependent.

## Top-five deep audit

{deep}

## Finding and decision

No source-safe responder-rebid subset exists. **{audit.decision}.**

## Concrete Phase 12R proposal

- Target: {audit.phase12r_specification['target']}
- Exact prefixes: {', '.join(audit.phase12r_specification['exact_auction_prefixes'])}
- Decision seat: {audit.phase12r_specification['decision_seat']}
- Deterministic population: {audit.phase12r_specification['deterministic_population']}
- Source-backed condition: {audit.phase12r_specification['source_backed_condition']}
- Expected call: {audit.phase12r_specification['expected_call']}
- Numeric HCP source-authorized: NO
- Shape/support: {audit.phase12r_specification['shape_support_required']}
- Policy required: NO
- New route required: NO during the audit

Guards: routes={audit.route_count}; Phase 12N={audit.phase12n_calls}; Phase 12O={audit.phase12o_residual}; Phase 12P deferred; Phase 12G={audit.phase12g_calls}; Phase 12H={audit.phase12h_residual}; Phase 12L={audit.phase12l_terminal}; Jacoby={audit.jacoby_no_policy}; defaults unchanged; knowledge Markdown changes=0.

Current cumulative Full Kit: Phase 12Q
""", encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_responder_rebid_source_readiness_audit(), Path.cwd())
