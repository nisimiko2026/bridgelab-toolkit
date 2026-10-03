"""A9.6.2 knowledge cross-reference for structurally missing production routes.

Diagnostic only. Historical reviewed BridgeLab evidence is mapped to the
A9.6.1 structural families; no bidding recommendation or route is created.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from .evidence_review_contract import ReviewClassification
from .missing_route_structural_classification import (
    MissingRouteStructuralFamily as F,
    classify_missing_route_structure,
)


class KnowledgeStatus(str, Enum):
    DEFERRED_SOURCE_PARTIAL = "deferred-source-partial"
    DEFERRED_PARTNERSHIP_POLICY = "deferred-partnership-policy"
    CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE = "current-source-grounded-partial-coverage"


@dataclass(frozen=True, slots=True)
class KnowledgeCrossReference:
    family: F
    population: int
    review_classification: ReviewClassification
    knowledge_status: KnowledgeStatus
    production_ready: bool
    basis: str


@dataclass(frozen=True, slots=True)
class KnowledgeCrossReferenceReport:
    runs: int
    missing_route_population: int
    entries: tuple[KnowledgeCrossReference, ...]


def _mapping(family: F):
    if family is F.RESPONSE_TO_TWO_LEVEL_OPENING:
        return (
            ReviewClassification.PARTNERSHIP_AGREEMENT,
            KnowledgeStatus.DEFERRED_PARTNERSHIP_POLICY,
            False,
            "Historical weak-two response audit: inquiry method, forcing status, and replies remain partnership agreements.",
        )
    if family is F.RESPONSE_TO_THREE_LEVEL_OPENING:
        return (
            ReviewClassification.JUDGMENT,
            KnowledgeStatus.DEFERRED_SOURCE_PARTIAL,
            False,
            "Historical three-level-preempt response audit found no executable numeric contract; fit, stoppers, vulnerability, judgment, and precedence remain unresolved.",
        )
    if family is F.OPENER_REBID_AFTER_ONE_LEVEL_RESPONSE:
        return (
            ReviewClassification.KNOWN_CONVENTION_MISSING_TREATMENT,
            KnowledgeStatus.CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE,
            False,
            "Current inventory contains source-grounded opener-rebid rules/routes, but the observed missing prefixes are outside implemented partial coverage; no blind expansion is justified.",
        )
    if family is F.RESPONDER_REBID_AFTER_OPENER_REBID:
        return (
            ReviewClassification.KNOWN_CONVENTION_MISSING_TREATMENT,
            KnowledgeStatus.DEFERRED_SOURCE_PARTIAL,
            False,
            "Historical responder-rebid audit remains source-partial because exact-prefix call precedence and exceptions are incomplete.",
        )
    if family is F.LATER_CONTINUATION:
        return (
            ReviewClassification.KNOWN_CONVENTION_MISSING_TREATMENT,
            KnowledgeStatus.DEFERRED_SOURCE_PARTIAL,
            False,
            "Observed later continuations belong to previously reviewed strong-2C/2NT continuation families with incomplete residual precedence or qualitative contracts.",
        )
    return (
        ReviewClassification.INSUFFICIENT_EVIDENCE,
        KnowledgeStatus.DEFERRED_SOURCE_PARTIAL,
        False,
        "No reviewed knowledge mapping is available for this structural family.",
    )


def cross_reference_missing_route_knowledge(*, start_seed: int = 1, count: int = 1000):
    source = classify_missing_route_structure(start_seed=start_seed, count=count)
    counts = {g.family: g.count for g in source.groups}
    entries = []
    for family in F:
        n = counts.get(family, 0)
        if not n:
            continue
        classification, status, ready, basis = _mapping(family)
        entries.append(KnowledgeCrossReference(
            family=family,
            population=n,
            review_classification=classification,
            knowledge_status=status,
            production_ready=ready,
            basis=basis,
        ))
    assert sum(x.population for x in entries) == source.missing_route_population
    return KnowledgeCrossReferenceReport(
        runs=source.runs,
        missing_route_population=source.missing_route_population,
        entries=tuple(entries),
    )
