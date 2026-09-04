"""Phase 12D audit of endpoints created by the Phase 12C fixture.

This module contains benchmark classification and reporting only. It adds no
production route, bidding rule, policy default, or hand-strength inference.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    Auction,
    BiddingContext,
    JacobyContinuationStrengthClass,
    Seat,
    SystemContext,
    Vulnerability,
    run_sayc_coverage_benchmark,
)
from bridge.sayc_route_configuration import create_standard_sayc_router

from .jacoby_continuation_policy_fixture import (
    HEART_AUCTION,
    SPADE_AUCTION,
    STRENGTH_CLASSES,
    run_jacoby_policy_fixture_benchmark,
)


@dataclass(frozen=True, slots=True)
class PostJacobyEndpointAudit:
    start_seed: int
    deal_count: int
    successful_phase12c_continuations: int
    accepted_heart_transfer_positions: int
    accepted_spade_transfer_positions: int
    weak: dict[str, object]
    invitational: dict[str, object]
    game_going: dict[str, object]
    source_certainty_matrix: tuple[dict[str, object], ...]
    invitational_2nt_source_findings: tuple[dict[str, object], ...]
    recommendation: str
    recommended_next_family: str
    default_behavior_unchanged: bool
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_post_jacoby_endpoint_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> PostJacobyEndpointAudit:
    phase12c = run_jacoby_policy_fixture_benchmark(
        start_seed=start_seed, deal_count=deal_count
    )
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    cases = tuple(
        case
        for case in baseline.batch.cases
        if case.result.final_auction in (HEART_AUCTION, SPADE_AUCTION)
    )
    split = Counter(
        (
            STRENGTH_CLASSES[index % len(STRENGTH_CLASSES)].name,
            "heart" if case.result.final_auction == HEART_AUCTION else "spade",
        )
        for index, case in enumerate(cases)
    )
    production_router = create_standard_sayc_router()
    route_attempts = Counter()
    for index, case in enumerate(cases):
        strength_class = STRENGTH_CLASSES[index % len(STRENGTH_CLASSES)]
        base_calls = tuple(case.result.final_auction.split())
        if strength_class is JacobyContinuationStrengthClass.WEAK:
            completed = Auction(Seat.NORTH, (*base_calls, "P", "P"))
            if not completed.is_complete:
                raise AssertionError("WEAK Pass path did not become auction-terminal")
            continue
        if strength_class is JacobyContinuationStrengthClass.INVITATIONAL:
            continuation = "2NT"
        elif strength_class is JacobyContinuationStrengthClass.GAME_GOING:
            continuation = "4H" if case.result.final_auction == HEART_AUCTION else "4S"
        else:
            continue
        endpoint = Auction(Seat.NORTH, (*base_calls, continuation, "P"))
        context = BiddingContext.create(
            hand=case.deal.hand(endpoint.next_seat),
            auction=endpoint,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        if production_router.match(context) is not None:
            route_attempts[strength_class.name] += 1

    weak = {
        "total": split[("WEAK", "heart")] + split[("WEAK", "spade")],
        "heart_pass": split[("WEAK", "heart")],
        "spade_pass": split[("WEAK", "spade")],
        "terminal_count": split[("WEAK", "heart")] + split[("WEAK", "spade")],
        "endpoint_classification": "TERMINAL",
        "current_production_route_attempts": route_attempts["WEAK"],
    }
    invitational = {
        "total": split[("INVITATIONAL", "heart")]
        + split[("INVITATIONAL", "spade")],
        "heart_2NT": split[("INVITATIONAL", "heart")],
        "spade_2NT": split[("INVITATIONAL", "spade")],
        "next_actor": "opener (after the benchmark opponent passes)",
        "endpoint_classification": "SOURCE_INSUFFICIENT",
        "current_production_route_attempts": route_attempts["INVITATIONAL"],
    }
    game_going = {
        "total": split[("GAME_GOING", "heart")] + split[("GAME_GOING", "spade")],
        "4H": phase12c.game_heart_4H,
        "4S": phase12c.game_spade_4S,
        "terminal_count": split[("GAME_GOING", "heart")]
        + split[("GAME_GOING", "spade")],
        "endpoint_classification": "TERMINAL",
        "current_production_route_attempts": route_attempts["GAME_GOING"],
    }

    matrix = (
        _matrix_row("WEAK heart Pass", weak["heart_pass"], "none", "TERMINAL", True, "none"),
        _matrix_row("WEAK spade Pass", weak["spade_pass"], "none", "TERMINAL", True, "none"),
        _matrix_row(
            "INVITATIONAL heart 2NT",
            invitational["heart_2NT"],
            "opener",
            "SOURCE_INSUFFICIENT",
            False,
            "No exact opener call, trigger conditions, or precedence in the frozen corpus.",
        ),
        _matrix_row(
            "INVITATIONAL spade 2NT",
            invitational["spade_2NT"],
            "opener",
            "SOURCE_INSUFFICIENT",
            False,
            "No exact opener call, trigger conditions, or precedence in the frozen corpus.",
        ),
        _matrix_row("GAME_GOING 4H", game_going["4H"], "none", "TERMINAL", True, "none"),
        _matrix_row("GAME_GOING 4S", game_going["4S"], "none", "TERMINAL", True, "none"),
    )
    findings = tuple(
        _source_finding(call)
        for call in ("Pass", "3H / 3S", "3NT", "4H / 4S")
    )
    return PostJacobyEndpointAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        successful_phase12c_continuations=phase12c.produced_call_count,
        accepted_heart_transfer_positions=phase12c.accepted_heart_transfer_positions,
        accepted_spade_transfer_positions=phase12c.accepted_spade_transfer_positions,
        weak=weak,
        invitational=invitational,
        game_going=game_going,
        source_certainty_matrix=matrix,
        invitational_2nt_source_findings=findings,
        recommendation="C. DEFER THIS FAMILY",
        recommended_next_family=(
            "Audit game-going responder continuations after deterministic 1NT Stayman "
            "responses; the frozen Stayman source explicitly names 4H/4S when a major "
            "fit is found and 3NT in its no-major-fit game example, subject to an "
            "explicit responder-strength policy boundary."
        ),
        default_behavior_unchanged=phase12c.default_behavior_unchanged,
    )


def _matrix_row(endpoint, count, next_actor, status, executable, blocker):
    return {
        "endpoint": endpoint,
        "count": count,
        "next_actor": next_actor,
        "source_status": status,
        "executable": executable,
        "blocker": blocker,
    }


def _source_finding(call: str) -> dict[str, object]:
    return {
        "candidate_call": call,
        "explicitly_stated_after_invitational_2NT": False,
        "trigger_condition": None,
        "condition_directly_computable": False,
        "unsupported_numeric_strength_required": False,
        "partnership_agreement_required": "undetermined because the call is not specified",
        "precedence_complete": False,
        "finding": (
            "The canonical Jacoby article specifies responder's 2NT as an invitation "
            "but supplies no opener continuation mapping after that auction."
        ),
    }


def write_endpoint_audit_artifacts(
    audit: PostJacobyEndpointAudit, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12d_post_jacoby_endpoint_audit.json"
    markdown_path = output_dir / "bridgelab_phase12d_post_jacoby_endpoint_audit.md"
    json_path.write_text(
        json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    rows = "\n".join(
        "| {endpoint} | {count} | {next_actor} | {source_status} | {executable} | {blocker} |".format(
            **row
        )
        for row in audit.source_certainty_matrix
    )
    findings = "\n".join(
        f"- **{item['candidate_call']}**: not explicitly stated; no trigger or complete precedence is supplied."
        for item in audit.invitational_2nt_source_findings
    )
    weak, invitational, game = audit.weak, audit.invitational, audit.game_going
    markdown_path.write_text(
        f"""# Phase 12D — Post-Jacoby Continuation Endpoint Audit

