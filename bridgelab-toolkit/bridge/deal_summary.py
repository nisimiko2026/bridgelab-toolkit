"""Immutable aggregation of existing deal-analysis results and evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .deal_analysis import AnalysisEvidence, AnalysisStage, AnalysisStatus, DealAnalysisResult
from .probability_engine import ProbabilityEngineResult, ProbabilityEngineStatus
from .probability_evidence import ProbabilityEvidence


class DealSummaryStatus(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    NO_DECISION = "no-decision"
    ERROR = "error"


class DealSummaryFailureCode(str, Enum):
    MISSING_SUBSYSTEM_RESULTS = "missing-subsystem-results"
    INVALID_STAGE_RESULT = "invalid-stage-result"
    DUPLICATE_STAGE = "duplicate-stage"


@dataclass(frozen=True, slots=True)
class DealSummaryItem:
    """Ordered reference to one original subsystem analysis result."""

    stage: AnalysisStage
    result: DealAnalysisResult

    def __post_init__(self) -> None:
        if not isinstance(self.stage, AnalysisStage) or not isinstance(self.result, DealAnalysisResult):
            raise TypeError("summary item requires an AnalysisStage and DealAnalysisResult")
        if self.stage is not self.result.stage:
            raise ValueError("summary item stage must match its result")


@dataclass(frozen=True, slots=True)
class DealSummaryInput:
    """Already-computed results; the summary layer performs no bridge analysis."""

    stage_results: tuple[DealAnalysisResult, ...] = ()
    probability_results: tuple[ProbabilityEngineResult, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.stage_results, tuple) or not all(
            isinstance(result, DealAnalysisResult) for result in self.stage_results
        ):
            raise TypeError("stage_results must be a tuple of DealAnalysisResult values")
        if not isinstance(self.probability_results, tuple) or not all(
            isinstance(result, ProbabilityEngineResult) for result in self.probability_results
        ):
            raise TypeError("probability_results must be a tuple of ProbabilityEngineResult values")


@dataclass(frozen=True, slots=True)
class DealSummaryResult:
    status: DealSummaryStatus
    items: tuple[DealSummaryItem, ...]
    recommendation_items: tuple[DealSummaryItem, ...]
    evidence_items: tuple[AnalysisEvidence | ProbabilityEvidence, ...]
    probability_results: tuple[ProbabilityEngineResult, ...]
    unresolved_items: tuple[DealSummaryItem, ...]
    error_items: tuple[DealSummaryItem, ...]
    explanation: str
    failure_code: DealSummaryFailureCode | None = None


_STAGE_ORDER = {
    AnalysisStage.AUCTION: 0,
    AnalysisStage.OPENING_LEAD: 1,
    AnalysisStage.DECLARER_PLAY: 2,
    AnalysisStage.DEFENSIVE_PLAY: 3,
    AnalysisStage.DEAL_SUMMARY: 4,
}


def build_deal_summary(source: DealSummaryInput) -> DealSummaryResult:
    """Aggregate existing results without choosing bids, cards, or probabilities."""

    if not isinstance(source, DealSummaryInput):
        raise TypeError("source must be DealSummaryInput")
    stages = [result.stage for result in source.stage_results]
    if len(stages) != len(set(stages)):
        return _failure(DealSummaryFailureCode.DUPLICATE_STAGE, "Duplicate analysis stages are not supported.")
    if any(result.stage is AnalysisStage.DEAL_SUMMARY for result in source.stage_results):
        return _failure(DealSummaryFailureCode.INVALID_STAGE_RESULT, "A summary cannot aggregate another summary stage.")
    if not source.stage_results and not source.probability_results:
        return _failure(
            DealSummaryFailureCode.MISSING_SUBSYSTEM_RESULTS,
            "No subsystem or probability results were supplied.",
            status=DealSummaryStatus.NO_DECISION,
        )

    items = tuple(
        DealSummaryItem(result.stage, result)
        for result in sorted(source.stage_results, key=lambda result: _STAGE_ORDER[result.stage])
    )
    recommendations = tuple(item for item in items if item.result.status is AnalysisStatus.RECOMMENDATION)
    unresolved = tuple(item for item in items if item.result.status in {AnalysisStatus.ABSTAIN, AnalysisStatus.NO_DECISION})
    errors = tuple(item for item in items if item.result.status is AnalysisStatus.ERROR)
    probability_errors = tuple(
        result for result in source.probability_results
        if result.status in {ProbabilityEngineStatus.ERROR, ProbabilityEngineStatus.INVALID_INPUT}
    )
    probability_available = tuple(
        result for result in source.probability_results if result.status is ProbabilityEngineStatus.SUCCESS
    )
    evidence: list[AnalysisEvidence | ProbabilityEvidence] = []
    for item in items:
        evidence.extend(item.result.evidence)
        evidence.extend(item.result.probability_evidence)
    for result in source.probability_results:
        evidence.extend(result.evidence)

    if errors or probability_errors:
        status = DealSummaryStatus.ERROR
    elif (recommendations or probability_available) and unresolved:
        status = DealSummaryStatus.PARTIAL
    elif recommendations or probability_available:
        status = DealSummaryStatus.AVAILABLE
    else:
        status = DealSummaryStatus.NO_DECISION
    explanation = _explanation(items, source.probability_results, status)
    return DealSummaryResult(
        status, items, recommendations, tuple(evidence), source.probability_results,
        unresolved, errors, explanation,
    )


def _failure(
    code: DealSummaryFailureCode,
    explanation: str,
    *,
    status: DealSummaryStatus = DealSummaryStatus.ERROR,
) -> DealSummaryResult:
    return DealSummaryResult(status, (), (), (), (), (), (), explanation, code)


def _explanation(
    items: tuple[DealSummaryItem, ...],
    probability_results: tuple[ProbabilityEngineResult, ...],
    status: DealSummaryStatus,
) -> str:
    details = [f"{item.stage.value}: {item.result.status.value}" for item in items]
    details.extend(f"probability-evidence: {result.status.value}" for result in probability_results)
    return f"Summary {status.value}. " + "; ".join(details) + "."
