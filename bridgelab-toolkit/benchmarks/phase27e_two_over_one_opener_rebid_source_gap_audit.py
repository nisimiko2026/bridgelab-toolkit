"""Phase 27E audit of Two-over-One opener-rebid source gaps.

This module measures existing routed behavior and frozen-source sufficiency only.
It does not add bidding rules, routes, policies, treatments, or defaults.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    Auction,
    BiddingContext,
    Hand,
    Seat,
    SystemContext,
    Vulnerability,
    create_standard_sayc_router,
)

ARTICLE = "bidding/systems/2-over-1"
PROBE_HAND = "AKQJ9.KQ3.JT8.32"

CANONICAL_CASES = (
    {
        "auction": ("1H", "P", "2C", "P"),
        "auction_text": "1H-P-2C-P",
        "route_id": "sayc.2over1.opener.1h.2c",
        "production_coverage": "NONE",
        "source_status": "SOURCE_INSUFFICIENT",
        "decision": "DEFER",
        "source_finding": "The frozen source gives no exact opener-rebid contract for the 1H-2C branch.",
        "blocker": "No source-explicit call, shape threshold, suit-ordering rule, support contract, own-suit contract, or balanced range is defined for this exact canonical auction.",
    },
    {
        "auction": ("1H", "P", "2D", "P"),
        "auction_text": "1H-P-2D-P",
        "route_id": "sayc.2over1.opener.1h.2d",
        "production_coverage": "PARTIAL",
        "source_status": "SOURCE_PARTIAL",
        "decision": "KEEP_EXISTING_RULES",
        "source_finding": "The frozen source explicitly supports the 2S second-suit example with five or more hearts and four or more spades. Balanced evidence is tracked separately and remains conservative.",
        "blocker": "The source does not define a complete opener-rebid table for every shape and strength in this auction.",
    },
    {
        "auction": ("1S", "P", "2C", "P"),
        "auction_text": "1S-P-2C-P",
        "route_id": "sayc.2over1.opener.1s.2c",
        "production_coverage": "PARTIAL",
        "source_status": "SOURCE_PARTIAL",
        "decision": "KEEP_EXISTING_RULES",
        "source_finding": "The frozen source explicitly supports selected 2D second-suit, 3C support, and objective six-spade 2S branches.",
        "blocker": "The source does not define a complete opener-rebid table or a general precedence rule between multiple available second suits.",
    },
    {
        "auction": ("1S", "P", "2D", "P"),
        "auction_text": "1S-P-2D-P",
        "route_id": "sayc.2over1.opener.1s.2d",
        "production_coverage": "NONE",
        "source_status": "SOURCE_INSUFFICIENT",
        "decision": "DEFER",
        "source_finding": "The frozen source gives no exact opener-rebid contract for the 1S-2D branch.",
        "blocker": "No source-explicit call, shape threshold, suit-ordering rule, support contract, own-suit contract, or balanced range is defined for this exact canonical auction.",
    },
)


@dataclass(frozen=True, slots=True)
class TwoOverOneOpenerRebidSourceGapAudit:
    article: str
    canonical_family_count: int
    route_count: int
    cases: tuple[dict[str, object], ...]
    unsupported_routes: tuple[str, ...]
    partially_supported_routes: tuple[str, ...]
    all_routes_reachable: bool
    unsupported_all_abstain: bool
    production_rules_added: int = 0
    routes_added: int = 0
    policies_added: int = 0
    production_defaults_changed: bool = False
    knowledge_markdown_changed: int = 0
    decision: str = "DEFER UNSUPPORTED TWO-OVER-ONE OPENER REBIDS"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _context(calls: tuple[str, ...]) -> BiddingContext:
    return BiddingContext.create(
        hand=Hand.parse(PROBE_HAND),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", {"two_over_one": "game_force"}),
    )


def run_two_over_one_opener_rebid_source_gap_audit() -> TwoOverOneOpenerRebidSourceGapAudit:
    router = create_standard_sayc_router()
    rows: list[dict[str, object]] = []
    unsupported_routes: list[str] = []
    partial_routes: list[str] = []
    all_routes_reachable = True
    unsupported_all_abstain = True

    for spec in CANONICAL_CASES:
        context = _context(spec["auction"])
        match = router.match(context)
        result = router.evaluate(context)
        reached_route = None if match is None else match.route_id
        action = "ABSTAIN" if result.recommended_call is None else result.recommended_call.serialize()
        route_reachable = reached_route == spec["route_id"]
        all_routes_reachable = all_routes_reachable and route_reachable

        if spec["production_coverage"] == "NONE":
            unsupported_routes.append(spec["route_id"])
            unsupported_all_abstain = unsupported_all_abstain and route_reachable and action == "ABSTAIN"
        else:
            partial_routes.append(spec["route_id"])

        rows.append({
            "auction": spec["auction_text"],
            "expected_route": spec["route_id"],
            "route_reached": reached_route,
            "route_reachable": route_reachable,
            "production_coverage": spec["production_coverage"],
            "source_status": spec["source_status"],
            "source_finding": spec["source_finding"],
            "blocker": spec["blocker"],
            "current_probe_action": action,
            "decision": spec["decision"],
        })

    return TwoOverOneOpenerRebidSourceGapAudit(
        article=ARTICLE,
        canonical_family_count=len(CANONICAL_CASES),
        route_count=len(router.routes),
        cases=tuple(rows),
        unsupported_routes=tuple(unsupported_routes),
        partially_supported_routes=tuple(partial_routes),
        all_routes_reachable=all_routes_reachable,
        unsupported_all_abstain=unsupported_all_abstain,
    )


def write_artifacts(audit: TwoOverOneOpenerRebidSourceGapAudit, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "bridgelab_phase27e_two_over_one_opener_rebid_source_gap_audit.json"
    markdown_path = output / "bridgelab_phase27e_two_over_one_opener_rebid_source_gap_audit.md"

    json_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows = "\n".join(
        "| {auction} | {expected_route} | {production_coverage} | {source_status} | {current_probe_action} | {decision} |".format(**row)
        for row in audit.cases
    )

    markdown_path.write_text(
        f"""# Phase 27E - Two-over-One Opener Rebid Source-Gap Audit

