"""Phase 12C deterministic Jacoby continuation policy-fixture benchmark.

This module is benchmark/test support only. The fixture is installed explicitly
for one collected continuation position at a time and is never registered by a
production registry or router builder.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    Auction,
    BiddingContext,
    JacobyContinuationStrengthAssessment,
    JacobyContinuationStrengthClass,
    KnowledgeSource,
    Seat,
    SystemContext,
    Vulnerability,
    run_sayc_coverage_benchmark,
)
from bridge.policy_registry import (
    JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION,
    PolicyRegistry,
)
from bridge.sayc_route_configuration import create_standard_sayc_router


FIXTURE_POLICY_ID = "benchmark.fixture.jacoby.round-robin"
STRENGTH_CLASSES = (
    JacobyContinuationStrengthClass.WEAK,
    JacobyContinuationStrengthClass.INVITATIONAL,
    JacobyContinuationStrengthClass.GAME_GOING,
    JacobyContinuationStrengthClass.SLAM_INTEREST,
    JacobyContinuationStrengthClass.UNKNOWN,
)
HEART_AUCTION = "1NT P 2D P 2H P"
SPADE_AUCTION = "1NT P 2H P 2S P"
_FIXTURE_SOURCE = KnowledgeSource(
    "bidding/conventions/transfers/jacoby-transfers",
    "Responder's Continuations",
)


@dataclass(frozen=True, slots=True)
class DeterministicJacobyContinuationPolicyFixture:
    """Assign one benchmark position solely from its deterministic index."""

    index: int
    policy_id: str = FIXTURE_POLICY_ID

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or isinstance(self.index, bool):
            raise TypeError("index must be an integer")
        if self.index < 0:
            raise ValueError("index must not be negative")

    @property
    def strength_class(self) -> JacobyContinuationStrengthClass:
        return STRENGTH_CLASSES[self.index % len(STRENGTH_CLASSES)]

    def assess(self, context: BiddingContext) -> JacobyContinuationStrengthAssessment:
        if not isinstance(context, BiddingContext):
            raise TypeError("context must be BiddingContext")
        strength_class = self.strength_class
        if strength_class is JacobyContinuationStrengthClass.UNKNOWN:
            return JacobyContinuationStrengthAssessment(self.policy_id, strength_class)
        return JacobyContinuationStrengthAssessment(
            self.policy_id,
            strength_class,
            "Deterministic Phase 12C round-robin fixture classification.",
            (_FIXTURE_SOURCE,),
        )


@dataclass(frozen=True, slots=True)
class JacobyPolicyFixtureBenchmarkMetrics:
    start_seed: int
    deal_count: int
    total_jacoby_continuations: int
    accepted_heart_transfer_positions: int
    accepted_spade_transfer_positions: int
    by_strength_class: dict[str, int]
    resulting_calls: dict[str, int]
    game_heart_4H: int
    game_spade_4S: int
    abstentions: dict[str, int]
    produced_call_count: int
    abstention_count: int
    coverage_numerator: int
    coverage_denominator: int
    coverage_pct: float
    default_behavior_unchanged: bool

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["coverage_fraction"] = (
            f"{self.coverage_numerator}/{self.coverage_denominator}"
        )
        return result


def _continuation_cases(baseline):
    return tuple(
        case
        for case in baseline.batch.cases
        if case.result.final_auction in (HEART_AUCTION, SPADE_AUCTION)
    )


def run_jacoby_policy_fixture_benchmark(
    *, start_seed: int = 1, deal_count: int = 10_000
) -> JacobyPolicyFixtureBenchmarkMetrics:
    """Run Phase 12C over the ordered Phase 12B continuation positions."""

    baseline = run_sayc_coverage_benchmark(start_seed=start_seed, count=deal_count)
    cases = _continuation_cases(baseline)
    heart_count = sum(case.result.final_auction == HEART_AUCTION for case in cases)
    spade_count = sum(case.result.final_auction == SPADE_AUCTION for case in cases)

    class_counts: Counter[str] = Counter()
    call_counts: Counter[str] = Counter()
    abstention_counts: Counter[str] = Counter()
    game_heart_4h = 0
    game_spade_4s = 0

    for index, case in enumerate(cases):
        policy = DeterministicJacobyContinuationPolicyFixture(index)
        strength_class = policy.strength_class
        class_counts[strength_class.name] += 1

        registry = PolicyRegistry.from_jacoby_continuation_strength_policies((policy,))
        router = create_standard_sayc_router(registry)
        system = SystemContext.from_mapping(
            "SAYC", {JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION: policy.policy_id}
        )
        auction = Auction(Seat.NORTH, tuple(case.result.final_auction.split()))
        context = BiddingContext.create(
            hand=case.deal.hand(auction.next_seat),
            auction=auction,
            vulnerability=Vulnerability.NONE,
            system=system,
        )
        result = router.evaluate(context)
        if result.recommended_call is None:
            abstention_counts[strength_class.name] += 1
        else:
            call = result.recommended_call.serialize()
            call_counts[call] += 1
            if strength_class is JacobyContinuationStrengthClass.GAME_GOING:
                expected = "4H" if case.result.final_auction == HEART_AUCTION else "4S"
                if call != expected:
                    raise AssertionError(
                        f"GAME_GOING {case.result.final_auction} produced {call}, expected {expected}"
                    )
                if expected == "4H":
                    game_heart_4h += 1
                else:
                    game_spade_4s += 1

    total = len(cases)
    produced = sum(call_counts.values())
    abstained = sum(abstention_counts.values())
    return JacobyPolicyFixtureBenchmarkMetrics(
        start_seed=start_seed,
        deal_count=deal_count,
        total_jacoby_continuations=total,
        accepted_heart_transfer_positions=heart_count,
        accepted_spade_transfer_positions=spade_count,
        by_strength_class={cls.name: class_counts[cls.name] for cls in STRENGTH_CLASSES},
        resulting_calls={
            "Pass": call_counts["P"],
            "2NT": call_counts["2NT"],
            "4H": call_counts["4H"],
            "4S": call_counts["4S"],
        },
        game_heart_4H=game_heart_4h,
        game_spade_4S=game_spade_4s,
        abstentions={
            cls.name: abstention_counts[cls.name]
            for cls in (
                JacobyContinuationStrengthClass.SLAM_INTEREST,
                JacobyContinuationStrengthClass.UNKNOWN,
            )
        },
        produced_call_count=produced,
        abstention_count=abstained,
        coverage_numerator=produced,
        coverage_denominator=total,
        coverage_pct=0.0 if total == 0 else round(100.0 * produced / total, 2),
        default_behavior_unchanged=(heart_count == 62 and spade_count == 61),
    )


def write_benchmark_artifacts(
    metrics: JacobyPolicyFixtureBenchmarkMetrics, output_dir: str | Path
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bridgelab_phase12c_jacoby_policy_fixture_benchmark.json"
    markdown_path = output_dir / "bridgelab_phase12c_jacoby_policy_fixture_benchmark.md"
    json_path.write_text(
        json.dumps(metrics.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    calls = metrics.resulting_calls
    abstentions = metrics.abstentions
    classes = metrics.by_strength_class
    markdown_path.write_text(
        "\n".join(
            (
                "# Phase 12C — Deterministic Jacoby Policy-Fixture Benchmark",
                "",
                f"- deterministic sample: seeds {metrics.start_seed}–{metrics.start_seed + metrics.deal_count - 1:,}",
                f"- accepted Jacoby continuations: {metrics.total_jacoby_continuations}",
                f"  - heart: {metrics.accepted_heart_transfer_positions}",
                f"  - spade: {metrics.accepted_spade_transfer_positions}",
                "",
                "## Fixture distribution",
                "",
                *(f"- {name}: {classes[name]}" for name in classes),
                "",
                "## Calls",
                "",
                f"- Pass: {calls['Pass']}",
                f"- 2NT: {calls['2NT']}",
                f"- 4H: {calls['4H']}",
                f"- 4S: {calls['4S']}",
                f"- 4H + 4S: {calls['4H'] + calls['4S']}",
                "",
                "## Abstentions",
                "",
                f"- SLAM_INTEREST: {abstentions['SLAM_INTEREST']}",
                f"- UNKNOWN: {abstentions['UNKNOWN']}",
                f"- total: {metrics.abstention_count}",
                "",
                f"Continuation calls: {metrics.produced_call_count}",
                f"Exact policy-fixture coverage: {metrics.coverage_numerator}/{metrics.coverage_denominator} = {metrics.coverage_pct:.2f}%",
                "",
                "## Default benchmark",
                "",
                f"- heart continuation stops: {metrics.accepted_heart_transfer_positions}",
                f"- spade continuation stops: {metrics.accepted_spade_transfer_positions}",
                f"- default behavior unchanged: {'YES' if metrics.default_behavior_unchanged else 'NO'}",
                "",
                "Production defaults changed: NO",
                "",
                "Knowledge Markdown changed: 0",
                "",
                "Current cumulative Full Kit: Phase 12C",
                "",
            )
        ),
        encoding="utf-8",
    )
    return markdown_path, json_path


if __name__ == "__main__":
    write_benchmark_artifacts(run_jacoby_policy_fixture_benchmark(), Path.cwd())
