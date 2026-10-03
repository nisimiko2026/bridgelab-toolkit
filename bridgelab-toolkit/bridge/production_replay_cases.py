"""A8.14 deterministic representative and replay cases.

Representative cases are selected mechanically from A8.13 evidence classes.
They are examples for reproducible investigation, not rankings, priorities,
correctness claims, or bidding-policy decisions.
"""
from __future__ import annotations

from dataclasses import dataclass

from .production_gap_evidence import (
    EvidenceClass,
    ClassifiedAbstention,
    classify_production_gap_evidence,
)


@dataclass(frozen=True, slots=True)
class RepresentativeReplayCase:
    evidence_class: EvidenceClass
    seed: int
    replay_key: str
    deal: str
    stopped_seat: str
    auction: str
    depth: int
    reason: str
    route_id: str | None
    rejected_rules: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class RepresentativeReplayGroup:
    evidence_class: EvidenceClass
    available_count: int
    cases: tuple[RepresentativeReplayCase, ...]


@dataclass(frozen=True, slots=True)
class RepresentativeReplayReport:
    start_seed: int
    runs: int
    abstained: int
    per_class_limit: int
    groups: tuple[RepresentativeReplayGroup, ...]

    @property
    def selected_count(self) -> int:
        return sum(len(g.cases) for g in self.groups)


def _convert(x: ClassifiedAbstention) -> RepresentativeReplayCase:
    c = x.case
    d = c.diagnostic
    return RepresentativeReplayCase(
        evidence_class=x.evidence_class,
        seed=c.seed,
        replay_key=c.replay_key,
        deal=c.deal,
        stopped_seat=c.stopped_seat.value,
        auction=c.auction,
        depth=c.depth,
        reason=d.reason.value,
        route_id=d.route_id,
        rejected_rules=tuple((r.rule_id, r.reason) for r in d.rejected_rules),
    )


def build_representative_replay_report(
    *, start_seed: int = 1, count: int = 1000, per_class_limit: int = 5
) -> RepresentativeReplayReport:
    if per_class_limit < 0:
        raise ValueError("per_class_limit must be >= 0")

    source = classify_production_gap_evidence(
        start_seed=start_seed, count=count
    )
    buckets: dict[EvidenceClass, list[ClassifiedAbstention]] = {
        e: [] for e in EvidenceClass
    }
    for case in source.cases:
        buckets[case.evidence_class].append(case)

    groups = []
    for evidence_class in EvidenceClass:
        population = sorted(buckets[evidence_class], key=lambda x: x.case.seed)
        selected = population[:per_class_limit]
        if population:
            groups.append(
                RepresentativeReplayGroup(
                    evidence_class=evidence_class,
                    available_count=len(population),
                    cases=tuple(_convert(x) for x in selected),
                )
            )

    return RepresentativeReplayReport(
        start_seed=start_seed,
        runs=source.runs,
        abstained=source.abstained,
        per_class_limit=per_class_limit,
        groups=tuple(groups),
    )
