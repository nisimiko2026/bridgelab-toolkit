"""Descriptive statistics for corpus bidding benchmarks.

This module summarizes already-produced CorpusBenchmarkResult objects.

It does not rerun BridgeLab, reclassify disagreements, rank evidence, infer
correctness, or treat corpus agreement as proof that a recommendation is
correct.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus_benchmark import (
    CorpusBenchmarkResult,
    CorpusBenchmarkStatus,
)
from .decision_evidence import DisagreementKind


@dataclass(frozen=True, slots=True)
class CorpusBenchmarkStatistics:
    """Aggregate descriptive statistics for one benchmark run."""

    total: int
    evaluated: int
    skipped_unknown_system: int

    bridgelab_recommended: int
    bridgelab_abstained: int

    agreements: int
    disagreement_counts: tuple[
        tuple[DisagreementKind, int],
        ...
    ]

    def __post_init__(self) -> None:
        integer_fields = (
            "total",
            "evaluated",
            "skipped_unknown_system",
            "bridgelab_recommended",
            "bridgelab_abstained",
            "agreements",
        )

        for name in integer_fields:
            value = getattr(self, name)

            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"{name} must be a non-negative integer"
                )

        if self.evaluated + self.skipped_unknown_system != self.total:
            raise ValueError(
                "evaluated plus skipped positions must equal total"
            )

        if (
            self.bridgelab_recommended
            + self.bridgelab_abstained
            != self.evaluated
        ):
            raise ValueError(
                "BridgeLab recommendation counts must equal evaluated"
            )

        if not isinstance(
            self.disagreement_counts,
            tuple,
        ):
            raise TypeError(
                "disagreement_counts must be a tuple"
            )

        seen: set[DisagreementKind] = set()

        for kind, count in self.disagreement_counts:
            if not isinstance(kind, DisagreementKind):
                raise TypeError(
                    "disagreement count key must be DisagreementKind"
                )

            if kind in seen:
                raise ValueError(
                    f"duplicate disagreement kind: {kind.value}"
                )

            seen.add(kind)

            if (
                not isinstance(count, int)
                or isinstance(count, bool)
                or count < 0
            ):
                raise ValueError(
                    "disagreement count must be a "
                    "non-negative integer"
                )

        if self.agreements != self.count(
            DisagreementKind.AGREEMENT
        ):
            raise ValueError(
                "agreements must equal AGREEMENT count"
            )

        if sum(
            count
            for _, count in self.disagreement_counts
        ) != self.evaluated:
            raise ValueError(
                "disagreement counts must equal evaluated"
            )

    def count(
        self,
        kind: DisagreementKind,
    ) -> int:
        if not isinstance(kind, DisagreementKind):
            raise TypeError(
                "kind must be DisagreementKind"
            )

        for existing_kind, count in self.disagreement_counts:
            if existing_kind is kind:
                return count

        return 0

    @property
    def system_known_rate(self) -> float:
        """Fraction of all positions that were benchmarkable."""

        if self.total == 0:
            return 0.0

        return self.evaluated / self.total

    @property
    def bridgelab_coverage_rate(self) -> float:
        """Fraction of evaluated positions with a BridgeLab recommendation."""

        if self.evaluated == 0:
            return 0.0

        return self.bridgelab_recommended / self.evaluated

    @property
    def bridgelab_abstention_rate(self) -> float:
        if self.evaluated == 0:
            return 0.0

        return self.bridgelab_abstained / self.evaluated

    @property
    def agreement_rate(self) -> float:
        """Observed agreement rate; this is not a correctness measure."""

        if self.evaluated == 0:
            return 0.0

        return self.agreements / self.evaluated


def summarize_corpus_benchmark(
    results: tuple[CorpusBenchmarkResult, ...],
) -> CorpusBenchmarkStatistics:
    """Summarize existing benchmark results without reevaluation."""

    if not isinstance(results, tuple):
        raise TypeError(
            "results must be a tuple"
        )

    if not all(
        isinstance(result, CorpusBenchmarkResult)
        for result in results
    ):
        raise TypeError(
            "results must contain CorpusBenchmarkResult values"
        )

    total = len(results)

    evaluated = 0
    skipped_unknown_system = 0
    bridgelab_recommended = 0
    bridgelab_abstained = 0

    counts = {
        kind: 0
        for kind in DisagreementKind
    }

    for result in results:
        if (
            result.status
            is CorpusBenchmarkStatus.SKIPPED_UNKNOWN_SYSTEM
        ):
            skipped_unknown_system += 1
            continue

        if result.status is not CorpusBenchmarkStatus.EVALUATED:
            raise ValueError(
                f"unsupported benchmark status: {result.status}"
            )

        if result.case is None:
            raise ValueError(
                "evaluated benchmark result has no DecisionCase"
            )

        evaluated += 1

        bridgelab = result.case.bridgelab

        if bridgelab is None:
            raise ValueError(
                "evaluated benchmark case has no BridgeLab evidence"
            )

        if bridgelab.recommendation is None:
            bridgelab_abstained += 1
        else:
            bridgelab_recommended += 1

        if len(result.case.disagreements) != 1:
            raise ValueError(
                "corpus benchmark case must contain exactly "
                "one disagreement classification"
            )

        kind = result.case.disagreements[0].kind
        counts[kind] += 1

    disagreement_counts = tuple(
        (kind, counts[kind])
        for kind in DisagreementKind
    )

    return CorpusBenchmarkStatistics(
        total=total,
        evaluated=evaluated,
        skipped_unknown_system=skipped_unknown_system,
        bridgelab_recommended=bridgelab_recommended,
        bridgelab_abstained=bridgelab_abstained,
        agreements=counts[
            DisagreementKind.AGREEMENT
        ],
        disagreement_counts=disagreement_counts,
    )
