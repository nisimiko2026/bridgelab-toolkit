"""A9.3 opening-review population classification.

Classifies the A8 opening-pass-review population mechanically by strength and
shape. This is diagnostic evidence only: it does not recommend Pass, infer a
missing SAYC treatment, or change production bidding.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from .opening_pass_review import OpeningPassReviewCase, review_opening_pass_cases


class OpeningReviewClass(str, Enum):
    BELOW_NORMAL_OPENING_STRENGTH = "below-normal-opening-strength"
    NORMAL_OPENING_STRENGTH_UNRESOLVED = "normal-opening-strength-unresolved"
    ABOVE_NORMAL_OPENING_STRENGTH_UNRESOLVED = "above-normal-opening-strength-unresolved"


@dataclass(frozen=True, slots=True)
class ClassifiedOpeningReview:
    case: OpeningPassReviewCase
    review_class: OpeningReviewClass
    basis: str


@dataclass(frozen=True, slots=True)
class OpeningReviewClassGroup:
    review_class: OpeningReviewClass
    count: int
    share_of_population: float
    seeds: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class OpeningPassClassificationReport:
    start_seed: int
    runs: int
    population: int
    cases: tuple[ClassifiedOpeningReview, ...]
    groups: tuple[OpeningReviewClassGroup, ...]
    hcp_counts: tuple[tuple[int, int], ...]
    shape_counts: tuple[tuple[tuple[int, int, int, int], int], ...]

    def count(self, review_class: OpeningReviewClass) -> int:
        return next((g.count for g in self.groups if g.review_class is review_class), 0)


def _classify(case: OpeningPassReviewCase) -> tuple[OpeningReviewClass, str]:
    if case.hcp < 12:
        return (
            OpeningReviewClass.BELOW_NORMAL_OPENING_STRENGTH,
            "HCP is below the current controlled SAYC 12-HCP one-level opening floor.",
        )
    if case.hcp <= 21:
        return (
            OpeningReviewClass.NORMAL_OPENING_STRENGTH_UNRESOLVED,
            "HCP is within the current controlled SAYC 12–21 one-level opening band, "
            "but no production opening rule applied.",
        )
    return (
        OpeningReviewClass.ABOVE_NORMAL_OPENING_STRENGTH_UNRESOLVED,
        "HCP is above the current controlled SAYC 12–21 one-level opening band, "
        "but no production opening rule applied.",
    )


def classify_opening_pass_population(
    *, start_seed: int = 1, count: int = 1000
) -> OpeningPassClassificationReport:
    source = review_opening_pass_cases(
        start_seed=start_seed, count=count, seeds=None
    )

    classified = []
    buckets = {x: [] for x in OpeningReviewClass}
    hcp = Counter()
    shapes = Counter()

    for case in source.cases:
        review_class, basis = _classify(case)
        item = ClassifiedOpeningReview(case, review_class, basis)
        classified.append(item)
        buckets[review_class].append(case.seed)
        hcp[case.hcp] += 1
        shapes[case.shape] += 1

    groups = tuple(
        OpeningReviewClassGroup(
            review_class=review_class,
            count=len(buckets[review_class]),
            share_of_population=(
                0.0 if source.population == 0
                else len(buckets[review_class]) / source.population
            ),
            seeds=tuple(buckets[review_class]),
        )
        for review_class in OpeningReviewClass
        if buckets[review_class]
    )

    return OpeningPassClassificationReport(
        start_seed=start_seed,
        runs=source.runs,
        population=source.population,
        cases=tuple(classified),
        groups=groups,
        hcp_counts=tuple(sorted(hcp.items())),
        shape_counts=tuple(sorted(shapes.items())),
    )
