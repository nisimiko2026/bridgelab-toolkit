"""Controlled multi-seat auction simulation.

This module contains no bridge theory.  It composes existing source-grounded
``BiddingEngine`` instances and stops explicitly when BridgeLab lacks a
recommendation.

The simulator never guesses a call and never treats Pass as an implicit
fallback.  A pass must come from a registered bidding rule just like any other
call.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .auction import Auction, Call
from .bidding_engine import BiddingEngineResult
from .engine_router import RecommendationEngine
from .bidding_rules import BiddingContext, KnowledgeSource, SystemContext
from .models import Hand, Seat, Vulnerability


class SimulationStopReason(Enum):
    AUCTION_COMPLETE = "auction-complete"
    NO_RECOMMENDATION = "no-recommendation"
    MAX_STEPS = "max-steps"


@dataclass(frozen=True, slots=True)
class SimulationStep:
    number: int
    seat: Seat
    auction_before: str
    call: Call
    rule_id: str
    explanation: str
    sources: tuple[KnowledgeSource, ...]
    alternatives: tuple[Call, ...]


@dataclass(frozen=True, slots=True)
class AuctionSimulationResult:
    dealer: Seat
    initial_auction: str
    final_auction: str
    steps: tuple[SimulationStep, ...]
    stop_reason: SimulationStopReason
    stopped_seat: Seat | None
    complete: bool

    @property
    def calls_added(self) -> tuple[Call, ...]:
        return tuple(step.call for step in self.steps)


class ControlledAuctionSimulator:
    """Run existing bidding engines one legal recommendation at a time."""

    def __init__(
        self,
        *,
        hands: Mapping[Seat, Hand],
        engines: Mapping[Seat, RecommendationEngine],
        systems: Mapping[Seat, SystemContext],
        vulnerability: Vulnerability = Vulnerability.NONE,
    ) -> None:
        if set(hands) != set(Seat):
            raise ValueError("hands must contain exactly N, E, S, W")
        if set(engines) != set(Seat):
            raise ValueError("engines must contain exactly N, E, S, W")
        if set(systems) != set(Seat):
            raise ValueError("systems must contain exactly N, E, S, W")
        if not all(isinstance(hand, Hand) for hand in hands.values()):
            raise TypeError("all hands must be Hand")
        if not all(isinstance(engine, RecommendationEngine) for engine in engines.values()):
            raise TypeError("all engines must satisfy RecommendationEngine")
        if not all(isinstance(system, SystemContext) for system in systems.values()):
            raise TypeError("all systems must be SystemContext")
        if not isinstance(vulnerability, Vulnerability):
            raise TypeError("vulnerability must be Vulnerability")

        # Duplicate cards make a simulated deal physically impossible.
        all_cards = [card for hand in hands.values() for card in hand.cards]
        if len(set(all_cards)) != 52:
            raise ValueError("hands must form one complete 52-card deal without duplicates")

        self._hands = dict(hands)
        self._engines = dict(engines)
        self._systems = dict(systems)
        self._vulnerability = vulnerability

    def simulate(self, auction: Auction, *, max_steps: int = 64) -> AuctionSimulationResult:
        if not isinstance(auction, Auction):
            raise TypeError("auction must be Auction")
        if not isinstance(max_steps, int) or isinstance(max_steps, bool):
            raise TypeError("max_steps must be an integer")
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")

        initial = auction.serialize()
        steps: list[SimulationStep] = []

        while not auction.is_complete and len(steps) < max_steps:
            seat = auction.next_seat
            context = BiddingContext.create(
                hand=self._hands[seat],
                auction=auction,
                vulnerability=self._vulnerability,
                system=self._systems[seat],
            )
            result: BiddingEngineResult = self._engines[seat].evaluate(context)

            if not result.has_recommendation:
                return AuctionSimulationResult(
                    dealer=auction.dealer,
                    initial_auction=initial,
                    final_auction=auction.serialize(),
                    steps=tuple(steps),
                    stop_reason=SimulationStopReason.NO_RECOMMENDATION,
                    stopped_seat=seat,
                    complete=False,
                )

            decision = result.recommended
            assert decision is not None and decision.candidate is not None
            call = decision.candidate

            # RuleDecision already validates legality, but retain the invariant
            # at the composition boundary before mutating the auction.
            if not auction.is_legal(call):
                raise ValueError(
                    f"engine recommendation {call.serialize()} is illegal for {seat.value}"
                )

            before = auction.serialize()
            auction.add(call)
            steps.append(
                SimulationStep(
                    number=len(steps) + 1,
                    seat=seat,
                    auction_before=before,
                    call=call,
                    rule_id=decision.rule_id,
                    explanation=decision.explanation,
                    sources=decision.sources,
                    alternatives=tuple(
                        alt.candidate
                        for alt in result.alternatives
                        if alt.candidate is not None
                    ),
                )
            )

        if auction.is_complete:
            return AuctionSimulationResult(
                dealer=auction.dealer,
                initial_auction=initial,
                final_auction=auction.serialize(),
                steps=tuple(steps),
                stop_reason=SimulationStopReason.AUCTION_COMPLETE,
                stopped_seat=None,
                complete=True,
            )

        return AuctionSimulationResult(
            dealer=auction.dealer,
            initial_auction=initial,
            final_auction=auction.serialize(),
            steps=tuple(steps),
            stop_reason=SimulationStopReason.MAX_STEPS,
            stopped_seat=auction.next_seat,
            complete=False,
        )
