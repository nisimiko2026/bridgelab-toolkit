"""A8.12 descriptive concentration analysis over production abstentions.

This module measures where production abstentions occur. Frequency is evidence
about concentration only; it is not a correctness, priority, or policy score.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .abstention_diagnostics import AbstentionReason
from .production_gap_extraction import (
    ProductionAbstentionCase,
    ProductionGapExtractionReport,
    extract_production_abstentions,
)


@dataclass(frozen=True, slots=True)
class ConcentrationGroup:
    dimension: str
    key: str
    count: int
    share_of_abstentions: float
    seeds: tuple[int, ...]

    def __post_init__(self):
        if not self.dimension or not self.key:
            raise ValueError("dimension and key must be non-blank")
        if self.count <= 0 or self.count != len(self.seeds):
            raise ValueError("count must be positive and equal seed count")
        if not 0.0 <= self.share_of_abstentions <= 1.0:
            raise ValueError("share_of_abstentions must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ProductionGapConcentrationReport:
    source: ProductionGapExtractionReport
    by_reason: tuple[ConcentrationGroup, ...]
    by_depth: tuple[ConcentrationGroup, ...]
    by_route: tuple[ConcentrationGroup, ...]
    by_auction: tuple[ConcentrationGroup, ...]

    @property
    def abstained(self) -> int:
        return self.source.abstained


def _group(
    cases: tuple[ProductionAbstentionCase, ...],
    dimension: str,
    key_fn,
) -> tuple[ConcentrationGroup, ...]:
    buckets: dict[str, list[int]] = {}
    for case in cases:
        key = str(key_fn(case))
        buckets.setdefault(key, []).append(case.seed)

    total = len(cases)
    # Stable lexical ordering. Deliberately not sorted by frequency.
    return tuple(
        ConcentrationGroup(
            dimension=dimension,
            key=key,
            count=len(seeds),
            share_of_abstentions=0.0 if total == 0 else len(seeds) / total,
            seeds=tuple(seeds),
        )
        for key, seeds in sorted(buckets.items())
    )


def analyze_production_gap_concentration(
    *, start_seed: int = 1, count: int = 1000
) -> ProductionGapConcentrationReport:
    source = extract_production_abstentions(start_seed=start_seed, count=count)
    cases = source.cases

    return ProductionGapConcentrationReport(
        source=source,
        by_reason=_group(cases, "reason", lambda x: x.diagnostic.reason.value),
        by_depth=_group(cases, "depth", lambda x: str(x.depth)),
        by_route=_group(
            cases,
            "route",
            lambda x: x.diagnostic.route_id
            if x.diagnostic.route_id is not None
            else "<NO_ROUTE>",
        ),
        by_auction=_group(
            cases,
            "auction",
            lambda x: x.auction if x.auction else "<OPENING>",
        ),
    )
