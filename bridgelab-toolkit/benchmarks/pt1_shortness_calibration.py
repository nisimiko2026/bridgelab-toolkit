"""Run seeded PT-1 structural cohorts and retain each complete deal.

With no operational trick solver, outcome statistics are intentionally null.
Run from repository root: python -m benchmarks.pt1_shortness_calibration.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from enum import Enum
import gzip
import json
from pathlib import Path
from time import perf_counter

from bridge.playing_trick_calibration import (
    ShortnessKind, TRUMP_STRUCTURES, run_calibration,
)


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def run(*, seed: int, primary_target: int, secondary_target: int,
        output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    case_path = output_dir / "pt1_cases.jsonl.gz"
    batches = []
    strata: dict[tuple[tuple[int, int], ShortnessKind], Counter[tuple[object, ...]]] = {}
    with gzip.open(case_path, "wt", encoding="utf-8") as stream:
        for family_index, structure in enumerate(TRUMP_STRUCTURES):
            primary_kind = (ShortnessKind.EQUAL_HAND_SINGLETON if structure == (5, 5)
                            else ShortnessKind.SHORT_HAND_SINGLETON)
            kinds = (primary_kind, ShortnessKind.RECIPROCAL_SINGLETONS, ShortnessKind.BASELINE)
            if structure != (5, 5):
                kinds += (ShortnessKind.LONG_HAND_SINGLETON,)
            for kind_index, kind in enumerate(kinds):
                target = primary_target if kind is primary_kind else secondary_target
                cohort_seed = seed + family_index * 1_000_000 + kind_index * 100_000
                start = perf_counter()
                batch = run_calibration(structure, kind, seed=cohort_seed,
                                        accepted_target=target)
                elapsed = perf_counter() - start
                strata[(structure, kind)] = Counter(case.comparison_stratum() for case in batch.records)
                for case in batch.records:
                    stream.write(json.dumps(_jsonable(asdict(case)), separators=(",", ":")) + "\n")
                summary = batch.summary()
                summary["runtime_seconds"] = round(elapsed, 3)
                batches.append(summary)
    def comparison(group: tuple[tuple[int, int], ...], kind: ShortnessKind) -> dict[str, object]:
        def cohort_kind(structure: tuple[int, int]) -> ShortnessKind:
            return (ShortnessKind.EQUAL_HAND_SINGLETON
                    if structure == (5, 5) and kind is ShortnessKind.SHORT_HAND_SINGLETON
                    else kind)
        cohorts = [strata[(structure, cohort_kind(structure))] for structure in group]
        common = set.intersection(*(set(cohort) for cohort in cohorts))
        return {
            "shared_observable_strata": len(common),
            "cases_in_shared_strata": {
                f"{structure[0]}-{structure[1]}": sum(strata[(structure, cohort_kind(structure))][key]
                                                    for key in common)
                for structure in group
            },
            "matched_outcome_status": "unavailable-no-double-dummy-solver",
            "separation_flag": "unavailable-no-trick-outcomes",
        }
    comparisons = {
        "six_three_vs_five_four": {
            "one_singleton": comparison(((6, 3), (5, 4)), ShortnessKind.SHORT_HAND_SINGLETON),
            "reciprocal_singletons": comparison(((6, 3), (5, 4)), ShortnessKind.RECIPROCAL_SINGLETONS),
        },
        "seven_three_vs_six_four_vs_five_five": {
            "one_singleton": comparison(((7, 3), (6, 4), (5, 5)), ShortnessKind.SHORT_HAND_SINGLETON),
            "reciprocal_singletons": comparison(((7, 3), (6, 4), (5, 5)), ShortnessKind.RECIPROCAL_SINGLETONS),
        },
    }
    result = {
        "seed": seed,
        "sampling_method": "combinatorially weighted conditioned partnership side lengths; uniformly shuffled defender residual cards",
        "primary_target_per_structure": primary_target,
        "secondary_target_per_structure_per_kind": secondary_target,
        "equal_fit_long_hand_singleton": "not-applicable; 5-5 has no longer or shorter hand",
        "solver_status": "unavailable",
        "comparison_strata": "total trumps, two-point HCP band, exact combined trump honors, side-honor count, potential ruffable losers, side-ace entry count, unordered defender trump split",
        "all_outcome_separation_flags": "unavailable; no trick observations or confidence intervals",
        "total_generated": sum(item["generated"] for item in batches),
        "total_accepted": sum(item["accepted"] for item in batches),
        "batches": batches,
        "structural_comparisons": comparisons,
        "case_file": case_path.name,
    }
    (output_dir / "pt1_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument("--primary-target", type=int, default=8000)
    parser.add_argument("--secondary-target", type=int, default=1000)
    parser.add_argument("--output-dir", type=Path, default=Path("output/pt1_shortness"))
    args = parser.parse_args()
    result = run(seed=args.seed, primary_target=args.primary_target,
                 secondary_target=args.secondary_target, output_dir=args.output_dir)
    print(json.dumps({"total_generated": result["total_generated"],
                      "total_accepted": result["total_accepted"],
                      "summary": str(args.output_dir / "pt1_summary.json"),
                      "cases": str(args.output_dir / "pt1_cases.jsonl.gz")}, indent=2))


if __name__ == "__main__":
    main()
