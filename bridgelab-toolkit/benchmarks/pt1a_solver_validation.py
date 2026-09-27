"""Small DDS-backed PT-1A validation of exact matched structural contrasts.

Default workload: 1,000 solver-complete primary cases per principal structure
and 400 matched reciprocal sets per comparison family. This is not PT-2.
Run with Python 3.12 and requirements-pt1a.txt installed.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from enum import Enum
import gzip
import json
from pathlib import Path
from statistics import mean, median, stdev
from time import perf_counter

from bridge.deals import Deal
from bridge.endplay_trick_solver import EndplayTrickSolver
from bridge.models import Seat, Suit
from bridge.playing_trick_calibration import (
    CalibrationCase, ShortnessKind, generate_conditioned_case,
)
from bridge.playing_trick_pairs import build_matched_set
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _solver_stats(values: list[int]) -> dict[str, object]:
    return {"solver_complete": len(values),
            "mean_solver_tricks": mean(values) if values else None,
            "median_solver_tricks": median(values) if values else None,
            "trick_distribution": dict(sorted(Counter(values).items()))}


def _delta_stats(values: list[int]) -> dict[str, object]:
    count = len(values)
    if not count:
        return {"matched_pairs": 0, "status": "unavailable-no-complete-pairs"}
    average = mean(values)
    sd = stdev(values) if count > 1 else 0.0
    half_width = 1.96 * sd / (count ** 0.5)
    return {
        "matched_pairs": count,
        "mean_delta_tricks": average,
        "median_delta_tricks": median(values),
        "sample_standard_deviation": sd,
        "mean_95_percent_normal_ci": [average - half_width, average + half_width],
        "p_delta_positive": sum(v > 0 for v in values) / count,
        "p_delta_zero": sum(v == 0 for v in values) / count,
        "p_delta_negative": sum(v < 0 for v in values) / count,
        "p_gain_ge_1": sum(v >= 1 for v in values) / count,
        "p_gain_ge_2": sum(v >= 2 for v in values) / count,
        "delta_distribution": dict(sorted(Counter(values).items())),
        "status": "solver-measured-paired-structural-contrast",
    }


def run(*, seed: int, primary_target: int = 1000,
        reciprocal_target: int = 400,
        output_dir: Path = Path("output/pt1a_solver_validation")) -> dict[str, object]:
    if primary_target < 1 or reciprocal_target < 1:
        raise ValueError("validation targets must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    solver = EndplayTrickSolver()
    case_path = output_dir / "pt1a_solver_cases.jsonl.gz"
    primary: dict[tuple[int, int], list[int]] = defaultdict(list)
    deltas: dict[str, list[int]] = defaultdict(list)
    reciprocal_deltas: dict[str, list[int]] = defaultdict(list)
    timings: list[float] = []
    statuses: Counter[str] = Counter()
    cohort_counts: dict[str, dict[str, int]] = {}
    began = perf_counter()
    with gzip.open(case_path, "wt", encoding="utf-8") as stream:
        def solve_record(case: CalibrationCase, cohort: str,
                         pair_id: str | None) -> TrickSolverResult:
            deal = Deal.parse(case.deal_id, seed=case.deal_seed)
            result = solver.solve(deal, Seat.NORTH, case.trump_suit)
            timings.append(result.elapsed_seconds)
            statuses[result.status.value] += 1
            measured = replace(case, double_dummy_tricks=result.maximum_declarer_tricks)
            stream.write(json.dumps(_jsonable({
                "cohort": cohort,
                "pair_id": pair_id,
                "case": asdict(measured),
                "solver": asdict(result),
            }), separators=(",", ":")) + "\n")
            return result

        def paired(source: tuple[int, int], kind: ShortnessKind,
                   target: int, start_seed: int, label: str) -> None:
            generated = accepted = shape_rejected = solver_rejected = 0
            while accepted < target:
                if generated >= target * 10:
                    raise RuntimeError(f"{label} target not reached")
                matched = build_matched_set(start_seed + generated, source, kind)
                generated += 1
                if matched is None:
                    shape_rejected += 1
                    continue
                results = [solve_record(case, label, matched.pair_id) for case in matched.cases]
                if not all(result.status is TrickSolverStatus.SUCCESS for result in results):
                    solver_rejected += 1
                    continue
                accepted += 1
                tricks = [result.maximum_declarer_tricks for result in results]
                assert all(isinstance(value, int) for value in tricks)
                if kind is ShortnessKind.SHORT_HAND_SINGLETON:
                    for case, value in zip(matched.cases, tricks):
                        primary[case.trump_structure].append(value)
                    target_deltas = deltas
                else:
                    target_deltas = reciprocal_deltas
                if source == (6, 3):
                    target_deltas["5-4_minus_6-3"].append(tricks[1] - tricks[0])
                else:
                    target_deltas["6-4_minus_7-3"].append(tricks[1] - tricks[0])
                    target_deltas["5-5_minus_6-4"].append(tricks[2] - tricks[1])
                    target_deltas["5-5_minus_7-3"].append(tricks[2] - tricks[0])
            cohort_counts[label] = {"generated": generated, "accepted_sets": accepted,
                                    "shape_rejected": shape_rejected,
                                    "solver_rejected": solver_rejected,
                                    "solver_complete_cases": accepted * (2 if source == (6, 3) else 3)}

        def standalone(structure: tuple[int, int], target: int,
                       start_seed: int) -> None:
            label = f"primary_{structure[0]}-{structure[1]}"
            generated = accepted = solver_rejected = 0
            while accepted < target:
                if generated >= target * 10:
                    raise RuntimeError(f"{label} target not reached")
                kind = (ShortnessKind.EQUAL_HAND_SINGLETON if structure == (5, 5)
                        else ShortnessKind.SHORT_HAND_SINGLETON)
                case = generate_conditioned_case(start_seed + generated, structure, kind)
                generated += 1
                result = solve_record(case, label, None)
                if result.status is TrickSolverStatus.SUCCESS:
                    assert result.maximum_declarer_tricks is not None
                    accepted += 1
                    primary[structure].append(result.maximum_declarer_tricks)
                else:
                    solver_rejected += 1
            cohort_counts[label] = {"generated": generated, "accepted_sets": accepted,
                                    "shape_rejected": 0,
                                    "solver_rejected": solver_rejected,
                                    "solver_complete_cases": accepted}

        paired((6, 3), ShortnessKind.SHORT_HAND_SINGLETON,
               primary_target, seed, "primary_6-3_vs_5-4")
        paired((7, 3), ShortnessKind.SHORT_HAND_SINGLETON,
               primary_target, seed + 1_000_000, "primary_7-3_vs_6-4_vs_5-5")
        for index, structure in enumerate(((5, 3), (7, 4), (6, 5))):
            standalone(structure, primary_target, seed + (index + 2) * 1_000_000)
        paired((6, 3), ShortnessKind.RECIPROCAL_SINGLETONS,
               reciprocal_target, seed + 5_000_000, "reciprocal_6-3_vs_5-4")
        paired((7, 3), ShortnessKind.RECIPROCAL_SINGLETONS,
               reciprocal_target, seed + 6_000_000, "reciprocal_7-3_vs_6-4_vs_5-5")
    wall_seconds = perf_counter() - began
    average_time = mean(timings)
    summary: dict[str, object] = {
        "seed": seed,
        "solver_implementation": solver.implementation,
        "solver_version": "0.5.12",
        "declarer": Seat.NORTH.value,
        "strain": Suit.SPADES.letter,
        "primary_target_per_structure": primary_target,
        "reciprocal_target_per_comparison_family": reciprocal_target,
        "solver_calls": len(timings),
        "solver_status_counts": dict(statuses),
        "mean_solver_seconds_per_call": average_time,
        "median_solver_seconds_per_call": median(timings),
        "total_solver_seconds": sum(timings),
        "validation_wall_seconds": wall_seconds,
        "runtime_projection_seconds": {
            "8000_per_structure_8_structures": 64_000 * average_time,
            "100000_per_structure_8_structures": 800_000 * average_time,
            "full_pt2_31_cohorts_at_100000_each": 3_100_000 * average_time,
        },
        "matching": {
            "exact_within_each_pair": [
                "partnership HCP", "total partnership trumps", "trump honors by hand",
                "side-suit honors by hand", "studied shortness suit and ruffable losers",
                "side-ace entry indicators by hand", "oriented defender trump split",
                "all 26 defender cards", "declarer", "trump suit",
            ],
            "bucketed_within_each_pair": [],
            "changed_exposure": "one low trump North-to-South and one low unstudied side card South-to-North per step",
            "prior_reciprocal_shared_strata": {"6-3_vs_5-4": 133, "7-3_vs_6-4_vs_5-5": 107},
            "new_reciprocal_complete_matched_sets": {
                "6-3_vs_5-4": reciprocal_target,
                "7-3_vs_6-4_vs_5-5": reciprocal_target,
            },
        },
        "cohorts": cohort_counts,
        "primary_solver_tricks": {
            f"{structure[0]}-{structure[1]}": _solver_stats(primary[structure])
            for structure in ((5, 3), (6, 3), (5, 4), (7, 3),
                              (6, 4), (5, 5), (7, 4), (6, 5))
        },
        "primary_paired_deltas": {name: _delta_stats(values) for name, values in deltas.items()},
        "reciprocal_paired_deltas": {
            name: _delta_stats(values) for name, values in reciprocal_deltas.items()},
        "interpretation": "DDS outcomes measure controlled trump-allocation contrasts; they are not NPT, APT, or final shortness coefficients.",
        "case_file": case_path.name,
    }
    (output_dir / "pt1a_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261001)
    parser.add_argument("--primary-target", type=int, default=1000)
    parser.add_argument("--reciprocal-target", type=int, default=400)
    parser.add_argument("--output-dir", type=Path, default=Path("output/pt1a_solver_validation"))
    args = parser.parse_args()
    result = run(seed=args.seed, primary_target=args.primary_target,
                 reciprocal_target=args.reciprocal_target, output_dir=args.output_dir)
    print(json.dumps({"solver_calls": result["solver_calls"],
                      "status_counts": result["solver_status_counts"],
                      "summary": str(args.output_dir / "pt1a_summary.json")}, indent=2))


if __name__ == "__main__":
    main()
