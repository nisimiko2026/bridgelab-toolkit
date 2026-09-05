"""One-pass integration of structured deal summary and deterministic rendering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .deal_analysis import DealAnalysisResult
from .deal_summary import DealSummaryInput, DealSummaryResult, DealSummaryStatus, build_deal_summary
from .deal_summary_rendering import DealSummaryRendering, render_deal_summary


class DealSummaryPipelineStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NO_DECISION = "no-decision"
    ERROR = "error"


class DealSummaryPipelineFailureCode(str, Enum):
    INVALID_INPUT = "invalid-input"
    SUMMARY_BUILD_FAILED = "summary-build-failed"
    RENDERING_FAILED = "rendering-failed"


@dataclass(frozen=True, slots=True)
class DealSummaryPipelineResult:
    status: DealSummaryPipelineStatus
    source: DealSummaryInput | None
    original_subsystem_results: tuple[DealAnalysisResult, ...]
    summary: DealSummaryResult
    rendering: DealSummaryRendering
    failure_code: DealSummaryPipelineFailureCode | None = None
    explanation: str = ""

    @property
    def text(self) -> str:
        return self.rendering.text


def build_and_render_deal_summary(source: DealSummaryInput) -> DealSummaryPipelineResult:
    """Build once and render once without rerunning any subsystem engine."""

    if not isinstance(source, DealSummaryInput):
        empty = build_deal_summary(DealSummaryInput())
        rendered = render_deal_summary(empty)
        return DealSummaryPipelineResult(
            DealSummaryPipelineStatus.ERROR, None, (), empty, rendered,
            DealSummaryPipelineFailureCode.INVALID_INPUT,
            "Integration requires DealSummaryInput.",
        )
    try:
        summary = build_deal_summary(source)
    except (TypeError, ValueError) as exc:
        empty = build_deal_summary(DealSummaryInput())
        rendered = render_deal_summary(empty)
        return DealSummaryPipelineResult(
            DealSummaryPipelineStatus.ERROR, source, source.stage_results, empty, rendered,
            DealSummaryPipelineFailureCode.SUMMARY_BUILD_FAILED, str(exc),
        )
    try:
        rendering = render_deal_summary(summary)
    except (TypeError, ValueError) as exc:
        fallback = render_deal_summary(build_deal_summary(DealSummaryInput()))
        return DealSummaryPipelineResult(
            DealSummaryPipelineStatus.ERROR, source, source.stage_results, summary, fallback,
            DealSummaryPipelineFailureCode.RENDERING_FAILED, str(exc),
        )
    status = {
        DealSummaryStatus.AVAILABLE: DealSummaryPipelineStatus.COMPLETE,
        DealSummaryStatus.PARTIAL: DealSummaryPipelineStatus.PARTIAL,
        DealSummaryStatus.NO_DECISION: DealSummaryPipelineStatus.NO_DECISION,
        DealSummaryStatus.ERROR: DealSummaryPipelineStatus.ERROR,
    }[summary.status]
    return DealSummaryPipelineResult(
        status, source, source.stage_results, summary, rendering,
        explanation="Structured summary and deterministic rendering completed without recomputation.",
    )
