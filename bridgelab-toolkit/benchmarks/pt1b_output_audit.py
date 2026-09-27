"""Verify every saved PT-1B control, DDS record, and sensitivity exchange."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import gzip
import json
from pathlib import Path

from bridge.deals import Deal
from bridge.models import Card, Hand, Rank, Seat, Suit
from bridge.playing_trick_shortness_pairs import CardExchange, _preserved, apply_exchange


def _exchange(value: dict) -> CardExchange:
    card = lambda item: Card(Suit(item["suit"]), Rank(item["rank"]))
    return CardExchange(
        card(value["added_card"]), Seat.parse(value["added_from"]),
        Seat.parse(value["added_to"]), card(value["removed_card"]),
        Seat.parse(value["removed_from"]), Seat.parse(value["removed_to"]),
        tuple(value["source_shape_before"]), tuple(value["opposite_shape_before"]),
        tuple(value["source_shape_after"]), tuple(value["opposite_shape_after"]),
    )


def _saved_deal(value: dict) -> Deal:
    return Deal(value["seed"], tuple(
        (Seat.parse(seat), Hand.from_cards(Card.parse(text) for text in hand["cards"]))
        for seat, hand in value["hands"]))


def _path(source: Deal, record: dict, expected_id: str) -> int:
    if record["candidate_exchange_count"] <= record["selected_exchange_index"]:
        raise AssertionError("invalid selected exchange index")
    current = source
    exchanges = tuple(_exchange(item) for item in record["exchanges"])
    for exchange in exchanges:
        current = apply_exchange(current, exchange)
    if current.serialize() != expected_id or _saved_deal(record["deal"]).serialize() != expected_id:
        raise AssertionError("recorded path disagrees with solver deal")
    if not _preserved(source, current, Suit.SPADES):
        raise AssertionError("matched control changed a protected feature")
    for exchange in reversed(exchanges):
        current = apply_exchange(current, exchange.inverse())
    if current.serialize() != source.serialize():
        raise AssertionError("reverse path did not restore source")
    return len(exchanges)


def audit(output_dir: Path) -> dict[str, object]:
    summary = json.loads((output_dir / "pt1b_summary.json").read_text(encoding="utf-8"))
    counts: Counter[str] = Counter()
    seen: set[tuple[str, int, str]] = set()
    with gzip.open(output_dir / summary["case_file"], "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            cohort, case = row["cohort"], row["case"]
            source = Deal.parse(case["deal_id"], seed=case["deal_seed"])
            key = (cohort, case["deal_seed"], source.serialize())
            if key in seen:
                raise AssertionError("duplicate source ID")
            seen.add(key)
            counts["main_source_rows"] += 1
            counts[f"cohort:{cohort}"] += 1
            if "doubleton_control" in row:
                solvers = row["solvers"]
                if solvers["source"]["deal_id"] != source.serialize():
                    raise AssertionError("source solver deal ID mismatch")
                counts["verified_card_moves"] += _path(
                    source, row["doubleton_control"], solvers["doubleton"]["deal_id"])
                counts["ordinary_doubleton_controls"] += 1
                if row["three_card_control"] is not None:
                    if solvers["three_card"] is None:
                        raise AssertionError("three-card control missing solver record")
                    counts["verified_card_moves"] += _path(
                        source, row["three_card_control"], solvers["three_card"]["deal_id"])
                    counts["ordinary_three_card_controls"] += 1
                for result in solvers.values():
                    if result is not None:
                        if result["status"] != "success" or result["maximum_declarer_tricks"] is None:
                            raise AssertionError("unavailable main solver result")
                        counts["main_solver_records"] += 1
                if row["delta_doubleton"] != (solvers["source"]["maximum_declarer_tricks"]
                                               - solvers["doubleton"]["maximum_declarer_tricks"]):
                    raise AssertionError("ordinary delta mismatch")
            elif "direct_control" in row:
                solvers = row["solvers"]
                if solvers[0]["deal_id"] != source.serialize():
                    raise AssertionError("source solver deal ID mismatch")
                counts["verified_card_moves"] += _path(
                    source, row["direct_control"], solvers[1]["deal_id"])
                counts["reciprocal_direct_controls"] += 1
                if row["effects"]["combined_direct"] != (
                        solvers[0]["maximum_declarer_tricks"]
                        - solvers[1]["maximum_declarer_tricks"]):
                    raise AssertionError("direct reciprocal delta mismatch")
                counts["main_solver_records"] += len(solvers)
            else:
                controls, solvers = row["controls"], row["solvers"]
                names = ("reciprocal", "north_removed", "south_removed", "neither")
                deals = tuple(_saved_deal(controls[name]) for name in names)
                if any(deal.serialize() != result["deal_id"]
                       for deal, result in zip(deals, solvers)):
                    raise AssertionError("reciprocal solver deal IDs mismatch")
                if deals[0].serialize() != source.serialize():
                    raise AssertionError("reciprocal source mismatch")
                north = _exchange(controls["north_exchange"])
                south = _exchange(controls["south_exchange"])
                south_after_north = _exchange(controls["south_exchange_after_north"])
                north_after_south = _exchange(controls["north_exchange_after_south"])
                edges = ((source, north, deals[1]), (source, south, deals[2]),
                         (deals[1], south_after_north, deals[3]),
                         (deals[2], north_after_south, deals[3]))
                for before, exchange, after in edges:
                    if apply_exchange(before, exchange).serialize() != after.serialize():
                        raise AssertionError("reciprocal forward edge failed")
                    if apply_exchange(after, exchange.inverse()).serialize() != before.serialize():
                        raise AssertionError("reciprocal reverse edge failed")
                    counts["verified_card_moves"] += 1
                if not all(_preserved(source, deal, Suit.SPADES) for deal in deals[1:]):
                    raise AssertionError("reciprocal protected feature changed")
                r, n, s, none = (item["maximum_declarer_tricks"] for item in solvers)
                if row["effects"]["interaction"] != r - n - s + none:
                    raise AssertionError("reciprocal interaction mismatch")
                counts["reciprocal_four_corner_controls"] += 1
                counts["main_solver_records"] += len(solvers)
    if counts["main_source_rows"] != 14_000:
        raise AssertionError("main source record count incomplete")

    sensitivity: Counter[str] = Counter()
    per_source: Counter[tuple[str, int]] = Counter()
    indices: dict[tuple[str, int], set[int]] = {}
    with gzip.open(output_dir / summary["sensitivity_provenance_file"],
                   "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            key = (row["cohort"], row["source_seed"])
            if row["candidate_index"] in indices.setdefault(key, set()):
                raise AssertionError("duplicate sensitivity candidate index")
            indices[key].add(row["candidate_index"])
            per_source[key] += 1
            source = Deal.parse(row["source_solver"]["deal_id"], seed=row["source_seed"])
            control = Deal.parse(row["control_deal_id"], seed=row["source_seed"])
            exchange = _exchange(row["exchange"])
            if (apply_exchange(source, exchange).serialize() != control.serialize()
                    or apply_exchange(control, exchange.inverse()).serialize() != source.serialize()
                    or not _preserved(source, control, Suit.SPADES)):
                raise AssertionError("sensitivity transformation invalid")
            if (row["control_solver"]["deal_id"] != control.serialize()
                    or row["source_solver"]["status"] != "success"
                    or row["control_solver"]["status"] != "success"):
                raise AssertionError("sensitivity solver provenance invalid")
            if row["delta"] != (row["source_solver"]["maximum_declarer_tricks"]
                                - row["control_solver"]["maximum_declarer_tricks"]):
                raise AssertionError("sensitivity delta mismatch")
            if row["candidate_exchange_count"] != summary["exchange_sensitivity"]["records"][
                    next(i for i, item in enumerate(summary["exchange_sensitivity"]["records"])
                         if (item["cohort"], item["source_seed"]) == key)]["candidate_exchange_count"]:
                raise AssertionError("sensitivity candidate count mismatch")
            sensitivity["sensitivity_records"] += 1
            sensitivity["verified_card_moves"] += 1
    for key, count in per_source.items():
        if indices[key] != set(range(count)):
            raise AssertionError("sensitivity source missing a candidate index")
    if len(per_source) != summary["exchange_sensitivity"]["sources"]:
        raise AssertionError("sensitivity source count incomplete")
    if sensitivity["sensitivity_records"] != summary["sensitivity_replay_solver_calls"]:
        raise AssertionError("sensitivity solver count mismatch")
    result = {"main": dict(counts), "sensitivity": dict(sensitivity),
              "sensitivity_sources": len(per_source), "integrity": "passed"}
    (output_dir / "pt1b_integrity_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("output/pt1b_shortness_validation"))
    args = parser.parse_args()
    print(json.dumps(audit(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
