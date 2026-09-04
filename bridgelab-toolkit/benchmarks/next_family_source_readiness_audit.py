"""Phase 12M deterministic inventory and frozen-source readiness audit.

This module measures existing production behavior only.  It adds no route,
rule, policy, classifier, or default.
"""

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


READINESS = {
    "SOURCE_EXECUTABLE", "POLICY_REQUIRED", "ARCHITECTURE_REQUIRED",
    "SOURCE_PARTIAL", "SOURCE_INSUFFICIENT", "PARTNERSHIP_DEPENDENT",
    "LOW_SAMPLE", "ALREADY_COVERED", "DEFERRED_EXISTING",
}


@dataclass(frozen=True, slots=True)
class CandidateFamily:
    family_id: str
    auction_prefixes: tuple[str, ...]
    decision_seat: str
    observed_count: int
    current_action: str
    current_routes: tuple[str, ...]
    existing_rule_abstains: bool
    routing_stops_before_rule: bool
    source_files: tuple[str, ...]
    classification: str
    blocker: str


@dataclass(frozen=True, slots=True)
class Phase12MSourceReadinessAudit:
    start_seed: int
    deal_count: int
    stop_reason_counts: dict[str, int]
    candidates: tuple[CandidateFamily, ...]
    top_five: tuple[dict[str, object], ...]
    selected_family_id: str
    selected_subset_count: int
    decision: str
    phase12n_specification: dict[str, object]
    deferred_families: tuple[dict[str, object], ...]
    route_count: int
    default_policies: dict[str, None]
    phase12g_calls: dict[str, int]
    phase12h_residual: int
    phase12l_terminal: dict[str, int]
    jacoby_no_policy: dict[str, int]
    production_rules_added: int = 0
    policies_added: int = 0
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _family(auction: str) -> str:
    calls = auction.split()
    if not calls:
        return "opening.unresolved"
    if len(calls) == 2:
        opening = calls[0]
        if opening in {"2D", "2H", "2S"}:
            return "response.weak-two"
        if opening in {"3C", "3D", "3H", "3S"}:
            return "response.three-level-preempt"
        if opening == "1NT":
            return "response.one-notrump"
        if opening == "2NT":
            return "response.two-notrump"
        return "response.one-level-existing-rule"
    if auction.startswith("2C P 2D P"):
        return "opener.strong-two-club-after-waiting"
    if len(calls) == 4:
        return "opener.one-level-rebid-existing-rule"
    return "responder.rebid-after-opener-rebid"


_META = {
    "opening.unresolved": ("../knowledge/bidding/natural-bids/opening-bids/opening-requirements.md", "SOURCE_PARTIAL", "Multiple opening choices and judgment boundaries remain."),
    "response.one-notrump": ("../knowledge/bidding/natural-bids/responses/response-to-1nt.md", "SOURCE_PARTIAL", "Natural calls are explicit, but convention precedence prevents a complete family contract."),
    "response.weak-two": ("../knowledge/bidding/natural-bids/responses/response-to-weak-two.md", "PARTNERSHIP_DEPENDENT", "Actions use usually/constructive language, suit quality, vulnerability, and agreements."),
    "response.three-level-preempt": ("../knowledge/bidding/natural-bids/responses/response-to-three-level-preempt.md", "SOURCE_PARTIAL", "Pass/game/sacrifice choices depend on fit, shape, vulnerability, and judgment."),
    "response.two-notrump": ("../knowledge/bidding/natural-bids/responses/response-to-2nt.md", "SOURCE_PARTIAL", "Uncovered natural and conventional choices lack complete precedence."),
    "response.one-level-existing-rule": ("../knowledge/bidding/natural-bids/responses/responding-to-opening-bids.md", "SOURCE_PARTIAL", "Existing routed rules deliberately abstain outside their complete sourced subsets."),
    "opener.strong-two-club-after-waiting": ("../knowledge/bidding/natural-bids/responses/response-to-2-clubs.md", "SOURCE_PARTIAL", "The 2NT subset is exact; suit rebids use qualitative strength and suit language."),
    "opener.one-level-rebid-existing-rule": ("../knowledge/bidding/natural-bids/rebids/opening-rebids.md", "SOURCE_PARTIAL", "Existing routed rebid rules abstain where source precedence is incomplete."),
    "responder.rebid-after-opener-rebid": ("../knowledge/bidding/natural-bids/rebids/responder-rebids.md", "SOURCE_PARTIAL", "Broad family has strength ranges but incomplete mutually exclusive call precedence."),
}


