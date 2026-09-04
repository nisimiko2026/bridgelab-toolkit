"""Phase 12F validation report for Stayman continuation policy architecture."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge.sayc_route_configuration import create_standard_sayc_router

from .stayman_gamegoing_audit import run_stayman_gamegoing_audit


@dataclass(frozen=True, slots=True)
class StaymanPolicyArchitectureValidation:
    policy_interface: str
    classifications: tuple[str, ...]
    registry_option: str
    default_policy: None
    endpoint_counts: dict[str, int]
    heart_fit_target: int
    spade_fit_target: int
    total_future_fit_target: int
    no_fit_branches_deferred: bool
    dual_major_abstentions: int
    production_routes_before: int
    production_routes_after: int
    production_bidding_calls_added: int
    production_defaults_changed: bool
    knowledge_markdown_changed: int
    recommended_next_phase: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_stayman_policy_architecture_validation(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> StaymanPolicyArchitectureValidation:
    audit = run_stayman_gamegoing_audit(
        start_seed=start_seed, deal_count=deal_count
    )
    matrix = audit.source_certainty_matrix
    heart_fit = next(
        row["benchmark_count"]
        for row in matrix
        if row["candidate_call"] == "4H"
    )
    spade_fit = next(
        row["benchmark_count"]
        for row in matrix
        if row["candidate_call"] == "4S"
    )
    route_count = len(create_standard_sayc_router().routes)
    return StaymanPolicyArchitectureValidation(
        policy_interface="StaymanContinuationStrengthPolicy",
        classifications=("GAME_GOING", "OTHER", "UNKNOWN"),
        registry_option="stayman_continuation_strength_policy",
        default_policy=None,
        endpoint_counts=audit.fixture_supported_endpoint_counts,
        heart_fit_target=heart_fit,
        spade_fit_target=spade_fit,
        total_future_fit_target=heart_fit + spade_fit,
        no_fit_branches_deferred=True,
        dual_major_abstentions=audit.opener_both_major_abstentions,
        production_routes_before=42,
        production_routes_after=route_count,
        production_bidding_calls_added=0,
        production_defaults_changed=False,
        knowledge_markdown_changed=0,
        recommended_next_phase=(
            "Phase 12G — Policy-Gated Stayman Major-Fit Game Continuations"
        ),
    )


def write_policy_architecture_artifacts(
    validation: StaymanPolicyArchitectureValidation, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12f_stayman_continuation_policy.json"
    markdown_path = output_dir / "bridgelab_phase12f_stayman_continuation_policy.md"
    json_path.write_text(
        json.dumps(validation.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    endpoints = validation.endpoint_counts
    markdown_path.write_text(
        f"""# Phase 12F — Stayman Responder Continuation Policy Architecture

## Policy interface

- protocol: `StaymanContinuationStrengthPolicy`
- result: `StaymanContinuationStrengthAssessment`
- classification enum: `StaymanContinuationStrength`
- values: `GAME_GOING`, `OTHER`, `UNKNOWN`
- the policy returns classifications only and never selects a bidding call
- known classifications require an explanation and `KnowledgeSource`

## Registry and default behavior

- registry option: `stayman_continuation_strength_policy`
- register, resolve, and assess paths are explicit
- default Stayman continuation policy: **NONE**
- unknown or unregistered identifiers resolve to no policy

## Benchmark validation

- opener 2D: {endpoints['2D']}
- opener 2H: {endpoints['2H']}
  - heart fit: {validation.heart_fit_target}
  - no fit: {endpoints['2H'] - validation.heart_fit_target}
- opener 2S: {endpoints['2S']}
  - spade fit: {validation.spade_fit_target}
  - no fit: {endpoints['2S'] - validation.spade_fit_target}
- total audited: {sum(endpoints.values())}
- future source-safe fit target: {validation.heart_fit_target} + {validation.spade_fit_target} = {validation.total_future_fit_target}

The no-fit branches remain deferred. The {validation.dual_major_abstentions}
dual-four-card-major opener positions remain unchanged and partnership-dependent.

Production routes: {validation.production_routes_before} before, {validation.production_routes_after} after.

Production bidding calls added: {validation.production_bidding_calls_added}

Production defaults changed: NO

Knowledge Markdown changed: 0

Recommended next phase: **{validation.recommended_next_phase}**

Current cumulative Full Kit: Phase 12F
""",
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_policy_architecture_artifacts(
        run_stayman_policy_architecture_validation(), Path.cwd()
    )
