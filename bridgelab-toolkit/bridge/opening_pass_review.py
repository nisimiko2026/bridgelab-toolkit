"""A9.2 opening-Pass review.

Inspects A8.13 opening-pass-review cases without changing production bidding.
The review preserves the exact hand, HCP/shape, and rejected opening-rule trace.
It deliberately does not decide whether the correct action is Pass.
"""
from __future__ import annotations

from dataclasses import dataclass

from .auction import Auction
from .bidding_rules import BiddingContext, SystemContext
from .models import Seat, Suit
from .production_gap_evidence import EvidenceClass, classify_production_gap_evidence
from .sayc import create_sayc_opening_engine


@dataclass(frozen=True, slots=True)
class OpeningPassReviewCase:
    seed: int
    replay_key: str
    deal: str
    hand: str
    hcp: int
    shape: tuple[int, int, int, int]
    rejected_rules: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class OpeningPassReviewReport:
    start_seed: int
    runs: int
    population: int
    cases: tuple[OpeningPassReviewCase, ...]


def _hand_text(hand) -> str:
    if hasattr(hand, "serialize"):
        return hand.serialize()
    return str(hand)


def review_opening_pass_cases(
    *, start_seed: int = 1, count: int = 1000, seeds: tuple[int, ...] | None = None
) -> OpeningPassReviewReport:
    evidence = classify_production_gap_evidence(start_seed=start_seed, count=count)
    population_cases = [
        x for x in evidence.cases
        if x.evidence_class is EvidenceClass.OPENING_PASS_REVIEW
    ]
    wanted = None if seeds is None else set(seeds)
    selected = [
        x for x in population_cases
        if wanted is None or x.case.seed in wanted
    ]

    from .sayc_coverage_benchmark import run_sayc_coverage_benchmark
    coverage = run_sayc_coverage_benchmark(start_seed=start_seed, count=count)
    by_seed = {c.deal.seed: c for c in coverage.batch.cases}

    out = []
    for x in selected:
        source = x.case
        # The production benchmark is North-dealt and depth-zero means North.
        batch_case = by_seed[source.seed]
        hand = batch_case.deal.mapping[Seat.NORTH]
        context = BiddingContext.create(
            hand=hand,
            auction=Auction(Seat.NORTH),
            vulnerability=coverage.batch.vulnerability,
            system=SystemContext("SAYC"),
        )
        result = create_sayc_opening_engine().evaluate(context)
        if result.has_recommendation:
            raise AssertionError(
                f"opening replay unexpectedly recommends at seed {source.seed}"
            )
        rejected = tuple(
            (d.rule_id, d.explanation)
            for d in result.decisions
            if not d.applicable
        )
        ev = context.evaluation
        out.append(
            OpeningPassReviewCase(
                seed=source.seed,
                replay_key=source.replay_key,
                deal=source.deal,
                hand=_hand_text(hand),
                hcp=ev.hcp,
                shape=(
                    ev.length(Suit.SPADES),
                    ev.length(Suit.HEARTS),
                    ev.length(Suit.DIAMONDS),
                    ev.length(Suit.CLUBS),
                ),
                rejected_rules=rejected,
            )
        )

    return OpeningPassReviewReport(
        start_seed=start_seed,
        runs=count,
        population=len(population_cases),
        cases=tuple(out),
    )

