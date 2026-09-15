"""Deterministic deal batches with one production opening analysis per deal."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .auction import Auction
from .bidding_rules import BiddingContext, SystemContext
from .deal_analysis import AnalysisStatus
from .deals import Deal, generate_deal
from .full_deal_application import (
    FullDealApplicationRequest,
    FullDealApplicationResponse,
    analyze_full_deal_application,
)
from .models import Seat, Vulnerability
from .sayc_route_configuration import create_standard_sayc_router


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    seed: int = 0
    deal_count: int = 100

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be an integer")
        if not isinstance(self.deal_count, int) or isinstance(self.deal_count, bool):
            raise TypeError("deal_count must be an integer")
        if self.deal_count < 1:
            raise ValueError("deal_count must be at least 1")


@dataclass(frozen=True, slots=True)
class SimulatedDeal:
    index: int
    dealer: Seat
    vulnerability: Vulnerability
    analyzed_hand: str
    status: AnalysisStatus
    recommended_call: str | None
    abstention_code: str | None
    rule_id: str | None
    route_id: str | None
    sources: tuple[str, ...]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class SimulationResult:
    seed: int
    requested_deals: int
    cases: tuple[SimulatedDeal, ...]
    recommendations: int
    abstains: int
    errors: int
    call_frequencies: tuple[tuple[str, int], ...]

    @property
    def completed_deals(self) -> int:
        return len(self.cases)


class AuctionOutcome(str, Enum):
    COMPLETE = "complete"
    ABSTAIN = "abstain"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class AuctionStep:
    index: int
    seat: Seat
    hand: str
    auction_before: tuple[str, ...]
    status: AnalysisStatus
    recommended_call: str | None
    abstention_code: str | None
    rule_id: str | None
    route_id: str | None
    sources: tuple[str, ...]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class FullAuctionResult:
    deal_index: int
    dealer: Seat
    vulnerability: Vulnerability
    final_calls: tuple[str, ...]
    steps: tuple[AuctionStep, ...]
    outcome: AuctionOutcome
    stopping_seat: Seat | None = None
    abstention_code: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class FullAuctionBatchResult:
    seed: int
    requested_deals: int
    auctions: tuple[FullAuctionResult, ...]
    complete: int
    abstain: int
    errors: int
    total_steps: int
    stopping_seat_counts: tuple[tuple[str, int], ...]
    abstention_code_counts: tuple[tuple[str, int], ...]
    route_use_counts: tuple[tuple[str, int], ...]

    @property
    def completed_simulations(self) -> int:
        return len(self.auctions)

    @property
    def completion_rate(self) -> float:
        return self.complete / self.completed_simulations


Analyzer = Callable[..., FullDealApplicationResponse]


def simulate_full_auction(
    *, deal_index: int, deal: Deal, dealer: Seat, vulnerability: Vulnerability,
    analyzer: Analyzer = analyze_full_deal_application,
) -> FullAuctionResult:
    """Advance one canonical auction until completion or an honest stop."""
    auction = Auction(dealer)
    router = create_standard_sayc_router()
    system = SystemContext("SAYC")
    steps: list[AuctionStep] = []
    while not auction.is_complete:
        seat = auction.next_seat
        hand = deal.hand(seat)
        before = tuple(call.serialize() for call in auction.calls)
        response = analyzer(
            FullDealApplicationRequest(
                requested_stages=("auction",),
                bidding=BiddingContext.create(
                    hand=hand, auction=auction, vulnerability=vulnerability,
                    system=system,
                ),
            ),
            bidding_router=router,
        )
        if not response.success or response.canonical_result is None:
            error = "; ".join(item.message for item in response.errors) or response.status
            step = AuctionStep(len(steps), seat, hand.serialize(), before,
                               AnalysisStatus.ERROR, None, None, None, None, (), error)
            return FullAuctionResult(deal_index, dealer, vulnerability, before,
                                     (*steps, step), AuctionOutcome.ERROR, seat, error=error)
        result = response.canonical_result.subsystem_results[0]
        call = None if result.action.bid is None else result.action.bid.serialize()
        trace = dict(result.debug_metadata)
        code = None if result.abstention_code is None else result.abstention_code.value
        sources = tuple(e.source.serialize() for e in result.evidence if e.source is not None)
        step = AuctionStep(len(steps), seat, hand.serialize(), before, result.status,
                           call, code, trace.get("rule"), trace.get("route"), sources)
        if result.status is AnalysisStatus.ABSTAIN:
            return FullAuctionResult(deal_index, dealer, vulnerability, before,
                                     (*steps, step), AuctionOutcome.ABSTAIN, seat, code)
        if result.status is not AnalysisStatus.RECOMMENDATION or call is None:
            error = "production response did not contain a recommended call"
            failed = AuctionStep(step.index, step.seat, step.hand, step.auction_before,
                                 AnalysisStatus.ERROR, call, code, step.rule_id,
                                 step.route_id, step.sources, error)
            return FullAuctionResult(deal_index, dealer, vulnerability, before,
                                     (*steps, failed), AuctionOutcome.ERROR, seat, error=error)
        try:
            auction.add(call)
        except (TypeError, ValueError) as exc:
            error = f"canonical Auction rejected production call {call}: {exc}"
            failed = AuctionStep(step.index, step.seat, step.hand, step.auction_before,
                                 AnalysisStatus.ERROR, call, code, step.rule_id,
                                 step.route_id, step.sources, error)
            return FullAuctionResult(deal_index, dealer, vulnerability, before,
                                     (*steps, failed), AuctionOutcome.ERROR, seat, error=error)
        if len(auction.calls) != len(before) + 1:
            error = "canonical auction did not advance by exactly one call"
            failed = AuctionStep(step.index, step.seat, step.hand, step.auction_before,
                                 AnalysisStatus.ERROR, call, code, step.rule_id,
                                 step.route_id, step.sources, error)
            return FullAuctionResult(deal_index, dealer, vulnerability, before,
                                     (*steps, failed), AuctionOutcome.ERROR, seat, error=error)
        steps.append(step)
    return FullAuctionResult(
        deal_index, dealer, vulnerability,
        tuple(call.serialize() for call in auction.calls), tuple(steps),
        AuctionOutcome.COMPLETE,
    )


def run_full_auction_simulation(
    config: SimulationConfig = SimulationConfig(), *,
    analyzer: Analyzer = analyze_full_deal_application,
) -> FullAuctionBatchResult:
    """Run deterministic full-auction attempts using the Phase 29F cycles."""
    if not isinstance(config, SimulationConfig):
        raise TypeError("config must be SimulationConfig")
    seats, vulnerabilities = tuple(Seat), tuple(Vulnerability)
    auctions = tuple(
        simulate_full_auction(
            deal_index=index, deal=generate_deal(config.seed + index),
            dealer=seats[index % len(seats)],
            vulnerability=vulnerabilities[index % len(vulnerabilities)],
            analyzer=analyzer,
        )
        for index in range(config.deal_count)
    )
    outcomes = Counter(item.outcome for item in auctions)
    stopping = Counter(item.stopping_seat.value for item in auctions if item.outcome is AuctionOutcome.ABSTAIN and item.stopping_seat)
    codes = Counter(item.abstention_code for item in auctions if item.outcome is AuctionOutcome.ABSTAIN and item.abstention_code)
    routes = Counter(step.route_id for item in auctions for step in item.steps if step.status is AnalysisStatus.RECOMMENDATION and step.route_id)
    return FullAuctionBatchResult(
        config.seed, config.deal_count, auctions,
        outcomes[AuctionOutcome.COMPLETE], outcomes[AuctionOutcome.ABSTAIN],
        outcomes[AuctionOutcome.ERROR], sum(len(item.steps) for item in auctions),
        tuple(sorted(stopping.items())), tuple(sorted(codes.items())),
        tuple(sorted(routes.items())),
    )


def run_simulation(
    config: SimulationConfig = SimulationConfig(),
    *,
    analyzer: Analyzer = analyze_full_deal_application,
) -> SimulationResult:
    """Analyze only each dealer's opening hand through the application layer.

    Dealer and vulnerability cycle independently in canonical enum order.
    This is a deterministic simulator policy, not duplicate-board numbering.
    """
    if not isinstance(config, SimulationConfig):
        raise TypeError("config must be SimulationConfig")
    if not callable(analyzer):
        raise TypeError("analyzer must be callable")
    router = create_standard_sayc_router()
    seats = tuple(Seat)
    vulnerabilities = tuple(Vulnerability)
    system = SystemContext("SAYC")
    cases: list[SimulatedDeal] = []
    frequencies: Counter[str] = Counter()
    recommendations = abstains = errors = 0

    for index in range(config.deal_count):
        deal = generate_deal(config.seed + index)
        dealer = seats[index % len(seats)]
        vulnerability = vulnerabilities[index % len(vulnerabilities)]
        hand = deal.hand(dealer)
        context = BiddingContext.create(
            hand=hand,
            auction=Auction(dealer),
            vulnerability=vulnerability,
            system=system,
        )
        response = analyzer(
            FullDealApplicationRequest(requested_stages=("auction",), bidding=context),
            bidding_router=router,
        )
        if response.success and response.canonical_result is not None:
            result = response.canonical_result.subsystem_results[0]
            status = result.status
            call = None if result.action.bid is None else result.action.bid.serialize()
            trace = dict(result.debug_metadata)
            abstention = (
                None if result.abstention_code is None else result.abstention_code.value
            )
            sources = tuple(
                evidence.source.serialize()
                for evidence in result.evidence
                if evidence.source is not None
            )
            error = None
        else:
            status = AnalysisStatus.ERROR
            call = None
            trace = {}
            abstention = None
            sources = ()
            error = "; ".join(item.message for item in response.errors) or response.status

        if status is AnalysisStatus.RECOMMENDATION and call is not None:
            recommendations += 1
            frequencies[call] += 1
        elif status is AnalysisStatus.ABSTAIN:
            abstains += 1
        else:
            errors += 1
            status = AnalysisStatus.ERROR

        cases.append(
            SimulatedDeal(
                index=index,
                dealer=dealer,
                vulnerability=vulnerability,
                analyzed_hand=hand.serialize(),
                status=status,
                recommended_call=call if status is AnalysisStatus.RECOMMENDATION else None,
                abstention_code=abstention,
                rule_id=trace.get("rule"),
                route_id=trace.get("route"),
                sources=sources,
                error=error,
            )
        )

    return SimulationResult(
        seed=config.seed,
        requested_deals=config.deal_count,
        cases=tuple(cases),
        recommendations=recommendations,
        abstains=abstains,
        errors=errors,
        call_frequencies=tuple(sorted(frequencies.items())),
    )