## Scope

This audit measures the four canonical uncontested Two-over-One opener-rebid auctions under explicit `two_over_one=game_force`.

It does not add bidding rules, routes, policies, treatments, defaults, or knowledge content.

Frozen source: `{audit.article}` - `Opener's Rebids`.

## Canonical family matrix

| Auction | Route | Production coverage | Source status | Current probe action | Decision |
|---|---|---|---|---|---|
{rows}

## Source finding

The frozen source gives the general opener-rebid priority:

1. show a second suit;
2. support responder;
3. rebid opener's own suit;
4. make a balanced rebid.

BridgeLab already implements only the source-explicit deterministic branches. It does not infer a complete rebid table from that priority list.

`1H-P-2C-P` and `1S-P-2D-P` have canonical routes but no exact frozen-source contract for a production opener rebid. They therefore remain intentionally routed and abstaining.

`1H-P-2D-P` and `1S-P-2C-P` retain their existing partial source-grounded production coverage. No broader semantics are inferred from those examples.

The single probe hand is used only to verify route reachability and
unsupported-route abstention. An `ABSTAIN` result on a partially supported
route does not mean that the route has no executable production branches.

## Router guards

- Canonical family count: {audit.canonical_family_count}
- Production route count: {audit.route_count}
- All four canonical routes reachable: {audit.all_routes_reachable}
- Unsupported canonical routes all abstain: {audit.unsupported_all_abstain}
- Unsupported routes: {audit.unsupported_routes}
- Partially supported routes: {audit.partially_supported_routes}

## Decision

**{audit.decision}.**

Do not add opener-rebid recommendations for `1H-P-2C-P` or `1S-P-2D-P` until a frozen source supplies an exact executable contract.

Guards: production rules added={audit.production_rules_added}; routes added={audit.routes_added}; policies added={audit.policies_added}; defaults changed={audit.production_defaults_changed}; knowledge Markdown changes={audit.knowledge_markdown_changed}.
""",
        encoding="utf-8",
    )

    return markdown_path, json_path


if __name__ == "__main__":
    write_artifacts(run_two_over_one_opener_rebid_source_gap_audit(), Path.cwd())