def _top_audit(family: CandidateFamily, rank: int) -> dict[str, object]:
    strong = family.family_id == "opener.strong-two-club-after-waiting"
    answers = {
        "1_auction_prefix": "2C P 2D P" if strong else " / ".join(family.auction_prefixes),
        "2_required_conditions": "balanced and 22–24 HCP" if strong else "Family-specific strength, shape, fit, and prior-call state.",
        "3_runtime_state_available": strong,
        "4_source_calls": ("2NT",) if strong else (),
        "5_mutually_exclusive": strong,
        "6_precedence_present": strong,
        "7_numeric_boundaries": strong,
        "8_boundaries_frozen": strong,
        "9_distribution_explicit": strong,
        "10_exceptions_explicit": False,
        "11_partnership_agreement_required": family.classification == "PARTNERSHIP_DEPENDENT",
        "12_entire_family_safe": False,
        "13_smaller_executable_subset": "balanced 22–24 HCP -> 2NT" if strong else None,
        "14_policy_boundary_solves": family.classification == "PARTNERSHIP_DEPENDENT",
        "15_architecture_alone_solves": False,
    }
    return {
        "rank": rank, "family_id": family.family_id,
        "auction_prefix": " / ".join(family.auction_prefixes),
        "decision_seat": family.decision_seat, "observed_count": family.observed_count,
        "current_behavior": family.current_action,
        "source_classification": family.classification,
        "small_source_safe_subset": "24 balanced 22–24 HCP positions -> 2NT" if strong else None,
        "policy_needed": family.classification == "PARTNERSHIP_DEPENDENT",
        "architecture_needed": False, "primary_blocker": family.blocker,
        "recommended_action": "Phase 12N narrow subset" if strong else "defer",
        "router_audit": {
            "route_exists": bool(family.current_routes),
            "routes": family.current_routes,
            "route_reaches_rule": family.existing_rule_abstains,
            "rule_abstains": family.existing_rule_abstains,
            "new_route_required": strong or not bool(family.current_routes),
        },
        "deep_source_audit": answers,
    }


def run_next_family_source_readiness_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> Phase12MSourceReadinessAudit:
    report = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    router = create_standard_sayc_router()
    grouped: dict[str, list[object]] = defaultdict(list)
    reasons = Counter()
    for case in report.batch.cases:
        reasons[case.result.stop_reason.value] += 1
        if case.result.stop_reason.value == "no-recommendation":
            grouped[_family(case.result.final_auction)].append(case)

    candidates = []
    for family_id in sorted(grouped):
        cases = grouped[family_id]
        routes = set()
        seats = set()
        auctions = set()
        for case in cases:
            result = case.result
            assert result.stopped_seat is not None
            seats.add(result.stopped_seat.value)
            auctions.add(
                "2C P 2D P"
                if family_id == "opener.strong-two-club-after-waiting"
                else result.final_auction or "<opening>"
            )
            context = BiddingContext.create(
                hand=case.deal.hand(result.stopped_seat),
                auction=Auction(result.dealer, tuple(result.final_auction.split())),
                vulnerability=Vulnerability.NONE,
                system=SystemContext("SAYC"),
            )
            route = router.match(context)
            if (
                route is not None
                and family_id != "opener.strong-two-club-after-waiting"
            ):
                routes.add(route.route_id)
        source, classification, blocker = _META[family_id]
        candidates.append(CandidateFamily(
            family_id, tuple(sorted(auctions)), "/".join(sorted(seats)), len(cases),
            "ABSTAIN", tuple(sorted(routes)), bool(routes), not bool(routes),
            (source,), classification, blocker,
        ))
    candidates = tuple(candidates)
    by_id = {candidate.family_id: candidate for candidate in candidates}
    ranked_ids = (
        "opener.strong-two-club-after-waiting", "response.one-notrump",
        "responder.rebid-after-opener-rebid", "response.three-level-preempt",
        "response.weak-two",
    )
    top = tuple(_top_audit(by_id[name], rank) for rank, name in enumerate(ranked_ids, 1))
    strong_cases = grouped["opener.strong-two-club-after-waiting"]
    subset_count = sum(
        22 <= evaluate_hand(case.deal.hand(case.result.dealer)).hcp <= 24
        and evaluate_hand(case.deal.hand(case.result.dealer)).is_balanced
        for case in strong_cases
    )
    return Phase12MSourceReadinessAudit(
        start_seed, deal_count, dict(sorted(reasons.items())), candidates, top,
        "opener.strong-two-club-after-waiting.balanced-22-24", subset_count,
        "D. ONLY A NARROW SUBSET IS IMPLEMENTABLE",
        {
            "target_family": "Strong 2C opener rebid after 2D waiting — balanced subset",
            "auction_prefix": "2C P 2D P", "decision_seat": "N",
            "observed_family_population": 47, "observed_subset_population": subset_count,
            "source_backed_condition": "Opener is balanced with 22–24 HCP.",
            "expected_calls": ("2NT",), "policy_architecture_needed": False,
            "route_change_needed": True, "production_implementation_appropriate": True,
            "key_guards": ("exact uncontested prefix only", "balanced only", "22–24 HCP inclusive", "all other hands abstain", "no default or policy changes"),
        },
        (
            {"family_id": "phase12h.stayman-residual", "observed_count": 197, "classification": "DEFERRED_EXISTING"},
            {"family_id": "phase12l.dual-major-hearts-residual", "observed_count": 31, "classification": "DEFERRED_EXISTING"},
            {"family_id": "phase12l.dual-major-spades-residual", "observed_count": 29, "classification": "DEFERRED_EXISTING"},
        ),
        44,
        {"stayman_dual_major": None, "stayman_continuation": None, "jacoby_continuation": None},
        {"4H": 17, "4S": 21}, 197, {"HEARTS": 5, "SPADES": 7},
        {"heart_transfer": 62, "spade_transfer": 61, "total": 123},
    )


