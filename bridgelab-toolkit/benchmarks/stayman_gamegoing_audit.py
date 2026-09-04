"""Phase 12E benchmark-only audit of GAME_GOING Stayman continuations."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    Auction,
    BiddingContext,
    KnowledgeSource,
    Seat,
    Suit,
    SystemContext,
    StaymanContinuationStrength,
    StaymanContinuationStrengthAssessment,
    Vulnerability,
    run_sayc_coverage_benchmark,
)
from bridge.policy_registry import (
    STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION,
    PolicyRegistry,
    assess_configured_stayman_continuation_strength,
)
from bridge.sayc_1nt_stayman import (
    create_sayc_one_notrump_stayman_opener_response_engine,
)
from bridge.sayc_route_configuration import create_standard_sayc_router


STAYMAN_ENDPOINTS = {
    "2D": "1NT P 2C P 2D P",
    "2H": "1NT P 2C P 2H P",
    "2S": "1NT P 2C P 2S P",
}
_FIXTURE_SOURCE = KnowledgeSource(
    "bidding/conventions/responses/stayman", "Responder's Continuations"
)


@dataclass(frozen=True, slots=True)
class StaymanGameGoingAuditFixture:
    """Explicit policy fixture; deliberately has no hand-strength classifier."""

    policy_id: str = "benchmark.fixture.stayman.game-going"

    def assess(self, context: BiddingContext) -> StaymanContinuationStrengthAssessment:
        return StaymanContinuationStrengthAssessment(
            self.policy_id,
            StaymanContinuationStrength.GAME_GOING,
            "Explicit deterministic Phase 12E/12F benchmark classification.",
            (_FIXTURE_SOURCE,),
        )


@dataclass(frozen=True, slots=True)
class StaymanGameGoingAudit:
    start_seed: int
    deal_count: int
    current_production_endpoint_counts: dict[str, int]
    fixture_supported_endpoint_counts: dict[str, int]
    opener_both_major_abstentions: int
    game_going_fixture_count_audited: int
    responder_holding_counts: dict[str, dict[str, int]]
    branch_classification_counts: dict[str, int]
    candidate_calls_found: tuple[str, ...]
    source_safe_calls: dict[str, bool]
    unresolved_blockers: tuple[str, ...]
    source_certainty_matrix: tuple[dict[str, object], ...]
    recommendation: str
    recommended_phase12f_direction: str
    default_registry_has_stayman_continuation_policy: bool
    production_route_count: int
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_stayman_gamegoing_audit(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StaymanGameGoingAudit:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    current = Counter(
        case.result.final_auction
        for case in baseline.batch.cases
        if case.result.final_auction in STAYMAN_ENDPOINTS.values()
    )
    one_notrump_stops = tuple(
        case for case in baseline.batch.cases if case.result.final_auction == "1NT P"
    )
    opener_engine = create_sayc_one_notrump_stayman_opener_response_engine()
    endpoint_counts = Counter()
    holdings: dict[str, Counter[str]] = {
        call: Counter() for call in STAYMAN_ENDPOINTS
    }
    both_major_abstentions = 0
    fixture = StaymanGameGoingAuditFixture()
    fixture_registry = PolicyRegistry.from_stayman_continuation_strength_policies(
        (fixture,)
    )
    fixture_system = SystemContext.from_mapping(
        "SAYC",
        {STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION: fixture.policy_id},
    )

    for case in one_notrump_stops:
        inquiry = Auction(Seat.NORTH, ("1NT", "P", "2C", "P"))
        opener_context = BiddingContext.create(
            hand=case.deal.hand(Seat.NORTH),
            auction=inquiry,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        result = opener_engine.evaluate(opener_context)
        if result.recommended_call is None:
            both_major_abstentions += 1
            continue
        call = result.recommended_call.serialize()
        endpoint_counts[call] += 1
        endpoint = Auction(Seat.NORTH, ("1NT", "P", "2C", "P", call, "P"))
        responder_context = BiddingContext.create(
            hand=case.deal.hand(Seat.SOUTH),
            auction=endpoint,
            vulnerability=Vulnerability.NONE,
            system=fixture_system,
        )
        assessment = assess_configured_stayman_continuation_strength(
            responder_context, fixture_registry
        )
        if (
            assessment is None
            or assessment.classification is not StaymanContinuationStrength.GAME_GOING
        ):
            raise AssertionError("benchmark fixture did not classify GAME_GOING")
        responder = case.deal.hand(Seat.SOUTH)
        hearts = sum(card.suit is Suit.HEARTS for card in responder.cards)
        spades = sum(card.suit is Suit.SPADES for card in responder.cards)
        holdings[call][_holding_key(hearts, spades, call)] += 1

    two_h_fit = sum(
        count for key, count in holdings["2H"].items() if key.startswith("fit:")
    )
    two_s_fit = sum(
        count for key, count in holdings["2S"].items() if key.startswith("fit:")
    )
    two_h_no_fit = endpoint_counts["2H"] - two_h_fit
    two_s_no_fit = endpoint_counts["2S"] - two_s_fit
    matrix = (
        _row("1NT-P-2C-P-2D-P", endpoint_counts["2D"], "any audited holding", "3NT", "SOURCE_INSUFFICIENT", "The source also permits minor game or slam according to distribution and gives no complete precedence."),
        _row("1NT-P-2C-P-2H-P", two_h_fit, "responder has 4+ hearts", "4H", "ARCHITECTURE_REQUIRED", "The call is source-explicit, but BridgeLab has no Stayman continuation strength-policy abstraction."),
        _row("1NT-P-2C-P-2H-P", two_h_no_fit, "responder has fewer than 4 hearts", "3NT / other", "SOURCE_INSUFFICIENT", "No exact no-fit GAME_GOING call or shape precedence is defined."),
        _row("1NT-P-2C-P-2S-P", two_s_fit, "responder has 4+ spades", "4S", "ARCHITECTURE_REQUIRED", "The call is source-explicit, but BridgeLab has no Stayman continuation strength-policy abstraction."),
        _row("1NT-P-2C-P-2S-P", two_s_no_fit, "responder has fewer than 4 spades", "3NT / other", "SOURCE_INSUFFICIENT", "No exact no-fit GAME_GOING call or shape precedence is defined."),
    )
    classification_counts = Counter(row["source_status"] for row in matrix)
    all_statuses = (
        "SOURCE_EXECUTABLE",
        "POLICY_REQUIRED",
        "SOURCE_INSUFFICIENT",
        "ARCHITECTURE_REQUIRED",
        "TERMINAL",
        "ALREADY_ROUTED",
    )
    router = create_standard_sayc_router()
    return StaymanGameGoingAudit(
        start_seed=start_seed,
        deal_count=deal_count,
        current_production_endpoint_counts={
            call: current[auction] for call, auction in STAYMAN_ENDPOINTS.items()
        },
        fixture_supported_endpoint_counts={
            call: endpoint_counts[call] for call in STAYMAN_ENDPOINTS
        },
        opener_both_major_abstentions=both_major_abstentions,
        game_going_fixture_count_audited=sum(endpoint_counts.values()),
        responder_holding_counts={
            call: dict(sorted(holdings[call].items())) for call in STAYMAN_ENDPOINTS
        },
        branch_classification_counts={
            status: classification_counts[status] for status in all_statuses
        },
        candidate_calls_found=("3NT", "4H", "4S", "minor-suit game", "slam exploration"),
        source_safe_calls={"3NT_after_2D": False, "4H_after_heart_fit": True, "4S_after_spade_fit": True},
        unresolved_blockers=(
            "No complete GAME_GOING precedence after a 2D denial.",
            "No exact continuation when opener's shown major does not fit responder.",
            "Five-card/other-major and unusual-shape exceptions are not resolved.",
            "The production architecture has no explicit Stayman continuation strength policy.",
            "The existing opener response abstains with both four-card majors (36 fixture positions).",
        ),
        source_certainty_matrix=matrix,
        recommendation="D. DEFER THIS FAMILY",
        recommended_phase12f_direction=(
            "Design and audit a non-default Stayman continuation strength/state policy boundary, "
            "scoped first to the source-complete major-fit GAME_GOING branches (4H and 4S); "
            "keep all no-fit branches deferred."
        ),
        default_registry_has_stayman_continuation_policy=bool(
            PolicyRegistry().stayman_continuation_strength_policy_ids
        ),
        production_route_count=len(router.routes),
    )


def _holding_key(hearts: int, spades: int, opener_call: str) -> str:
    fit = hearts >= 4 if opener_call == "2H" else spades >= 4 if opener_call == "2S" else False
    other = spades >= 4 if opener_call == "2H" else hearts >= 4 if opener_call == "2S" else hearts >= 4 or spades >= 4
    return f"{'fit' if fit else 'no_fit'}:other_major_{'>=4' if other else '<4'}"


def _row(endpoint, count, condition, call, status, blocker):
    return {
        "auction_endpoint": endpoint,
        "benchmark_count": count,
        "responder_holding_condition": condition,
        "candidate_call": call,
        "source_status": status,
        "executable": status == "SOURCE_EXECUTABLE",
        "blocker": blocker,
        "recommended_action": "defer" if status == "SOURCE_INSUFFICIENT" else "add architecture only in a later phase",
    }


def write_stayman_audit_artifacts(
    audit: StaymanGameGoingAudit, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12e_1nt_stayman_gamegoing_audit.json"
    markdown_path = output_dir / "bridgelab_phase12e_1nt_stayman_gamegoing_audit.md"
    json_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = "\n".join(
        "| {auction_endpoint} | {benchmark_count} | {responder_holding_condition} | {candidate_call} | {source_status} | {executable} | {blocker} | {recommended_action} |".format(**row)
        for row in audit.source_certainty_matrix
    )
    counts = audit.fixture_supported_endpoint_counts
    classes = audit.branch_classification_counts
    markdown_path.write_text(
        f"""# Phase 12E — 1NT Stayman GAME_GOING Responder Continuation Audit

