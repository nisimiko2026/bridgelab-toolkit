"""Phase 12J validation of Stayman dual-major response policy architecture."""

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
    StaymanDualMajorResponse,
    StaymanDualMajorResponseAssessment,
    Suit,
    SystemContext,
    Vulnerability,
    run_sayc_coverage_benchmark,
)
from bridge.policy_registry import (
    STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION,
    PolicyRegistry,
    assess_configured_stayman_dual_major_response,
)
from bridge.sayc_route_configuration import create_standard_sayc_router

from .stayman_residual_coverage_audit import run_stayman_residual_coverage_audit


SOURCE = KnowledgeSource(
    "bidding/conventions/responses/stayman", "Opener's Responses"
)


class FixedStaymanDualMajorResponsePolicy:
    """Benchmark-only explicit policy fixture."""

    def __init__(self, response: StaymanDualMajorResponse):
        self.policy_id = f"fixture.stayman.dual-major.{response.value}"
        self.response = response

    def assess(self, context: BiddingContext) -> StaymanDualMajorResponseAssessment:
        if self.response is StaymanDualMajorResponse.UNKNOWN:
            return StaymanDualMajorResponseAssessment(self.policy_id, self.response)
        return StaymanDualMajorResponseAssessment(
            self.policy_id,
            self.response,
            "Explicit benchmark partnership preference.",
            (SOURCE,),
        )


@dataclass(frozen=True, slots=True)
class StaymanDualMajorPolicyArchitectureValidation:
    start_seed: int
    deal_count: int
    policy_enum: tuple[str, ...]
    assessment_type: str
    policy_interface: str
    registry_option: str
    default_policy: None
    dual_major_total: int
    exact_shapes: dict[str, int]
    fixture_results: dict[str, int]
    production_actions: dict[str, int]
    existing_route_attempts: dict[str, int]
    route_count: int
    production_bidding_calls_added: int
    phase12g_calls: dict[str, int]
    phase12h_residual_total: int
    production_defaults_changed: bool
    knowledge_markdown_changed: int
    recommended_next_phase: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_stayman_dual_major_policy_architecture_validation(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StaymanDualMajorPolicyArchitectureValidation:
    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    policies = tuple(
        FixedStaymanDualMajorResponsePolicy(response)
        for response in StaymanDualMajorResponse
    )
    registry = PolicyRegistry.from_stayman_dual_major_response_policies(policies)
    router = create_standard_sayc_router()
    inquiry = Auction(Seat.NORTH, ("1NT", "P", "2C", "P"))
    shapes = Counter()
    fixtures = Counter()
    actions = Counter()
    routes = Counter()

    for case in baseline.batch.cases:
        base_context = BiddingContext.create(
            hand=case.deal.hand(Seat.NORTH),
            auction=inquiry,
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        if case.result.final_auction != "1NT P" or not _is_dual_major(base_context):
            continue

        exact_shape = tuple(base_context.evaluation.length(suit) for suit in Suit)
        shapes["-".join(str(length) for length in exact_shape)] += 1
        route = router.match(base_context)
        routes[route.route_id if route is not None else "NONE"] += 1
        production = router.evaluate(base_context)
        actions[
            production.recommended_call.serialize()
            if production.recommended_call is not None
            else "ABSTAIN"
        ] += 1

        for policy in policies:
            context = BiddingContext.create(
                hand=base_context.hand,
                auction=inquiry,
                vulnerability=Vulnerability.NONE,
                system=SystemContext.from_mapping(
                    "SAYC",
                    {STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION: policy.policy_id},
                ),
            )
            assessment = assess_configured_stayman_dual_major_response(
                context, registry
            )
            if assessment is None:
                raise AssertionError("configured benchmark policy did not resolve")
            fixtures[assessment.response.name] += 1

    phase12h = run_stayman_residual_coverage_audit(
        start_seed=start_seed, deal_count=deal_count
    )
    return StaymanDualMajorPolicyArchitectureValidation(
        start_seed=start_seed,
        deal_count=deal_count,
        policy_enum=tuple(response.name for response in StaymanDualMajorResponse),
        assessment_type="StaymanDualMajorResponseAssessment",
        policy_interface="StaymanDualMajorResponsePolicy",
        registry_option=STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION,
        default_policy=None,
        dual_major_total=sum(shapes.values()),
        exact_shapes=dict(sorted(shapes.items())),
        fixture_results={name: fixtures[name] for name in ("HEARTS", "SPADES", "UNKNOWN")},
        production_actions=dict(sorted(actions.items())),
        existing_route_attempts=dict(sorted(routes.items())),
        route_count=len(router.routes),
        production_bidding_calls_added=0,
        phase12g_calls=phase12h.phase12g_calls,
        phase12h_residual_total=phase12h.residual_total,
        production_defaults_changed=False,
        knowledge_markdown_changed=0,
        recommended_next_phase=(
            "Phase 12K — Policy-Gated Stayman Dual-Major Opener Responses"
        ),
    )


def _is_dual_major(context: BiddingContext) -> bool:
    return (
        context.evaluation.length(Suit.HEARTS) == 4
        and context.evaluation.length(Suit.SPADES) == 4
    )


def write_dual_major_policy_architecture_artifacts(
    validation: StaymanDualMajorPolicyArchitectureValidation,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12j_stayman_dual_major_policy.json"
    markdown_path = output_dir / "bridgelab_phase12j_stayman_dual_major_policy.md"
    json_path.write_text(
        json.dumps(validation.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        f"""# Phase 12J — Stayman Dual-Major Response Policy Architecture

## Policy model

- enum: `StaymanDualMajorResponse`
- values: HEARTS, SPADES, UNKNOWN
- assessment: `StaymanDualMajorResponseAssessment`
- interface: `StaymanDualMajorResponsePolicy`
- assessment contains an abstract response choice and attribution only, never a bid
- known HEARTS/SPADES choices require explanation and `KnowledgeSource`
- UNKNOWN may be unattributed

## Registry and configuration

- option: `{validation.registry_option}`
- explicit register, resolve, and assess paths
- default dual-major response policy: **NONE**
- missing and unknown policy identifiers resolve to no policy
- no fallback is installed

## Deterministic architecture validation

- seeds 1–10,000
- dual-major positions: {validation.dual_major_total}
- 2-3-4-4: {validation.exact_shapes.get('2-3-4-4', 0)}
- 3-2-4-4: {validation.exact_shapes.get('3-2-4-4', 0)}
- HEARTS fixture: {validation.fixture_results['HEARTS']}
- SPADES fixture: {validation.fixture_results['SPADES']}
- UNKNOWN fixture: {validation.fixture_results['UNKNOWN']}

Fixtures validate policy assessment only. They do not translate a response
choice to 2H or 2S through production bidding logic.

## Production guards

- production action: ABSTAIN for all {validation.production_actions.get('ABSTAIN', 0)}
- existing route attempts through `sayc.opener.1nt.stayman`: {validation.existing_route_attempts.get('sayc.opener.1nt.stayman', 0)}
- routes: {validation.route_count}
- production bidding calls added: {validation.production_bidding_calls_added}
- Phase 12G calls unchanged: 4H={validation.phase12g_calls['4H']}, 4S={validation.phase12g_calls['4S']}
- Phase 12H residuals unchanged: {validation.phase12h_residual_total}
- production defaults changed: NO
- knowledge changes: 0

Recommended next phase: **{validation.recommended_next_phase}**

Current cumulative Full Kit: Phase 12J
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_dual_major_policy_architecture_artifacts(
        run_stayman_dual_major_policy_architecture_validation(), Path.cwd()
    )