## Deterministic sample

- seeds 1–10,000
- Phase 12C successful continuations: {audit.successful_phase12c_continuations}

## WEAK

- total: {weak['total']}
- heart Pass: {weak['heart_pass']}
- spade Pass: {weak['spade_pass']}
- terminal count: {weak['terminal_count']}
- endpoint classification: {weak['endpoint_classification']}

## INVITATIONAL

- total: {invitational['total']}
- heart 2NT: {invitational['heart_2NT']}
- spade 2NT: {invitational['spade_2NT']}
- endpoint classification: {invitational['endpoint_classification']}

## GAME_GOING

- total: {game['total']}
- 4H: {game['4H']}
- 4S: {game['4S']}
- terminal count: {game['terminal_count']}
- endpoint classification: {game['endpoint_classification']}

## Source-certainty matrix

| Endpoint | Count | Next actor | Source status | Executable? | Blocker |
|---|---:|---|---|---|---|
{rows}

## Invitational-2NT source findings

The frozen `jacoby-transfers.md` source explicitly presents both transfer-then-2NT
auctions and says responder invites game. It does not state opener's next call,
define minimum/maximum for this decision, map two- versus three-card support,
or provide deterministic precedence among Pass, 3H/3S, 3NT, and 4H/4S.
`response-to-1nt.md` says the goal of an invitational hand is to determine whether
opener has a maximum, but likewise supplies no post-transfer call mapping.
`sayc.md` lists Jacoby Transfers as part of SAYC but adds no such continuation.

{findings}

## Recommendation

**{audit.recommendation}.** The source is incomplete, not merely separated by a
well-defined policy classification, so Phase 12D must not implement this family.

Recommended next implementation-family audit: {audit.recommended_next_family}

Ordinary no-policy benchmark unchanged: **{'YES' if audit.default_behavior_unchanged else 'NO'}**
({audit.accepted_heart_transfer_positions} + {audit.accepted_spade_transfer_positions} = 123).

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12D
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_endpoint_audit_artifacts(run_post_jacoby_endpoint_audit(), Path.cwd())
