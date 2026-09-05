"""Presentation-neutral application boundary for full-deal analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bidding_rules import BiddingContext
from .deal_analysis import AnalysisStage
from .deals import Deal
from .declarer_play_state import DeclarerPlayInput
from .defensive_play_state import DefensivePlayInput
from .engine_router import BiddingEngineRouter
from .full_deal_analysis import (
    FullDealAnalysisInput,
    FullDealAnalysisResult,
    FullDealProbabilityRequest,
    analyze_full_deal,
    full_deal_analysis_to_dict,
)
from .opening_lead_state import OpeningLeadInput
from .policy_registry import PolicyRegistry


class FullDealApplicationErrorCode(str, Enum):
    PARSE_ERROR = "parse-error"
    VALIDATION_ERROR = "validation-error"
    UNSUPPORTED_INPUT = "unsupported-input"
    PRODUCTION_ERROR = "production-error"


@dataclass(frozen=True, slots=True)
class FullDealApplicationError:
    code: FullDealApplicationErrorCode
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class FullDealApplicationRequest:
    """External request using narrow strings plus canonical legal-view stage inputs."""

    deal: Deal | str | None = None
    requested_stages: tuple[str | AnalysisStage, ...] = ()
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
class FullDealApplicationValidationResult:
    canonical_request: FullDealAnalysisInput | None
    errors: tuple[FullDealApplicationError, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.canonical_request is not None and not self.errors


@dataclass(frozen=True, slots=True)
class FullDealApplicationResponse:
    success: bool
    status: str
    canonical_result: FullDealAnalysisResult | None
    structured_result: dict[str, object] | None
    rendered_text: str
    errors: tuple[FullDealApplicationError, ...] = ()
    diagnostics: tuple[tuple[str, str], ...] = ()


_STAGE_ALIASES = {
    "auction": AnalysisStage.AUCTION,
    "opening-lead": AnalysisStage.OPENING_LEAD,
    "declarer-play": AnalysisStage.DECLARER_PLAY,
    "defensive-play": AnalysisStage.DEFENSIVE_PLAY,
}


def application_request_to_full_deal_input(
    request: FullDealApplicationRequest,
) -> FullDealApplicationValidationResult:
    """Parse only unambiguous external values into canonical production types."""

    if not isinstance(request, FullDealApplicationRequest):
        return FullDealApplicationValidationResult(
            None,
            (
                FullDealApplicationError(
                    FullDealApplicationErrorCode.UNSUPPORTED_INPUT,
                    "request",
                    "Expected FullDealApplicationRequest.",
                ),
            ),
        )
    deal = request.deal
    if isinstance(deal, str):
        try:
            deal = Deal.parse(deal)
        except (TypeError, ValueError) as exc:
            return FullDealApplicationValidationResult(
                None,
                (
                    FullDealApplicationError(
                        FullDealApplicationErrorCode.PARSE_ERROR, "deal", str(exc)
                    ),
                ),
            )
    elif deal is not None and not isinstance(deal, Deal):
        return FullDealApplicationValidationResult(
            None,
            (
                FullDealApplicationError(
                    FullDealApplicationErrorCode.UNSUPPORTED_INPUT,
                    "deal",
                    "Deal must be a canonical Deal or serialized deal string.",
                ),
            ),
        )
    stages: list[AnalysisStage] = []
    errors: list[FullDealApplicationError] = []
    for index, value in enumerate(request.requested_stages):
        if isinstance(value, AnalysisStage):
            stage = value
        elif isinstance(value, str):
            normalized = value.strip().casefold().replace("_", "-")
            stage = _STAGE_ALIASES.get(normalized)
            if stage is None:
                errors.append(
                    FullDealApplicationError(
                        FullDealApplicationErrorCode.VALIDATION_ERROR,
                        f"requested_stages[{index}]",
                        f"Unsupported analysis stage: {value!r}.",
                    )
                )
                continue
        else:
            errors.append(
                FullDealApplicationError(
                    FullDealApplicationErrorCode.UNSUPPORTED_INPUT,
                    f"requested_stages[{index}]",
                    "Stage must be an AnalysisStage or supported string.",
                )
            )
            continue
        if stage not in stages:
            stages.append(stage)
    if any(
        not isinstance(item, FullDealProbabilityRequest)
        for item in request.probability_requests
    ):
        errors.append(
            FullDealApplicationError(
                FullDealApplicationErrorCode.VALIDATION_ERROR,
                "probability_requests",
                "Probability requests must use FullDealProbabilityRequest.",
            )
        )
    if errors:
        return FullDealApplicationValidationResult(None, tuple(errors))
    canonical = FullDealAnalysisInput(
        deal,
        tuple(stages),
        request.bidding,
        request.opening_lead,
        request.declarer_play,
        request.defensive_play,
        request.probability_requests,
        request.policies,
    )
    return FullDealApplicationValidationResult(canonical)


def analyze_full_deal_application(
    request: FullDealApplicationRequest,
    *,
    bidding_router: BiddingEngineRouter | None = None,
) -> FullDealApplicationResponse:
    """Validate once, orchestrate once, and reuse canonical serialization/rendering."""

    validation = application_request_to_full_deal_input(request)
    if not validation.is_valid:
        return FullDealApplicationResponse(
            False,
            "error",
            None,
            None,
            "",
            validation.errors,
            (("validation", "failed"), ("production-called", "no")),
        )
    assert validation.canonical_request is not None
    try:
        result = analyze_full_deal(
            validation.canonical_request, bidding_router=bidding_router
        )
        structured = full_deal_analysis_to_dict(result)
    except (TypeError, ValueError) as exc:
        error = FullDealApplicationError(
            FullDealApplicationErrorCode.PRODUCTION_ERROR, "production", str(exc)
        )
        return FullDealApplicationResponse(
            False,
            "error",
            None,
            None,
            "",
            (error,),
            (("validation", "passed"), ("production-called", "yes")),
        )
    return FullDealApplicationResponse(
        result.status.value != "error",
        result.status.value,
        result,
        structured,
        result.text,
        diagnostics=(
            ("validation", "passed"),
            ("production-called", "yes"),
            ("serialization", "canonical"),
            ("rendering", "phase14b"),
        ),
    )
