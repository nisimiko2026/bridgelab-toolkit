"""Presentation-neutral application boundary for full-deal analysis."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from .auction import Auction, Contract
from .bidding_rules import BiddingContext, SystemContext
from .deal_analysis import AnalysisStage
from .deals import Deal
from .declarer_play_state import DeclarerPlayInput, PlayedCard, Trick
from .defensive_play_state import DefensivePlayInput
from .engine_router import BiddingEngineRouter
from .full_deal_analysis import (
    FullDealAnalysisInput,
    FullDealAnalysisResult,
    FullDealProbabilityRequest,
    analyze_full_deal,
    full_deal_analysis_to_dict,
)
from .models import Card, Hand, Seat, Vulnerability
from .opening_lead_state import OpeningLeadInput
from .policy_registry import PolicyRegistry
from .probability_engine import ProbabilityContext
from .probability_questions import KnownCardCountQuestion


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
    policies: PolicyRegistry = field(default_factory=PolicyRegistry)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_stages", tuple(self.requested_stages))
        object.__setattr__(
            self, "probability_requests", tuple(self.probability_requests)
        )


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


def _require_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a JSON object")
    if any(not isinstance(key, str) for key in value):
        raise TypeError(f"{field} keys must be strings")
    return value  # type: ignore[return-value]


def _reject_unknown_fields(
    value: Mapping[str, object], supported: set[str], field: str
) -> None:
    unknown = sorted(set(value) - supported)
    if unknown:
        raise ValueError(f"Unsupported {field} field: {unknown[0]!r}.")


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    return value


def _bidding_context_from_dict(value: object) -> BiddingContext | None:
    if value is None:
        return None
    bidding = _require_mapping(value, "bidding")
    required = {"hand", "auction", "vulnerability", "system"}
    _reject_unknown_fields(bidding, required, "bidding")
    missing = sorted(required - set(bidding))
    if missing:
        raise ValueError(f"Missing bidding field: {missing[0]!r}.")

    auction_value = _require_mapping(bidding["auction"], "bidding.auction")
    _reject_unknown_fields(auction_value, {"dealer", "calls"}, "bidding.auction")
    if "dealer" not in auction_value:
        raise ValueError("Missing bidding.auction field: 'dealer'.")
    calls = auction_value.get("calls", ())
    if not isinstance(calls, (list, tuple)):
        raise TypeError("bidding.auction.calls must be an array")
    if any(not isinstance(call, str) for call in calls):
        raise TypeError("bidding.auction.calls values must be strings")
    auction = Auction(
        Seat.parse(
            _require_string(auction_value["dealer"], "bidding.auction.dealer")
        ),
        calls,
    )

    vulnerability_text = _require_string(
        bidding["vulnerability"], "bidding.vulnerability"
    )
    try:
        vulnerability = Vulnerability(vulnerability_text)
    except ValueError as exc:
        raise ValueError(
            "bidding.vulnerability must be one of: None, NS, EW, Both"
        ) from exc

    system_value = _require_mapping(bidding["system"], "bidding.system")
    _reject_unknown_fields(system_value, {"id", "options"}, "bidding.system")
    if "id" not in system_value:
        raise ValueError("Missing bidding.system field: 'id'.")
    options = _require_mapping(
        system_value.get("options", {}), "bidding.system.options"
    )
    if any(not isinstance(item, str) for item in options.values()):
        raise TypeError("bidding.system.options values must be strings")
    system = SystemContext.from_mapping(
        _require_string(system_value["id"], "bidding.system.id"), options
    )

    return BiddingContext.create(
        hand=Hand.parse(_require_string(bidding["hand"], "bidding.hand")),
        auction=auction,
        vulnerability=vulnerability,
        system=system,
    )


def _card_set_from_array(value: object, field: str) -> frozenset[Card]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{field} must be an array")
    cards = tuple(Card.parse(_require_string(item, field)) for item in value)
    if len(cards) != len(set(cards)):
        raise ValueError(f"{field} contains a duplicate card")
    return frozenset(cards)


def _played_card_from_dict(value: object, field: str) -> PlayedCard:
    play = _require_mapping(value, field)
    required = {"seat", "card"}
    _reject_unknown_fields(play, required, field)
    missing = sorted(required - set(play))
    if missing:
        raise ValueError(f"Missing {field} field: {missing[0]!r}.")
    return PlayedCard(
        Seat.parse(_require_string(play["seat"], f"{field}.seat")),
        Card.parse(_require_string(play["card"], f"{field}.card")),
    )


def _trick_from_dict(value: object, field: str, *, complete: bool) -> Trick:
    trick_value = _require_mapping(value, field)
    required = {"leader", "plays"}
    _reject_unknown_fields(trick_value, required, field)
    missing = sorted(required - set(trick_value))
    if missing:
        raise ValueError(f"Missing {field} field: {missing[0]!r}.")
    plays_value = trick_value["plays"]
    if not isinstance(plays_value, (list, tuple)):
        raise TypeError(f"{field}.plays must be an array")
    trick = Trick(
        Seat.parse(_require_string(trick_value["leader"], f"{field}.leader")),
        tuple(
            _played_card_from_dict(play, f"{field}.plays[{index}]")
            for index, play in enumerate(plays_value)
        ),
    )
    if complete and not trick.is_complete:
        raise ValueError(f"{field} must contain exactly four plays")
    if not complete and trick.is_complete:
        raise ValueError(f"{field} cannot already be complete")
    return trick


def _declarer_play_input_from_dict(value: object) -> DeclarerPlayInput | None:
    if value is None:
        return None
    declarer = _require_mapping(value, "declarer_play")
    required = {
        "contract",
        "declarer_cards",
        "dummy_cards",
        "completed_tricks",
        "current_trick",
    }
    supported = required | {"vulnerability"}
    _reject_unknown_fields(declarer, supported, "declarer_play")
    missing = sorted(required - set(declarer))
    if missing:
        raise ValueError(f"Missing declarer_play field: {missing[0]!r}.")

    contract = Contract.parse(
        _require_string(declarer["contract"], "declarer_play.contract")
    )
    completed_value = declarer["completed_tricks"]
    if not isinstance(completed_value, (list, tuple)):
        raise TypeError("declarer_play.completed_tricks must be an array")
    completed = tuple(
        _trick_from_dict(
            trick, f"declarer_play.completed_tricks[{index}]", complete=True
        )
        for index, trick in enumerate(completed_value)
    )
    current = _trick_from_dict(
        declarer["current_trick"], "declarer_play.current_trick", complete=False
    )
    current_actor = (
        current.leader if not current.plays else current.plays[-1].seat.next()
    )
    vulnerability = None
    if "vulnerability" in declarer:
        vulnerability_text = _require_string(
            declarer["vulnerability"], "declarer_play.vulnerability"
        )
        try:
            vulnerability = Vulnerability(vulnerability_text)
        except ValueError as exc:
            raise ValueError(
                "declarer_play.vulnerability must be one of: None, NS, EW, Both"
            ) from exc
    return DeclarerPlayInput(
        contract=contract,
        declarer_seat=contract.declarer,
        declarer_cards=_card_set_from_array(
            declarer["declarer_cards"], "declarer_play.declarer_cards"
        ),
        dummy_cards=_card_set_from_array(
            declarer["dummy_cards"], "declarer_play.dummy_cards"
        ),
        current_actor=current_actor,
        completed_tricks=completed,
        current_trick=current,
        vulnerability=vulnerability,
        opening_leader=contract.declarer.next(),
    )


def _declarer_deal_conflict(
    deal: Deal, source: DeclarerPlayInput
) -> str | None:
    if source.contract is None:
        return None
    declarer = source.contract.declarer
    dummy = declarer.partner()
    visible = (
        (declarer, source.declarer_cards),
        (dummy, source.dummy_cards),
    )
    for seat, cards in visible:
        if cards is not None and not cards <= deal.hand(seat).cards:
            return "Declarer-play holdings conflict with card ownership in the deal."
    tricks = (*source.completed_tricks, source.current_trick) if (
        source.completed_tricks is not None and source.current_trick is not None
    ) else ()
    played_cards: set[Card] = set()
    for trick in tricks:
        for play in trick.plays:
            if play.card not in deal.hand(play.seat).cards:
                return "Declarer-play history conflicts with card ownership in the deal."
            played_cards.add(play.card)
    if any(cards is not None and cards & played_cards for _, cards in visible):
        return "Declarer-play holdings conflict with played-card history."
    return None


def full_deal_application_request_from_dict(
    payload: Mapping[str, object],
) -> FullDealApplicationRequest:
    """Build the narrow JSON-facing request without performing domain analysis."""

    if not isinstance(payload, Mapping):
        raise TypeError("application request must be a JSON object")
    supported = {
        "bidding",
        "deal",
        "declarer_play",
        "requested_stages",
        "probability_requests",
    }
    unknown = sorted(set(payload) - supported)
    if unknown:
        raise ValueError(f"Unsupported request field: {unknown[0]!r}.")
    stages = payload.get("requested_stages", ())
    probabilities = payload.get("probability_requests", ())
    if not isinstance(stages, (list, tuple)):
        stages = (stages,)
    if not isinstance(probabilities, (list, tuple)):
        probabilities = (probabilities,)
    converted: list[object] = []
    for item in probabilities:
        if not isinstance(item, Mapping) or item.get("question") != "known-card-count":
            converted.append(item)
            continue
        context = item.get("context")
        if not isinstance(context, Mapping):
            converted.append(item)
            continue
        try:
            visible = frozenset(
                Card.parse(str(value)) for value in context.get("visible_cards", ())
            )
            played = frozenset(
                Card.parse(str(value)) for value in context.get("played_cards", ())
            )
            unknown_count = int(context["unknown_card_count"])
        except (KeyError, TypeError, ValueError):
            converted.append(item)
            continue
        converted.append(
            FullDealProbabilityRequest(
                KnownCardCountQuestion(),
                ProbabilityContext(visible, played, unknown_count),
            )
        )
    return FullDealApplicationRequest(
        deal=payload.get("deal"),
        requested_stages=tuple(stages),
        bidding=_bidding_context_from_dict(payload.get("bidding")),
        declarer_play=_declarer_play_input_from_dict(payload.get("declarer_play")),
        probability_requests=tuple(converted),  # type: ignore[arg-type]
    )


def full_deal_application_response_to_dict(
    response: FullDealApplicationResponse,
) -> dict[str, object]:
    """Return a deterministic, JSON-ready application response."""

    if not isinstance(response, FullDealApplicationResponse):
        raise TypeError("response must be FullDealApplicationResponse")
    return {
        "success": response.success,
        "status": response.status,
        "errors": tuple(
            {"code": error.code.value, "field": error.field, "message": error.message}
            for error in response.errors
        ),
        "result": response.structured_result,
        "rendered_text": response.rendered_text,
        "diagnostics": response.diagnostics,
    }


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
    serialized_deal_supplied = isinstance(deal, str)
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
    if (
        serialized_deal_supplied
        and isinstance(request.bidding, BiddingContext)
        and deal is not None
        and deal.hand(request.bidding.seat) != request.bidding.hand
    ):
        return FullDealApplicationValidationResult(
            None,
            (
                FullDealApplicationError(
                    FullDealApplicationErrorCode.VALIDATION_ERROR,
                    "bidding.hand",
                    "Bidding hand conflicts with the deal hand for the current bidder.",
                ),
            ),
        )
    if serialized_deal_supplied and request.declarer_play is not None and deal is not None:
        conflict = _declarer_deal_conflict(deal, request.declarer_play)
        if conflict is not None:
            return FullDealApplicationValidationResult(
                None,
                (
                    FullDealApplicationError(
                        FullDealApplicationErrorCode.VALIDATION_ERROR,
                        "declarer_play",
                        conflict,
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
