"""Deterministic presentation of an existing structured deal summary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bidding_rules import KnowledgeSource
from .deal_analysis import ActionKind, AnalysisStage, AnalysisStatus
from .deal_summary import DealSummaryItem, DealSummaryResult, DealSummaryStatus
from .probability_engine import ProbabilityEngineResult
from .probability_evidence import ProbabilityEvidence


class DealSummaryRenderingStatus(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    NO_DECISION = "no-decision"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class DealSummaryRenderedSection:
    label: str
    stage: AnalysisStage | None
    status: str
    text: str
    sources: tuple[KnowledgeSource, ...]
    evidence: tuple[ProbabilityEvidence, ...]
    trace: tuple[tuple[str, str], ...]
    summary_item: DealSummaryItem | None = None
    probability_result: ProbabilityEngineResult | None = None


@dataclass(frozen=True, slots=True)
class DealSummaryRendering:
    status: DealSummaryRenderingStatus
    summary_status: DealSummaryStatus
    header: str
    sections: tuple[DealSummaryRenderedSection, ...]
    source_references: tuple[KnowledgeSource, ...]
    evidence_references: tuple[ProbabilityEvidence, ...]
    text: str
    original_summary: DealSummaryResult


_STATUS_TEXT = {
    DealSummaryStatus.AVAILABLE: "Analysis contains available recommendations or evidence.",
    DealSummaryStatus.PARTIAL: "Analysis is partial; some stages remain unresolved.",
    DealSummaryStatus.NO_DECISION: "No actionable recommendation is currently available.",
    DealSummaryStatus.ERROR: "The analysis contains an error.",
}


def render_deal_summary(summary: DealSummaryResult) -> DealSummaryRendering:
    """Render preserved fields only; perform no bridge or probability reasoning."""

    if not isinstance(summary, DealSummaryResult):
        raise TypeError("summary must be DealSummaryResult")
    sections = [_render_stage(item) for item in summary.items]
    sections.extend(_render_probability(result) for result in summary.probability_results)
    sources = tuple(source for section in sections for source in section.sources)
    evidence = tuple(item for section in sections for item in section.evidence)
    header = "Deal analysis summary"
    text_parts = [header, _STATUS_TEXT[summary.status]]
    text_parts.extend(section.text for section in sections)
    if not sections and summary.explanation:
        text_parts.append(summary.explanation)
    status = DealSummaryRenderingStatus(summary.status.value)
    return DealSummaryRendering(
        status, summary.status, header, tuple(sections), sources, evidence,
        "\n\n".join(text_parts), summary,
    )


def _render_stage(item: DealSummaryItem) -> DealSummaryRenderedSection:
    result = item.result
    label = item.stage.value.replace("-", " ").title()
    if result.status is AnalysisStatus.RECOMMENDATION:
        outcome = _action_text(item)
    elif result.status is AnalysisStatus.ABSTAIN:
        outcome = "Abstained"
    elif result.status is AnalysisStatus.ERROR:
        outcome = "Error"
    else:
        outcome = "No decision"
    code = "" if result.abstention_code is None else f" [{result.abstention_code.value}]"
    text = f"{label}: {outcome}{code}. {result.explanation}"
    sources = tuple(
        evidence.source for evidence in result.evidence if evidence.source is not None
    )
    trace = tuple(result.debug_metadata)
    if trace:
        text += " Trace: " + ", ".join(f"{key}={value}" for key, value in trace) + "."
    if sources:
        text += " Sources: " + ", ".join(source.serialize() for source in sources) + "."
    return DealSummaryRenderedSection(
        label, item.stage, result.status.value, text, sources,
        result.probability_evidence, trace, summary_item=item,
    )


def _action_text(item: DealSummaryItem) -> str:
    action = item.result.action
    if action.kind is ActionKind.BID:
        assert action.bid is not None
        return f"Recommend {action.bid.serialize()}"
    if action.kind is ActionKind.OPENING_LEAD:
        assert action.card is not None
        return f"Lead {action.card.serialize()}"
    if action.kind in {ActionKind.CARD_PLAY, ActionKind.DEFENSIVE_CARD}:
        assert action.card is not None
        return f"Play {action.card.serialize()}"
    return "Recommendation recorded with no action"


def _render_probability(result: ProbabilityEngineResult) -> DealSummaryRenderedSection:
    lines = [f"Probability evidence: {result.status.value}."]
    if result.mode is not None:
        lines.append(f"Mode: {result.mode.value}.")
    sources: list[KnowledgeSource] = []
    for evidence in result.evidence:
        lines.append(f"{evidence.subject}: {evidence.result}.")
        lines.extend(f"{key}: {value}." for key, value in evidence.known_facts)
        lines.extend(f"Assumption: {assumption}" for assumption in evidence.assumptions)
        if evidence.source is not None:
            sources.append(evidence.source)
    trace = result.trace
    if trace:
        lines.append("Trace: " + ", ".join(f"{key}={value}" for key, value in trace) + ".")
    if sources:
        lines.append("Sources: " + ", ".join(source.serialize() for source in sources) + ".")
    return DealSummaryRenderedSection(
        "Probability Evidence", None, result.status.value, " ".join(lines),
        tuple(sources), result.evidence, trace, probability_result=result,
    )