## Deterministic sample

- seeds 1–10,000
- ordinary production endpoints: 2D=0, 2H=0, 2S=0
- fixture-supported Stayman endpoints: 2D={counts['2D']}, 2H={counts['2H']}, 2S={counts['2S']}
- opener both-major abstentions: {audit.opener_both_major_abstentions}
- GAME_GOING audited: {audit.game_going_fixture_count_audited}

## Source-certainty matrix

| Auction endpoint | Count | Responder holding | Candidate | Source status | Executable? | Blocker | Action |
|---|---:|---|---|---|---|---|---|
{rows}

## Findings after 2D

The source gives 3NT as a no-major-fit game example, but its general text also
allows 2NT, minor-suit game, or slam exploration according to strength and
distribution. GAME_GOING removes 2NT, but it does not resolve minor-game, slam,
five-card-major, or unusual-shape precedence. Therefore 3NT is not executable
as a general deterministic continuation.

## Findings after 2H

With 4+ responder hearts, the source-explicit major-fit call is 4H. Without a
heart fit, the frozen source does not select 3NT or another exact call. Holdings
in the other major and unusual shapes remain unresolved.

## Findings after 2S

With 4+ responder spades, the symmetric source-explicit call is 4S. Without a
spade fit, the frozen source does not select 3NT or another exact call.

## Exact source-safe calls

- 3NT after 2D generally: NO
- 4H after an established heart fit: YES, but architecture is required
- 4S after an established spade fit: YES, but architecture is required

## Branch classification totals

{chr(10).join(f'- {name}: {value}' for name, value in classes.items())}

## Recommendation

**{audit.recommendation}.** The complete family remains source-incomplete.

Recommended Phase 12F direction: {audit.recommended_phase12f_direction}

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12E
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_stayman_audit_artifacts(run_stayman_gamegoing_audit(), Path.cwd())
