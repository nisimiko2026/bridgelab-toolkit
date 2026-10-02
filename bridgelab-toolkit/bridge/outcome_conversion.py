"""Duplicate-score conversion to IMP and matchpoint measurements.

A6.13 — IMP / Matchpoint Outcome Conversion.

Conversions are descriptive measurements only. They do not rank contracts,
select a winner, recommend an action, or modify bidding policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class OutcomeComparisonMethod(str, Enum):
    IMP = "imp"
    MATCHPOINT = "matchpoint"


# WBF-style IMP thresholds: the first upper bound strictly greater than the
# absolute score difference determines the IMP magnitude.
_IMP_UPPER_BOUNDS = (
    20, 50, 90, 130, 170, 220, 270, 320, 370, 430, 500, 600,
    750, 900, 1100, 1300, 1500, 1750, 2000, 2250, 2500, 3000,
    3500, 4000,
)


@dataclass(frozen=True, slots=True)
class IMPOutcomeMeasurement:
    ns_score: int
    reference_ns_score: int
    score_difference: int
    imps: int
    method: OutcomeComparisonMethod = OutcomeComparisonMethod.IMP

    def as_dict(self) -> dict[str, object]:
        return {
            "method": self.method.value,
            "ns_score": self.ns_score,
            "reference_ns_score": self.reference_ns_score,
            "score_difference": self.score_difference,
            "imps": self.imps,
        }


@dataclass(frozen=True, slots=True)
class MatchpointOutcomeMeasurement:
    ns_score: int
    comparison_ns_scores: tuple[int, ...]
    comparisons: int
    wins: int
    ties: int
    matchpoints: float
    top: int
    percentage: float
    method: OutcomeComparisonMethod = OutcomeComparisonMethod.MATCHPOINT

    def as_dict(self) -> dict[str, object]:
        return {
            "method": self.method.value,
            "ns_score": self.ns_score,
            "comparison_ns_scores": list(self.comparison_ns_scores),
            "comparisons": self.comparisons,
            "wins": self.wins,
            "ties": self.ties,
            "matchpoints": self.matchpoints,
            "top": self.top,
            "percentage": self.percentage,
        }


def _require_score(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer duplicate score")
    return value


def score_difference_to_imps(score_difference: int) -> int:
    """Convert an NS score difference to signed IMPs."""
    _require_score(score_difference, "score_difference")
    if score_difference == 0:
        return 0

    magnitude = abs(score_difference)
    imps = 24
    for candidate, upper_bound in enumerate(_IMP_UPPER_BOUNDS):
        if magnitude < upper_bound:
            imps = candidate
            break

    return imps if score_difference > 0 else -imps


def measure_imps(
    *,
    ns_score: int,
    reference_ns_score: int,
) -> IMPOutcomeMeasurement:
    """Measure IMPs from the fixed NS perspective against one reference score."""
    ns_score = _require_score(ns_score, "ns_score")
    reference_ns_score = _require_score(reference_ns_score, "reference_ns_score")
    difference = ns_score - reference_ns_score
    return IMPOutcomeMeasurement(
        ns_score=ns_score,
        reference_ns_score=reference_ns_score,
        score_difference=difference,
        imps=score_difference_to_imps(difference),
    )


def measure_matchpoints(
    *,
    ns_score: int,
    comparison_ns_scores: Iterable[int],
) -> MatchpointOutcomeMeasurement:
    """Measure matchpoints from the fixed NS perspective against field scores.

    Each lower comparison score contributes 2 matchpoints, each tie contributes
    1, and each higher score contributes 0. The top is therefore 2*N.
    """
    ns_score = _require_score(ns_score, "ns_score")
    try:
        scores = tuple(comparison_ns_scores)
    except TypeError as exc:
        raise TypeError("comparison_ns_scores must be an iterable") from exc

    if not scores:
        raise ValueError("matchpoint measurement requires comparison scores")
    for score in scores:
        _require_score(score, "comparison score")

    wins = sum(ns_score > score for score in scores)
    ties = sum(ns_score == score for score in scores)
    matchpoints = float(2 * wins + ties)
    top = 2 * len(scores)
    percentage = 100.0 * matchpoints / top

    return MatchpointOutcomeMeasurement(
        ns_score=ns_score,
        comparison_ns_scores=scores,
        comparisons=len(scores),
        wins=wins,
        ties=ties,
        matchpoints=matchpoints,
        top=top,
        percentage=percentage,
    )