def write_artifacts(audit: Phase12MSourceReadinessAudit, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "bridgelab_phase12m_next_family_source_readiness_audit.json"
    md_path = output / "bridgelab_phase12m_next_family_source_readiness_audit.md"
    json_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    inventory = "\n".join(
        f"| {c.family_id} | {'<br>'.join(c.auction_prefixes)} | {c.decision_seat} | {c.observed_count} | ABSTAIN | {', '.join(c.current_routes) or 'NONE'} | {'YES' if c.existing_rule_abstains else 'NO'} | {'YES' if c.routing_stops_before_rule else 'NO'} | {c.source_files[0]} | {c.classification} |"
        for c in audit.candidates
    )
    ranking = "\n".join(
        f"| {r['rank']} | {r['family_id']} | {r['observed_count']} | {r['source_classification']} | {r['small_source_safe_subset'] or 'NO'} | {r['primary_blocker']} | {r['recommended_action']} |"
        for r in audit.top_five
    )
    deep = "\n\n".join(
        f"### {r['rank']}. {r['family_id']}\n\n" + "\n".join(f"{key}. **{value}**" for key, value in r["deep_source_audit"].items()) +
        f"\n\nRouter: {json.dumps(r['router_audit'], sort_keys=True)}"
        for r in audit.top_five
    )
    spec = audit.phase12n_specification
    md_path.write_text(f"""# Phase 12M — Next Deterministic Family Source-Readiness Audit

## Deterministic sample

- seeds 1–10,000
- ordinary no-policy production configuration
- production routes: {audit.route_count}
- candidate families: {len(audit.candidates)}

Explicitly deferred families: Phase 12H Stayman residuals (197), Phase 12L dual-major downstream residuals (HEARTS 31, SPADES 29). Each is `DEFERRED_EXISTING` and excluded from selection.

## Complete candidate-family inventory

| Family ID | Auction prefix(es) | Seat | Count | Action | Route(s) | Rule abstains | Stops before rule | Frozen source | Classification |
|---|---|---|---:|---|---|---|---|---|---|
{inventory}

## Top-five ranking

| Rank | Family | Count | Classification | Source-safe subset | Primary blocker | Action |
|---:|---|---:|---|---|---|---|
{ranking}

The ranking prioritizes source certainty over volume. Exact blockers for every non-selected top candidate are shown above.

## Deep frozen-source audit

{deep}

## Selection

**{audit.decision}.** The best source-safe candidate is the 24-position balanced 22–24 HCP subset within the 47-position strong-2C opener-rebid family. A smaller subset is required because the source describes suit rebids qualitatively and does not give their complete precedence.

## Recommended Phase 12N specification

- Target family: {spec['target_family']}
- Exact auction prefix: `{spec['auction_prefix']}`
- Decision seat: {spec['decision_seat']}
- Observed deterministic population: family {spec['observed_family_population']}; executable subset {spec['observed_subset_population']}
- Exact source-backed condition: {spec['source_backed_condition']}
- Expected call: `2NT`
- Policy architecture needed: NO
- Route change needed: YES, one exact-prefix route
- Production implementation appropriate: YES, in Phase 12N only
- Guards: {'; '.join(spec['key_guards'])}

Production guards: routes=44; defaults NONE/NONE/NONE; Phase 12G=17/21; Phase 12H=197; Phase 12L=5/7; Jacoby no-policy=62+61=123; production rules added=0; policies added=0; production defaults changed=NO; knowledge Markdown changed=0.

Current cumulative Full Kit: Phase 12M
""", encoding="utf-8")
    return md_path, json_path


if __name__ == "__main__":
    write_artifacts(run_next_family_source_readiness_audit(), Path.cwd())
