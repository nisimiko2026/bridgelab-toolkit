"""A9.4 opening decision coverage audit.

Explains the A9.3 opening-review population without changing production policy.
Normal-strength unresolved hands are classified by the exact equal-length
families already documented as conservative SAYC abstentions. Lower-strength
hands remain review evidence; they are not converted to Pass.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from .opening_pass_classification import (
    OpeningReviewClass,
    ClassifiedOpeningReview,
    classify_opening_pass_population,
)


class OpeningCoverageFamily(str, Enum):
    BELOW_NORMAL_STRENGTH_REVIEW = "below-normal-strength-review"
    EQUAL_FIVE_PLUS_MAJORS = "equal-five-plus-majors"
    EQUAL_FIVE_MINORS = "equal-five-minors"
    OTHER_NORMAL_STRENGTH_UNRESOLVED = "other-normal-strength-unresolved"
    ABOVE_NORMAL_STRENGTH_UNRESOLVED = "above-normal-strength-unresolved"


@dataclass(frozen=True, slots=True)
class OpeningCoverageCase:
    source: ClassifiedOpeningReview
    family: OpeningCoverageFamily
    basis: str


@dataclass(frozen=True, slots=True)
class OpeningCoverageGroup:
    family: OpeningCoverageFamily
    count: int
    share_of_population: float
    seeds: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class OpeningDecisionCoverageAudit:
    start_seed: int
    runs: int
    population: int
    cases: tuple[OpeningCoverageCase, ...]
    groups: tuple[OpeningCoverageGroup, ...]
    normal_strength_shape_counts: tuple[tuple[tuple[int, int, int, int], int], ...]

    def count(self, family: OpeningCoverageFamily) -> int:
        return next((g.count for g in self.groups if g.family is family), 0)


def _family(item: ClassifiedOpeningReview) -> tuple[OpeningCoverageFamily, str]:
    c = item.case
    s, h, d, clubs = c.shape

    if item.review_class is OpeningReviewClass.BELOW_NORMAL_OPENING_STRENGTH:
        return (
            OpeningCoverageFamily.BELOW_NORMAL_STRENGTH_REVIEW,
            "Below the current controlled 12-HCP normal-opening floor; this audit "
            "does not infer Pass or a weak/preemptive treatment.",
        )

    if item.review_class is OpeningReviewClass.ABOVE_NORMAL_OPENING_STRENGTH_UNRESOLVED:
        return (
            OpeningCoverageFamily.ABOVE_NORMAL_STRENGTH_UNRESOLVED,
            "Above the controlled normal-opening band and still unresolved.",
        )

    if s == h and s >= 5:
        return (
            OpeningCoverageFamily.EQUAL_FIVE_PLUS_MAJORS,
            "Equal 5+ majors: the controlled SAYC major rules require the bid major "
            "to be strictly longer than the other major.",
        )

    if d == clubs == 5:
        return (
            OpeningCoverageFamily.EQUAL_FIVE_MINORS,
            "Exactly 5-5 minors: current Better-Minor production covers unequal "
            "minors plus 3-3 and 4-4 ties, but not the 5-5 tie.",
        )

    return (
        OpeningCoverageFamily.OTHER_NORMAL_STRENGTH_UNRESOLVED,
        "Normal opening strength, but not one of the documented equal-major or "
        "equal-5-5-minor conservative boundaries.",
    )


def audit_opening_decision_coverage(
    *, start_seed: int = 1, count: int = 1000
) -> OpeningDecisionCoverageAudit:
    source = classify_opening_pass_population(start_seed=start_seed, count=count)
    cases = []
    buckets = {x: [] for x in OpeningCoverageFamily}
    normal_shapes = Counter()

    for item in source.cases:
        family, basis = _family(item)
        cases.append(OpeningCoverageCase(item, family, basis))
        buckets[family].append(item.case.seed)
        if item.case.hcp >= 12:
            normal_shapes[item.case.shape] += 1

    groups = tuple(
        OpeningCoverageGroup(
            family=family,
            count=len(buckets[family]),
            share_of_population=(
                0.0 if source.population == 0
                else len(buckets[family]) / source.population
            ),
            seeds=tuple(buckets[family]),
        )
        for family in OpeningCoverageFamily
        if buckets[family]
    )

    return OpeningDecisionCoverageAudit(
        start_seed=start_seed,
        runs=source.runs,
        population=source.population,
        cases=tuple(cases),
        groups=groups,
        normal_strength_shape_counts=tuple(sorted(normal_shapes.items())),
    )
