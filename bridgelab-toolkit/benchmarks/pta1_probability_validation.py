"""PT-A1 exact-combinatorial comparisons and measured proposal diagnostics.

This benchmark does not enumerate full hidden deals or invoke a solver.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import json
from math import comb, sqrt
from pathlib import Path
from time import perf_counter

from bridge.auction_information import (
    AuctionConstraintUpdate, AuctionInformationState, Certainty, ConstraintProvenance,
    EvidenceOrigin, NumericRange, RangeEvidence,
)
from bridge.deals import full_deck
from bridge.hidden_hand_probability import (
    Feature, SamplingConfig, sample_hidden_hands, vacant_place_reference,
)
from bridge.models import Hand, Rank, Seat, Suit

OWN = Hand.parse("AKQ42.9876.3.J76")
SOURCE = ConstraintProvenance(EvidenceOrigin.PROFILE_INTERPRETATION, "benchmark general constraint")


def update(seat, *, suit=None, low=0, high=13):
    evidence = RangeEvidence(NumericRange(low, high), Certainty.GUARANTEED, SOURCE)
    return (AuctionConstraintUpdate(seat, hcp=evidence) if suit is None else
            AuctionConstraintUpdate(seat, suit_lengths=((suit, evidence),)))


def exact_partner_joint(own: Hand) -> dict[tuple[int, int], Fraction]:
    """Count 13-card subsets by spade count and HCP with integer dynamic programming."""
    dp = [Counter() for _ in range(14)]
    dp[0][(0, 0)] = 1
    unseen = [card for card in full_deck() if card not in own.cards]
    points = {Rank.ACE: 4, Rank.KING: 3, Rank.QUEEN: 2, Rank.JACK: 1}
    for i, card in enumerate(unseen):
        for n in range(min(i + 1, 13), 0, -1):
            for (spades, hcp), count in dp[n - 1].items():
                dp[n][(spades + int(card.suit is Suit.SPADES), hcp + points.get(card.rank, 0))] += count
    denominator = comb(39, 13)
    assert sum(dp[13].values()) == denominator
    return {key: Fraction(count, denominator) for key, count in dp[13].items()}


def comparison(expected: Fraction, observed: float, n: int) -> dict:
    p = float(expected)
    se = sqrt(p * (1 - p) / n) if n else None
    return {"expected_probability": p, "expected_fraction": str(expected),
            "observed_probability": observed if n else None,
            "absolute_error": abs(observed - p) if n else None,
            "sampling_standard_error": se, "sample_size": n,
            "standardized_error": (observed - p) / se if se else None}


def measured(state, config):
    start = perf_counter()
    result = sample_hidden_hands(state, config)
    seconds = perf_counter() - start
    diagnostics = {
        "requested": result.requested, "proposals": result.proposals, "accepted": result.accepted,
        "rejections": dict(result.rejections), "rejection_rate": result.rejection_rate,
        "seconds": seconds, "proposals_per_second": result.proposals / seconds,
        "accepted_per_second": result.accepted / seconds,
        "sampling_status": result.sampling_status.value, "weighting_status": result.weighting_status.value,
        "effective_sample_size": float(result.effective_sample_size), "seed": config.seed,
    }
    return result, diagnostics


def run(samples=4000, max_proposals=200000, seed=731):
    base = AuctionInformationState.start(Seat.SOUTH, OWN, Seat.SOUTH)
    exact = exact_partner_joint(OWN)
    scenarios = (
        ("unconstrained", (), lambda s, h: True),
        ("unconstrained_second_seed", (), lambda s, h: True),
        ("partner_spades_ge3", (update(Seat.NORTH, suit=Suit.SPADES, low=3),), lambda s, h: s >= 3),
        ("partner_spades_ge4", (update(Seat.NORTH, suit=Suit.SPADES, low=4),), lambda s, h: s >= 4),
        ("partner_spades_eq4", (update(Seat.NORTH, suit=Suit.SPADES, low=4, high=4),), lambda s, h: s == 4),
        ("partner_hcp_10_12", (update(Seat.NORTH, low=10, high=12),), lambda s, h: 10 <= h <= 12),
        ("partner_hcp_eq11", (update(Seat.NORTH, low=11, high=11),), lambda s, h: h == 11),
        ("combined", (update(Seat.NORTH, suit=Suit.SPADES, low=4),
                      update(Seat.NORTH, low=10, high=12)), lambda s, h: s >= 4 and 10 <= h <= 12),
    )
    rows = []
    for index, (name, updates, predicate) in enumerate(scenarios):
        conditioned = {key: p for key, p in exact.items() if predicate(*key)}
        mass = sum(conditioned.values(), Fraction())
        result, diagnostics = measured(base.with_updates(updates),
                                       SamplingConfig(samples, max_proposals, seed + index))
        comparisons = []
        for feature, coordinate in ((Feature.SPADES, 0), (Feature.HCP, 1)):
            expected = Counter()
            for key, p in conditioned.items():
                expected[key[coordinate]] += p / mass
            observed = (dict(result.marginal(Seat.NORTH, feature).outcomes) if result.accepted else {})
            for value in sorted(set(expected) | set(observed)):
                actual = float(observed[value].as_fraction()) if value in observed else 0.0
                comparisons.append({"feature": feature.value, "outcome": value,
                                    **comparison(expected[value], actual, result.accepted)})
        rows.append({"scenario": name, "expected_acceptance_probability": float(mass),
                     **diagnostics, "comparisons": comparisons})

    # Exact reference conditional on a fixed opponent total and oriented side lengths.
    for name, updates, side in (
        ("defender_baseline", (update(Seat.NORTH, suit=Suit.SPADES, low=4, high=4),), None),
        ("defender_diamonds_5_3",
         (update(Seat.NORTH, suit=Suit.SPADES, low=4, high=4),
          update(Seat.WEST, suit=Suit.DIAMONDS, low=5, high=5),
          update(Seat.EAST, suit=Suit.DIAMONDS, low=3, high=3)), Suit.DIAMONDS),
    ):
        s = base.with_updates(updates)
        result, diagnostics = measured(s, SamplingConfig(samples, max_proposals, seed + len(rows)))
        reference = vacant_place_reference(s, Suit.SPADES, 4, defender_side_suit=side)
        counts = Counter(sample.hand(Seat.WEST).length(Suit.SPADES) for sample in result.samples)
        comparisons = [{"feature": "LHO spades", "outcome": item.first_trumps,
                        **comparison(item.probability.as_fraction(),
                                     counts[item.first_trumps] / result.accepted if result.accepted else 0,
                                     result.accepted)}
                       for item in reference]
        rows.append({"scenario": name, **diagnostics, "comparisons": comparisons})

    # Deliberately rare but feasible event: partner holds the eight remaining spades.
    rare = base.with_updates((update(Seat.NORTH, suit=Suit.SPADES, low=8, high=8),))
    _, diagnostics = measured(rare, SamplingConfig(samples, 20000, seed + len(rows)))
    rows.append({"scenario": "rare_partner_all_remaining_spades", **diagnostics, "comparisons": []})
    return {"algorithm": "uniform-unseen-shuffle-rejection-v1", "scenarios": rows,
            "interpretation": "Monte Carlo diagnostics, not a blanket calibration claim. "
                              "SE uses exact conditional Bernoulli probability and accepted N. "
                              "Multiple marginal bins are dependent; inspect errors jointly. "
                              "Budget exhaustion is reported, never treated as infeasibility."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=4000)
    parser.add_argument("--max-proposals", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=731)
    parser.add_argument("--output", type=Path, default=Path("output/pta1_probability/summary.json"))
    args = parser.parse_args()
    payload = run(args.samples, args.max_proposals, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for row in payload["scenarios"]:
        errors = [abs(c["standardized_error"]) for c in row["comparisons"] if c["standardized_error"] is not None]
        print(row["scenario"], row["accepted"], "/", row["proposals"],
              row["sampling_status"], "max_abs_z=", round(max(errors, default=0), 3))


if __name__ == "__main__":
    main()
