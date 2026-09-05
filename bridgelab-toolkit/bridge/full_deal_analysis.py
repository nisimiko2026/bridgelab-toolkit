"""Bounded orchestration of existing deal-analysis stages and Phase 14 output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .bidding_rules import BiddingContext
from .deal_analysis import (
    AnalysisStage,
    DealAnalysisContext,
    DealAnalysisResult,
    analyze_deal_decision,
)
from .deal_summary import DealSummaryInput, DealSummaryResult
from .deal_summary_pipeline import (
    DealSummaryPipelineResult,
    DealSummaryPipelineStatus,
    build_and_render_deal_summary,
)
from .deal_summary_rendering import DealSummaryRendering
from .deals import Deal
from .declarer_play_state import DeclarerPlayInput, DeclarerPlayState
from .declarer_recommendation import DeclarerRecommendation
from .defensive_play_state import DefensivePlayInput
from .engine_router import BiddingEngineRouter
from .opening_lead_state import OpeningLeadInput
from .policy_registry import PolicyRegistry
from .probability_engine import (
    DEFAULT_PROBABILITY_ENGINE_REGISTRY,
    ProbabilityContext,
    ProbabilityEngineRegistry,
    ProbabilityEngineResult,
    evaluate_probability,
)
from .probability_questions import ProbabilityQuestion


class FullDealSkipReason(str, Enum):
    NOT_REQUESTED = "not-requested"
    INSUFFICIENT_STAGE_STATE = "insufficient-stage-state"
    STAGE_NOT_APPLICABLE = "stage-not-applicable"
    ENGINE_UNAVAILABLE = "engine-unavailable"
    UNSUPPORTED_REQUEST = "unsupported-request"


@dataclass(frozen=True, slots=True)
class FullDealProbabilityRequest:
    question: ProbabilityQuestion
    context: ProbabilityContext | None = None


@dataclass(frozen=True, slots=True)
class FullDealAnalysisInput:
    """Explicit legal-view inputs; ``deal`` is retained but never exposed to adapters."""

    deal: Deal | None = None
    requested_stages: tuple[AnalysisStage, ...] = ()
    bidding: BiddingContext | None = None
    opening_lead: OpeningLeadInput | None = None
    declarer_play: DeclarerPlayInput | None = None
    defensive_play: DefensivePlayInput | None = None
    probability_requests: tuple[FullDealProbabilityRequest, ...] = ()
    policies: PolicyRegistry = PolicyRegistry()

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_stages", tuple(self.requested_stages))
        object.__setattr__(self, "probability_requests", tuple(self.probability_requests))


@dataclass(frozen=True, slots=True)
class FullDealSkippedStage:
    stage: str
    reason: FullDealSkipReason
    explanation: str


@dataclass(frozen=True, slots=True)
class FullDealAnalysisResult:
    original_request: FullDealAnalysisInput | None
    requested_stages: tuple[str, ...]
    applicable_stages: tuple[str, ...]
    attempted_stages: tuple[str, ...]
    skipped_stages: tuple[FullDealSkippedStage, ...]
    subsystem_results: tuple[DealAnalysisResult, ...]
    probability_results: tuple[ProbabilityEngineResult, ...]
    pipeline: DealSummaryPipelineResult
    status: DealSummaryPipelineStatus
    trace: tuple[tuple[str, str], ...]

    @property
    def summary(self) -> DealSummaryResult:
        return self.pipeline.summary

    @property
    def rendering(self) -> DealSummaryRendering:
        return self.pipeline.rendering

    @property
    def text(self) -> str:
        return self.pipeline.text


_STAGE_ORDER = (
    AnalysisStage.AUCTION,
    AnalysisStage.OPENING_LEAD,
    AnalysisStage.DECLARER_PLAY,
    AnalysisStage.DEFENSIVE_PLAY,
)


def _invalid_result(
    request: FullDealAnalysisInput | None,
    explanation: str,
) -> FullDealAnalysisResult:
    pipeline = build_and_render_deal_summary(DealSummaryInput())
    skipped = FullDealSkippedStage(
        "request", FullDealSkipReason.UNSUPPORTED_REQUEST, explanation
    )
    return FullDealAnalysisResult(
        request,
        (),
        (),
        (),
        (skipped,),
        (),
        (),
        pipeline,
        DealSummaryPipelineStatus.ERROR,
        (("request", "invalid"), ("summary-built", "yes"), ("rendering-built", "yes")),
    )


def analyze_full_deal(
    request: FullDealAnalysisInput,
    *,
    bidding_router: BiddingEngineRouter | None = None,
    declarer_evaluator: Callable[[DeclarerPlayState], DeclarerRecommendation] | None = None,
    probability_registry: ProbabilityEngineRegistry = DEFAULT_PROBABILITY_ENGINE_REGISTRY,
) -> FullDealAnalysisResult:
    """Evaluate each explicit legal-view stage once, then reuse the Phase 14 pipeline."""

    if not isinstance(request, FullDealAnalysisInput):
        return _invalid_result(None, "Invalid full-deal request.")
    if any(not isinstance(stage, AnalysisStage) for stage in request.requested_stages):
        return _invalid_result(request, "Requested stages must use AnalysisStage values.")
    if any(
        not isinstance(item, FullDealProbabilityRequest)
        or not isinstance(item.question, ProbabilityQuestion)
        for item in request.probability_requests
    ):
        return _invalid_result(request, "Invalid probability request.")

    requested = tuple(stage for stage in _STAGE_ORDER if stage in request.requested_stages)
    stage_inputs = {
        AnalysisStage.AUCTION: request.bidding,
        AnalysisStage.OPENING_LEAD: request.opening_lead,
        AnalysisStage.DECLARER_PLAY: request.declarer_play,
        AnalysisStage.DEFENSIVE_PLAY: request.defensive_play,
    }
    applicable: list[str] = []
    attempted: list[str] = []
    skipped: list[FullDealSkippedStage] = []
    stage_results: list[DealAnalysisResult] = []
    for stage in requested:
        source = stage_inputs[stage]
        if source is None:
            skipped.append(
                FullDealSkippedStage(
                    stage.value,
                    FullDealSkipReason.INSUFFICIENT_STAGE_STATE,
                    "No explicit legal-view state input was supplied.",
                )
            )
            continue
        if stage is AnalysisStage.AUCTION and bidding_router is None:
            skipped.append(
                FullDealSkippedStage(
                    stage.value,
                    FullDealSkipReason.ENGINE_UNAVAILABLE,
                    "Auction orchestration requires an explicit bidding router.",
                )
            )
            continue
        applicable.append(stage.value)
        attempted.append(stage.value)
        context = DealAnalysisContext(
            stage=stage,
            bidding=source if stage is AnalysisStage.AUCTION else None,
            opening_lead=source if stage is AnalysisStage.OPENING_LEAD else None,
            declarer_play=source if stage is AnalysisStage.DECLARER_PLAY else None,
            defensive_play=source if stage is AnalysisStage.DEFENSIVE_PLAY else None,
        )
        stage_results.append(
            analyze_deal_decision(
                context,
                bidding_router=bidding_router,
                declarer_evaluator=declarer_evaluator,
            )
        )

    probability_results: list[ProbabilityEngineResult] = []
    for item in request.probability_requests:
        label = "probability-evidence"
        if item.context is None:
            skipped.append(
                FullDealSkippedStage(
                    label,
                    FullDealSkipReason.INSUFFICIENT_STAGE_STATE,
                    "Probability execution requires an explicit legal-view context.",
                )
            )
            continue
        applicable.append(label)
        attempted.append(label)
        probability_results.append(
            evaluate_probability(
                item.question, context=item.context, registry=probability_registry
            )
        )

    pipeline = build_and_render_deal_summary(
        DealSummaryInput(tuple(stage_results), tuple(probability_results))
    )
    requested_labels = tuple(stage.value for stage in requested) + tuple(
        "probability-evidence" for _ in request.probability_requests
    )
    trace = (
        ("requested", ",".join(requested_labels) or "none"),
        ("attempted", ",".join(attempted) or "none"),
        ("skipped", ",".join(item.stage for item in skipped) or "none"),
        ("summary-built", "yes"),
        ("rendering-built", "yes"),
    )
    return FullDealAnalysisResult(
        request,
        requested_labels,
        tuple(applicable),
        tuple(attempted),
        tuple(skipped),
        tuple(stage_results),
        tuple(probability_results),
        pipeline,
        pipeline.status,
        trace,
    )


def full_deal_analysis_to_dict(result: FullDealAnalysisResult) -> dict[str, object]:
    """Return a deterministic public representation without flattening provenance."""

    if not isinstance(result, FullDealAnalysisResult):
        raise TypeError("result must be FullDealAnalysisResult")

    def source_value(source: object) -> str | None:
        return None if source is None else source.serialize()  # type: ignore[attr-defined]

    subsystem = tuple(
        {
            "stage": item.stage.value,
            "seat": None if item.seat is None else item.seat.value,
            "status": item.status.value,
            "action": {
                "kind": item.action.kind.value,
                "bid": None if item.action.bid is None else item.action.bid.serialize(),
                "card": None if item.action.card is None else item.action.card.serialize(),
            },
            "explanation": item.explanation,
            "abstention_code": (
                None if item.abstention_code is None else item.abstention_code.value
            ),
            "sources": tuple(source_value(value.source) for value in item.evidence),
            "trace": item.debug_metadata,
        }
        for item in result.subsystem_results
    )
    probabilities = tuple(
        {
            "status": item.status.value,
            "mode": None if item.mode is None else item.mode.value,
            "formula": None if item.formula_id is None else item.formula_id.value,
            "failure_code": None if item.failure_code is None else item.failure_code.value,
            "explanation": item.explanation,
            "trace": item.trace,
            "evidence": tuple(
                {
                    "type": evidence.evidence_type.value,
                    "subject": evidence.subject,
                    "assumptions": evidence.assumptions,
                    "known_facts": evidence.known_facts,
                    "result": evidence.result,
                    "probability": evidence.probability,
                    "source": source_value(evidence.source),
                    "trace": evidence.trace,
                }
                for evidence in item.evidence
            ),
        }
        for item in result.probability_results
    )
    return {
        "status": result.status.value,
        "requested_stages": result.requested_stages,
        "applicable_stages": result.applicable_stages,
        "attempted_stages": result.attempted_stages,
        "skipped_stages": tuple(
            {
                "stage": item.stage,
                "reason": item.reason.value,
                "explanation": item.explanation,
            }
            for item in result.skipped_stages
        ),
        "subsystem_results": subsystem,
        "probability_results": probabilities,
        "summary_status": result.summary.status.value,
        "rendering_status": result.rendering.status.value,
        "rendered_text": result.text,
        "trace": result.trace,
    }
