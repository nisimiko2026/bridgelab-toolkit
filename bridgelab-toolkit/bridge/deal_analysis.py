"""Typed, theory-neutral end-to-end deal-decision analysis architecture."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .auction import Call
from .bidding_rules import BiddingContext, KnowledgeSource
from .engine_router import BiddingEngineRouter
from .models import Card, Seat


class AnalysisStage(str, Enum):
    AUCTION = "auction"
    OPENING_LEAD = "opening-lead"
    DECLARER_PLAY = "declarer-play"
    DEFENSIVE_PLAY = "defensive-play"
    DEAL_SUMMARY = "deal-summary"


class AnalysisStatus(str, Enum):
    RECOMMENDATION = "recommendation"
    ABSTAIN = "abstain"
    NO_DECISION = "no-decision"
    ERROR = "error"


class ActionKind(str, Enum):
    BID = "bid"
    CARD_PLAY = "card-play"
    OPENING_LEAD = "opening-lead"
    DEFENSIVE_CARD = "defensive-card"
    NONE = "none"


class AbstentionCode(str, Enum):
    NO_ROUTE = "no-route"
    RULE_ABSTAINED = "rule-abstained"
    SOURCE_INSUFFICIENT = "source-insufficient"
    POLICY_REQUIRED = "policy-required"
    MISSING_STATE = "missing-state"
    UNSUPPORTED_STAGE = "unsupported-stage"
    AMBIGUOUS_ACTION = "ambiguous-action"


class Subsystem(str, Enum):
    BIDDING = "bidding"
    DECLARER_PLAY = "declarer-play"
    DEFENSE = "defense"
    PROBABILITY = "probability"
    SOURCE = "source"


@dataclass(frozen=True, slots=True)
class AnalysisAction:
    kind: ActionKind
    bid: Call | None = None
    card: Card | None = None

    def __post_init__(self) -> None:
        if self.kind is ActionKind.BID and (self.bid is None or self.card is not None):
            raise ValueError("bid action requires only a bid")
        if self.kind in {ActionKind.CARD_PLAY, ActionKind.OPENING_LEAD, ActionKind.DEFENSIVE_CARD} and (
            self.card is None or self.bid is not None
        ):
            raise ValueError("card action requires only a card")
        if self.kind is ActionKind.NONE and (self.bid is not None or self.card is not None):
            raise ValueError("none action cannot carry a bid or card")


@dataclass(frozen=True, slots=True)
class AnalysisEvidence:
    kind: str
    explanation: str
    source: KnowledgeSource | None = None
    value: str | None = None


@dataclass(frozen=True, slots=True)
class SubsystemResult:
    subsystem: Subsystem
    attempted: bool
    status: AnalysisStatus
    action: AnalysisAction
    explanation: str
    evidence: tuple[AnalysisEvidence, ...] = ()
    abstention_code: AbstentionCode | None = None


@dataclass(frozen=True, slots=True)
class DealAnalysisContext:
    stage: AnalysisStage | None = None
    bidding: BiddingContext | None = None


@dataclass(frozen=True, slots=True)
class DealAnalysisResult:
    stage: AnalysisStage
    seat: Seat | None
    status: AnalysisStatus
    action: AnalysisAction
    explanation: str
    evidence: tuple[AnalysisEvidence, ...]
    subsystem_results: tuple[SubsystemResult, ...]
    abstention_code: AbstentionCode | None = None
    probability_evidence: tuple[AnalysisEvidence, ...] = ()
    debug_metadata: tuple[tuple[str, str], ...] = ()


def detect_analysis_stage(context: DealAnalysisContext) -> AnalysisStage:
    if context.stage is not None:
        return context.stage
    if context.bidding is not None:
        return AnalysisStage.AUCTION
    return AnalysisStage.DEAL_SUMMARY


def _inactive(subsystem: Subsystem, stage: AnalysisStage) -> SubsystemResult:
    return SubsystemResult(
        subsystem,
        False,
        AnalysisStatus.NO_DECISION,
        AnalysisAction(ActionKind.NONE),
        f"No production {subsystem.value} adapter is available for {stage.value} in Phase 13A.",
        abstention_code=AbstentionCode.UNSUPPORTED_STAGE,
    )


def analyze_deal_decision(
    context: DealAnalysisContext,
    *,
    bidding_router: BiddingEngineRouter | None = None,
) -> DealAnalysisResult:
    """Dispatch only to existing production systems and normalize their result."""
    stage = detect_analysis_stage(context)
    inactive = tuple(
        _inactive(system, stage)
        for system in (Subsystem.DECLARER_PLAY, Subsystem.DEFENSE, Subsystem.PROBABILITY, Subsystem.SOURCE)
    )
    if stage is not AnalysisStage.AUCTION or context.bidding is None:
        return DealAnalysisResult(
            stage,
            None if context.bidding is None else context.bidding.seat,
            AnalysisStatus.NO_DECISION,
            AnalysisAction(ActionKind.NONE),
            f"Stage {stage.value} has no production recommendation adapter.",
            (),
            inactive,
            AbstentionCode.UNSUPPORTED_STAGE,
        )
    if bidding_router is None:
        raise ValueError("auction analysis requires an explicit production bidding router")

    match = bidding_router.match(context.bidding)
    engine_result = bidding_router.evaluate(context.bidding)
    if engine_result.has_recommendation:
        decision = engine_result.recommended
        assert decision is not None and decision.candidate is not None
        evidence = tuple(
            AnalysisEvidence("knowledge-source", decision.explanation, source)
            for source in decision.sources
        )
        bidding = SubsystemResult(
            Subsystem.BIDDING,
            True,
            AnalysisStatus.RECOMMENDATION,
            AnalysisAction(ActionKind.BID, bid=decision.candidate),
            decision.explanation,
            evidence,
        )
        return DealAnalysisResult(
            stage,
            context.bidding.seat,
            AnalysisStatus.RECOMMENDATION,
            bidding.action,
            decision.explanation,
            evidence,
            (bidding, *inactive),
            debug_metadata=(("route", match.route_id if match else "fallback"), ("rule", decision.rule_id)),
        )

    rejected = tuple(decision.explanation for decision in engine_result.decisions if decision.explanation)
    policy_required = any("policy" in reason.casefold() for reason in rejected)
    code = AbstentionCode.NO_ROUTE if match is None else (
        AbstentionCode.POLICY_REQUIRED if policy_required else AbstentionCode.RULE_ABSTAINED
    )
    explanation = (
        "No production route supports this auction."
        if match is None
        else "The routed production bidding rules abstained."
    )
    evidence = tuple(AnalysisEvidence("rule-rejection", reason) for reason in rejected)
    bidding = SubsystemResult(
        Subsystem.BIDDING,
        True,
        AnalysisStatus.ABSTAIN,
        AnalysisAction(ActionKind.NONE),
        explanation,
        evidence,
        code,
    )
    return DealAnalysisResult(
        stage,
        context.bidding.seat,
        AnalysisStatus.ABSTAIN,
        bidding.action,
        explanation,
        evidence,
        (bidding, *inactive),
        code,
        debug_metadata=(("route", match.route_id if match else "none"),),
    )
