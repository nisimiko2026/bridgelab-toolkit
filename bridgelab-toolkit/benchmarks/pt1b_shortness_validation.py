"""PT-1B matched shortness validation; run under Python 3.12 with endplay/DDS.

This is a causal-contrast measurement, not a Playing-Trick coefficient fit.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from enum import Enum
import gzip
import json
from pathlib import Path
from statistics import mean, median, stdev
from time import perf_counter

from bridge.deals import Deal
from bridge.endplay_trick_solver import EndplayTrickSolver
from bridge.models import Seat, Suit
from bridge.playing_trick_calibration import ShortnessKind, generate_conditioned_case
from bridge.playing_trick_shortness_pairs import (
    reciprocal_candidates, select_direct_reciprocal_control,
    select_reciprocal_controls, select_singleton_control, singleton_candidates,
)
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus


STRUCTURES = ((5, 3), (6, 3), (5, 4), (7, 3), (6, 4), (5, 5))


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, frozenset):
        return [_jsonable(item) for item in sorted(value)]
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "serialize"):
        return value.serialize()
    return value


def delta_stats(values: list[int]) -> dict[str, object]:
    n = len(values)
    if not n:
        return {"n": 0, "status": "unavailable-no-complete-matches",
                "mean_delta": None, "median_delta": None,
                "sample_sd": None, "mean_95_percent_normal_ci": None,
                "p_positive": None, "p_zero": None, "p_negative": None,
                "p_ge_1": None, "p_le_minus_1": None}
    m = mean(values)
    sd = stdev(values) if n > 1 else 0.0
    half = 1.96 * sd / n ** 0.5
    return {"n": n, "status": "solver-measured-matched-shortness-contrast",
            "mean_delta": m, "median_delta": median(values), "sample_sd": sd,
            "mean_95_percent_normal_ci": [m - half, m + half],
            "p_positive": sum(x > 0 for x in values) / n,
            "p_zero": sum(x == 0 for x in values) / n,
            "p_negative": sum(x < 0 for x in values) / n,
            "p_ge_1": sum(x >= 1 for x in values) / n,
            "p_le_minus_1": sum(x <= -1 for x in values) / n,
            "distribution": dict(sorted(Counter(values).items()))}


def trump_quality(case) -> str:
    """Predeclared A=2,K=1,Q=1,J=0; weak <=1, medium 2-3, strong 4."""
    score = sum({"A": 2, "K": 1, "Q": 1}.get(rank, 0)
                for rank in case.trump_honor_control)
    return "weak" if score <= 1 else "medium" if score <= 3 else "strong"


def loser_bucket(losers: int) -> str:
    return str(losers) if losers < 3 else "3+"


def reciprocal_effects(r: int, north_removed: int, south_removed: int,
                       neither: int) -> dict[str, int]:
    """Four-corner additive interaction; positive means synergy."""
    return {
        "combined": r - neither,
        "remove_n_conditional": r - north_removed,
        "remove_s_conditional": r - south_removed,
        "n_alone": south_removed - neither,
        "s_alone": north_removed - neither,
        "interaction": r - north_removed - south_removed + neither,
    }


def refresh_stratification(output_dir: Path) -> dict[str, object]:
    """Rebuild within-cohort strata from recorded DDS-backed case rows."""
    summary_path = output_dir / "pt1b_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    grouped: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    reciprocal_grouped: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list))
    with gzip.open(output_dir / summary["case_file"], "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if isinstance(row.get("effects"), dict):
                source_case = row["case"]
                effects = row["effects"]
                split = "-".join(map(str, sorted(source_case["defender_trump_split"])))
                score = sum({"A": 2, "K": 1, "Q": 1}.get(rank, 0)
                            for rank in source_case["trump_honor_control"])
                quality = "weak" if score <= 1 else "medium" if score <= 3 else "strong"
                for effect, value in effects.items():
                    reciprocal_grouped["defender_split"][
                        f'{row["cohort"]}|{split}|{effect}'].append(value)
                    reciprocal_grouped["trump_quality"][
                        f'{row["cohort"]}|{quality}|{effect}'].append(value)
                    for short in source_case["short_suits"]:
                        hand = short["hand"]
                        loser = loser_bucket(short["ruffable_losers"])
                        for feature, feature_value in (
                            ("loser_bucket", loser),
                            ("opposite_length", short["opposite_length"]),
                            ("natural_winners", short["certain_top_rank_winners"]),
                        ):
                            reciprocal_grouped[feature][
                                f'{row["cohort"]}|{hand}|{feature_value}|{effect}'].append(value)
            features = row.get("features")
            delta = row.get("delta_doubleton")
            if features is None or not isinstance(delta, int):
                continue
            source_case = row["case"]
            source_deal = Deal.parse(source_case["deal_id"])
            studied = {(Seat.parse(item["hand"]), Suit(item["suit"]))
                       for item in source_case["short_suits"]}
            extra = tuple((seat.value, suit.letter, source_deal.hand(seat).length(suit))
                          for seat in (Seat.NORTH, Seat.SOUTH) for suit in Suit
                          if suit is not Suit.SPADES and (seat, suit) not in studied
                          and source_deal.hand(seat).length(suit) < 2)
            context = "no_other_side_shortness" if not extra else "additional_side_shortness"
            for feature in ("loser_bucket", "defender_split", "trump_quality",
                            "opposite_length", "natural_winners"):
                grouped[feature][f'{features["cohort"]}|{features[feature]}'].append(delta)
            grouped["location_by_loser"][
                f'{features["location"]}|{features["loser_bucket"]}'].append(delta)
            grouped["source_context"][context].append(delta)
            grouped["source_context_by_cohort"][f'{features["cohort"]}|{context}'].append(delta)
            grouped["additional_short_suit_count"][str(len(extra))].append(delta)
    summary["within_cohort_strata"] = {
        feature: {key: delta_stats(values) for key, values in sorted(rows.items())}
        for feature, rows in sorted(grouped.items())}
    summary["reciprocal_within_cohort_strata"] = {
        feature: {key: delta_stats(values) for key, values in sorted(rows.items())}
        for feature, rows in sorted(reciprocal_grouped.items())}
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    return summary


def record_exchange_sensitivity(output_dir: Path) -> dict[str, object]:
    """Replay the declared sensitivity subset with full DDS provenance."""
    summary_path = output_dir / "pt1b_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    subset = int(summary["sensitivity_sources_per_primary_cohort"])
    selected: Counter[str] = Counter()
    records: list[dict[str, object]] = []
    solver = EndplayTrickSolver()
    statuses: Counter[str] = Counter()
    calls = 0
    started = perf_counter()
    provenance_path = output_dir / "pt1b_exchange_sensitivity.jsonl.gz"
    temporary_path = output_dir / "pt1b_exchange_sensitivity.jsonl.gz.tmp"
    prior_records = {(item["cohort"], item["source_seed"]): item
                     for item in summary["exchange_sensitivity"]["records"]}
    with gzip.open(output_dir / summary["case_file"], "rt", encoding="utf-8") as source_stream, \
            gzip.open(temporary_path, "wt", encoding="utf-8") as provenance_stream:
        for line in source_stream:
            row = json.loads(line)
            if not isinstance(row.get("delta_doubleton"), int):
                continue
            cohort = row["cohort"]
            if selected[cohort] >= subset:
                continue
            selected[cohort] += 1
            case = row["case"]
            deal = Deal.parse(case["deal_id"], seed=case["deal_seed"])
            short = case["short_suits"][0]
            candidates = singleton_candidates(deal, Seat.parse(short["hand"]),
                                               Suit(short["suit"]), Suit(case["trump_suit"]))
            source_solver = row["solvers"]["source"]
            assert source_solver["status"] == TrickSolverStatus.SUCCESS.value
            deltas: list[int] = []
            for index, (variant, exchange) in enumerate(candidates):
                result = solver.solve(variant, Seat.NORTH, Suit.SPADES)
                calls += 1
                statuses[result.status.value] += 1
                delta = (int(source_solver["maximum_declarer_tricks"])
                         - result.maximum_declarer_tricks
                         if result.status is TrickSolverStatus.SUCCESS else None)
                if delta is not None:
                    deltas.append(delta)
                provenance_stream.write(json.dumps(_jsonable({
                    "cohort": cohort, "source_seed": case["deal_seed"],
                    "candidate_exchange_count": len(candidates),
                    "candidate_index": index, "exchange": asdict(exchange),
                    "control_deal_id": variant.serialize(),
                    "source_solver": source_solver, "control_solver": asdict(result),
                    "delta": delta,
                }), separators=(",", ":")) + "\n")
            records.append({"cohort": cohort, "source_seed": case["deal_seed"],
                            "candidate_exchange_count": len(candidates),
                            "solver_complete_exchanges": len(deltas),
                            "mean_delta": mean(deltas) if deltas else None,
                            "min_delta": min(deltas) if deltas else None,
                            "max_delta": max(deltas) if deltas else None,
                            "within_source_sample_sd": (stdev(deltas) if len(deltas) > 1
                                else 0.0 if deltas else None)})
            prior = prior_records.get((cohort, case["deal_seed"]))
            if prior is None or any(records[-1][key] != prior[key] for key in (
                "candidate_exchange_count", "solver_complete_exchanges",
                "mean_delta", "min_delta", "max_delta", "within_source_sample_sd")):
                raise RuntimeError("sensitivity replay disagrees with saved source summary")
    if len(records) != len(prior_records):
        raise RuntimeError("sensitivity replay did not cover every saved source")
    temporary_path.replace(provenance_path)
    complete = [x for x in records if x["min_delta"] is not None]
    summary["exchange_sensitivity"] = {
        "sources": len(records),
        "all_exchange_solver_complete_sources": sum(
            x["candidate_exchange_count"] == x["solver_complete_exchanges"]
            for x in records),
        "mean_within_source_sd": mean(x["within_source_sample_sd"]
                                      for x in complete) if complete else None,
        "mean_within_source_range": mean(x["max_delta"] - x["min_delta"]
                                         for x in complete) if complete else None,
        "p_sources_with_exchange_sensitive_delta": sum(
            x["max_delta"] != x["min_delta"] for x in complete) / len(complete)
            if complete else None,
        "records": records,
    }
    summary["sensitivity_provenance_file"] = provenance_path.name
    summary["sensitivity_replay_solver_calls"] = calls
    summary["sensitivity_replay_status_counts"] = dict(statuses)
    summary["sensitivity_replay_wall_seconds"] = perf_counter() - started
    summary["total_solver_calls_including_replay"] = summary["solver_calls"] + calls
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    return summary


def run(*, seed: int = 2901, primary_target: int = 1000,
        reciprocal_target: int = 500, sensitivity_sources: int = 20,
        output_dir: Path = Path("output/pt1b_shortness_validation")) -> dict[str, object]:
    if min(primary_target, reciprocal_target) < 1 or sensitivity_sources < 0:
        raise ValueError("positive targets and nonnegative sensitivity subset required")
    output_dir.mkdir(parents=True, exist_ok=True)
    solver = EndplayTrickSolver()
    started = perf_counter()
    statuses: Counter[str] = Counter()
    times: list[float] = []
    cache: dict[str, TrickSolverResult] = {}
    cohorts: dict[str, dict[str, object]] = {}
    observations: list[dict[str, object]] = []
    sensitivity: list[dict[str, object]] = []
    reciprocal_rows: list[dict[str, object]] = []
    case_path = output_dir / "pt1b_cases.jsonl.gz"
    with gzip.open(case_path, "wt", encoding="utf-8") as stream:
        def solve(deal: Deal) -> TrickSolverResult:
            key = deal.serialize()
            if key not in cache:
                result = solver.solve(deal, Seat.NORTH, Suit.SPADES)
                cache[key] = result
                statuses[result.status.value] += 1
                times.append(result.elapsed_seconds)
            return cache[key]

        def write(row: dict[str, object]) -> None:
            stream.write(json.dumps(_jsonable(row), separators=(",", ":")) + "\n")

        cohort_index = 0
        for structure in STRUCTURES:
            kinds = ((ShortnessKind.EQUAL_HAND_SINGLETON,) if structure == (5, 5)
                     else (ShortnessKind.SHORT_HAND_SINGLETON,
                           ShortnessKind.LONG_HAND_SINGLETON))
            for kind in kinds:
                label = f"{structure[0]}-{structure[1]}_{kind.value}"
                start_seed = seed + cohort_index * 1_000_000
                cohort_index += 1
                counts: Counter[str] = Counter()
                cohort_obs: list[dict[str, object]] = []
                while counts["accepted"] < primary_target:
                    if counts["generated"] >= primary_target * 10:
                        raise RuntimeError(f"{label}: generation limit reached: {dict(counts)}")
                    source_seed = start_seed + counts["generated"]
                    case = generate_conditioned_case(source_seed, structure, kind)
                    counts["generated"] += 1
                    control = select_singleton_control(case, length=2,
                                                       selection_seed=source_seed ^ 0xB12)
                    if control is None:
                        counts["no_valid_doubleton_exchange"] += 1
                        continue
                    source = Deal.parse(case.deal_id, seed=case.deal_seed)
                    source_result, control_result = solve(source), solve(control.deal)
                    if (source_result.status is not TrickSolverStatus.SUCCESS
                            or control_result.status is not TrickSolverStatus.SUCCESS):
                        counts["solver_incomplete"] += 1
                        write({"cohort": label, "case": asdict(case),
                               "control": asdict(control),
                               "solvers": [asdict(source_result), asdict(control_result)],
                               "delta": None})
                        continue
                    counts["accepted"] += 1
                    assert source_result.maximum_declarer_tricks is not None
                    assert control_result.maximum_declarer_tricks is not None
                    delta = (source_result.maximum_declarer_tricks
                             - control_result.maximum_declarer_tricks)
                    item = case.short_suits[0]
                    observation = {
                        "cohort": label, "structure": f"{structure[0]}-{structure[1]}",
                        "location": ("equal" if structure == (5, 5) else
                                     "short" if kind is ShortnessKind.SHORT_HAND_SINGLETON
                                     else "long"),
                        "opposite_length": item.opposite_length,
                        "natural_winners": item.certain_top_rank_winners,
                        "ruffable_losers": item.ruffable_losers,
                        "loser_bucket": loser_bucket(item.ruffable_losers),
                        "defender_split": "-".join(map(str, sorted(case.defender_trump_split))),
                        "trump_quality": trump_quality(case), "delta": delta,
                    }
                    observations.append(observation)
                    cohort_obs.append(observation)
                    triple = select_singleton_control(case, length=3,
                                                      selection_seed=source_seed ^ 0xB13)
                    triple_result = solve(triple.deal) if triple is not None else None
                    if triple is None:
                        counts["no_valid_three_card_exchange"] += 1
                    elif triple_result.status is not TrickSolverStatus.SUCCESS:
                        counts["three_card_solver_incomplete"] += 1
                    else:
                        counts["three_card_complete"] += 1
                    if len(cohort_obs) <= sensitivity_sources:
                        variants = singleton_candidates(source, item.hand, item.suit,
                                                        case.trump_suit)
                        all_deltas = []
                        for variant, _ in variants:
                            result = solve(variant)
                            if result.status is TrickSolverStatus.SUCCESS:
                                assert result.maximum_declarer_tricks is not None
                                all_deltas.append(source_result.maximum_declarer_tricks
                                                  - result.maximum_declarer_tricks)
                        sensitivity.append({"cohort": label, "source_seed": source_seed,
                                            "candidate_exchange_count": len(variants),
                                            "solver_complete_exchanges": len(all_deltas),
                                            "mean_delta": mean(all_deltas) if all_deltas else None,
                                            "min_delta": min(all_deltas) if all_deltas else None,
                                            "max_delta": max(all_deltas) if all_deltas else None,
                                            "within_source_sample_sd": (stdev(all_deltas)
                                                if len(all_deltas) > 1 else 0.0
                                                if all_deltas else None)})
                    write({"cohort": label, "case": asdict(case),
                           "doubleton_control": asdict(control),
                           "three_card_control": asdict(triple) if triple else None,
                           "solvers": {"source": asdict(source_result),
                                       "doubleton": asdict(control_result),
                                       "three_card": asdict(triple_result)
                                       if triple_result else None},
                           "delta_doubleton": delta,
                           "delta_three_card": (source_result.maximum_declarer_tricks
                               - triple_result.maximum_declarer_tricks)
                               if triple_result is not None and
                               triple_result.status is TrickSolverStatus.SUCCESS else None,
                           "features": observation})
                    if triple_result is not None and triple_result.status is TrickSolverStatus.SUCCESS:
                        observation["delta_three_card"] = (source_result.maximum_declarer_tricks
                                                             - triple_result.maximum_declarer_tricks)
                cohorts[label] = {"counts": dict(counts),
                                  "singleton_vs_doubleton": delta_stats(
                                      [int(x["delta"]) for x in cohort_obs]),
                                  "singleton_vs_three_card": delta_stats(
                                      [int(x["delta_three_card"]) for x in cohort_obs
                                       if "delta_three_card" in x])}

        for structure in STRUCTURES:
            label = f"{structure[0]}-{structure[1]}_reciprocal"
            start_seed = seed + cohort_index * 1_000_000
            cohort_index += 1
            counts = Counter()
            target = reciprocal_target
            # A 7-3 long hand has only six side cards. It cannot hold one
            # singleton plus >=3 cards in each other side suit for a clean square.
            direct_only = structure == (7, 3)
            while counts["accepted"] < target:
                if counts["generated"] >= target * 15:
                    raise RuntimeError(f"{label}: generation limit reached: {dict(counts)}")
                source_seed = start_seed + counts["generated"]
                case = generate_conditioned_case(
                    source_seed, structure, ShortnessKind.RECIPROCAL_SINGLETONS)
                counts["generated"] += 1
                if direct_only:
                    control = select_direct_reciprocal_control(
                        case, selection_seed=source_seed ^ 0xB14)
                    if control is None:
                        counts["no_valid_direct_exchange"] += 1
                        continue
                    source = Deal.parse(case.deal_id, seed=case.deal_seed)
                    results = [solve(source), solve(control.deal)]
                    if any(result.status is not TrickSolverStatus.SUCCESS for result in results):
                        counts["solver_incomplete"] += 1
                        write({"cohort": label, "case": asdict(case),
                               "direct_control": asdict(control),
                               "solvers": [asdict(x) for x in results], "delta": None})
                        continue
                    counts["accepted"] += 1
                    r, none = (int(x.maximum_declarer_tricks) for x in results)
                    effects = {"combined_direct": r - none}
                    write({"cohort": label, "case": asdict(case),
                           "direct_control": asdict(control),
                           "solvers": [asdict(x) for x in results], "effects": effects})
                else:
                    controls = select_reciprocal_controls(
                        case, selection_seed=source_seed ^ 0xB15)
                    if controls is None:
                        counts["no_valid_four_corner_exchange"] += 1
                        continue
                    deals = (controls.reciprocal, controls.north_removed,
                             controls.south_removed, controls.neither)
                    results = [solve(deal) for deal in deals]
                    if any(result.status is not TrickSolverStatus.SUCCESS for result in results):
                        counts["solver_incomplete"] += 1
                        write({"cohort": label, "case": asdict(case),
                               "controls": asdict(controls),
                               "solvers": [asdict(x) for x in results], "effects": None})
                        continue
                    counts["accepted"] += 1
                    effects = reciprocal_effects(*(int(x.maximum_declarer_tricks)
                                                    for x in results))
                    write({"cohort": label, "case": asdict(case),
                           "controls": asdict(controls),
                           "solvers": [asdict(x) for x in results], "effects": effects})
                reciprocal_rows.append({"cohort": label, "structure": f"{structure[0]}-{structure[1]}",
                                        **effects})
            cohorts[label] = {"counts": dict(counts), "design": "direct-only" if direct_only else
                              "complete-four-corner", "comparisons": {
                                  key: delta_stats([int(x[key]) for x in reciprocal_rows
                                                    if x["cohort"] == label])
                                  for key in effects}}
            if direct_only:
                cohorts[label]["four_corner_rejection"] = (
                    "structurally impossible without creating another singleton: "
                    "long 7-trump hand has only six side cards")

    def grouped(field: str) -> dict[str, dict[str, object]]:
        values: dict[str, list[int]] = defaultdict(list)
        for row in observations:
            values[str(row[field])].append(int(row["delta"]))
        return {key: delta_stats(vals) for key, vals in sorted(values.items())}

    summary: dict[str, object] = {
        "seed": seed, "primary_target_per_location_structure": primary_target,
        "reciprocal_target_per_structure": reciprocal_target,
        "sensitivity_sources_per_primary_cohort": sensitivity_sources,
        "declarer": "N", "strain": "S", "solver_implementation": "endplay/DDS",
        "solver_versions": sorted({x.version for x in cache.values() if x.version}),
        "solver_calls": len(times), "solver_status_counts": dict(statuses),
        "total_solver_seconds": sum(times),
        "mean_solver_seconds": mean(times) if times else None,
        "validation_wall_seconds": perf_counter() - started,
        "cohorts": cohorts, "by_location": grouped("location"),
        "by_ruffable_loser_bucket": grouped("loser_bucket"),
        "by_defender_trump_split": grouped("defender_split"),
        "by_trump_quality": grouped("trump_quality"),
        "by_opposite_length": grouped("opposite_length"),
        "by_natural_winners": grouped("natural_winners"),
        "reciprocal_all_four_corner": {
            key: delta_stats([int(x[key]) for x in reciprocal_rows if key in x])
            for key in ("combined", "remove_n_conditional", "remove_s_conditional",
                        "n_alone", "s_alone", "interaction")},
        "exchange_sensitivity": {
            "sources": len(sensitivity),
            "all_exchange_solver_complete_sources": sum(
                x["candidate_exchange_count"] == x["solver_complete_exchanges"]
                for x in sensitivity),
            "mean_within_source_sd": mean(
                x["within_source_sample_sd"] for x in sensitivity
                if x["within_source_sample_sd"] is not None) if sensitivity else None,
            "mean_within_source_range": mean(
                x["max_delta"] - x["min_delta"] for x in sensitivity
                if x["min_delta"] is not None) if sensitivity else None,
            "p_sources_with_exchange_sensitive_delta": sum(
                x["max_delta"] != x["min_delta"] for x in sensitivity
                if x["min_delta"] is not None) / len(sensitivity) if sensitivity else None,
            "records": sensitivity},
        "method": {
            "delta_sign": "DD(source singleton) minus DD(matched control)",
            "interaction": "R - N_removed - S_removed + neither",
            "exchange_selection": "stable exhaustive enumeration then seeded uniform index",
            "spot_cards": "ranks 2 through 10 only",
            "trump_quality": "A=2,K=1,Q=1,J=0; weak 0-1, medium 2-3, strong 4",
            "exactly_preserved": ["52-card deck", "defender hands", "partnership HCP",
                                  "trump cards and allocation", "all honors by hand",
                                  "side ace entries", "declarer", "strain", "defender trump split"],
            "necessarily_changed": ["studied side-suit lengths", "compensation side-suit lengths",
                                     "spot-card distribution", "some ruffable-loser proxies"],
            "three_card_control": "two sequential spot exchanges, no new side singleton",
            "reciprocal_square": "commuting swaps through third side suit; all four cells solved",
            "no_coefficient_adopted": True,
        },
        "case_file": case_path.name,
    }
    (output_dir / "pt1b_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    refresh_stratification(output_dir)
    return record_exchange_sensitivity(output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2901)
    parser.add_argument("--primary-target", type=int, default=1000)
    parser.add_argument("--reciprocal-target", type=int, default=500)
    parser.add_argument("--sensitivity-sources", type=int, default=20)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("output/pt1b_shortness_validation"))
    args = parser.parse_args()
    result = run(seed=args.seed, primary_target=args.primary_target,
                 reciprocal_target=args.reciprocal_target,
                 sensitivity_sources=args.sensitivity_sources,
                 output_dir=args.output_dir)
    print(json.dumps({"solver_calls": result["solver_calls"],
                      "solver_status_counts": result["solver_status_counts"],
                      "wall_seconds": result["validation_wall_seconds"],
                      "summary": str(args.output_dir / "pt1b_summary.json")}, indent=2))


if __name__ == "__main__":
    main()
