"""Offline deterministic batch runner for controlled auction simulation.

The runner orchestrates existing components only.  It does not create bidding
decisions, auto-pass opponents, or reinterpret abstentions as errors.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Mapping

from .auction import Auction
from .auction_simulation import AuctionSimulationResult, ControlledAuctionSimulator
from .bidding_rules import SystemContext
from .deals import Deal, generate_deals
from .engine_router import RecommendationEngine
from .models import Seat, Vulnerability
from .simulation_statistics import SimulationStatistics, summarize_simulations


EngineFactory=Callable[[Deal], Mapping[Seat, RecommendationEngine]]
SystemFactory=Callable[[Deal], Mapping[Seat, SystemContext]]


@dataclass(frozen=True, slots=True)
class BatchSimulationCase:
    deal: Deal
    result: AuctionSimulationResult


@dataclass(frozen=True, slots=True)
class BatchSimulationReport:
    start_seed: int
    count: int
    dealer: Seat
    vulnerability: Vulnerability
    cases: tuple[BatchSimulationCase, ...]
    statistics: SimulationStatistics

    @property
    def replay_records(self) -> tuple[tuple[int,str], ...]:
        return tuple((case.deal.seed,case.deal.serialize()) for case in self.cases)


def run_seeded_batch(
    *,
    start_seed: int,
    count: int,
    engine_factory: EngineFactory,
    system_factory: SystemFactory,
    dealer: Seat = Seat.NORTH,
    vulnerability: Vulnerability = Vulnerability.NONE,
    max_steps: int = 64,
) -> BatchSimulationReport:
    if not callable(engine_factory):
        raise TypeError("engine_factory must be callable")
    if not callable(system_factory):
        raise TypeError("system_factory must be callable")
    if not isinstance(dealer,Seat):
        raise TypeError("dealer must be Seat")
    if not isinstance(vulnerability,Vulnerability):
        raise TypeError("vulnerability must be Vulnerability")
    if not isinstance(max_steps,int) or isinstance(max_steps,bool) or max_steps <= 0:
        raise ValueError("max_steps must be a positive integer")

    cases=[]
    for deal in generate_deals(start_seed=start_seed,count=count):
        engines=dict(engine_factory(deal))
        systems=dict(system_factory(deal))
        simulator=ControlledAuctionSimulator(
            hands=deal.mapping,engines=engines,systems=systems,
            vulnerability=vulnerability,
        )
        result=simulator.simulate(Auction(dealer),max_steps=max_steps)
        cases.append(BatchSimulationCase(deal,result))

    frozen=tuple(cases)
    return BatchSimulationReport(
        start_seed=start_seed,count=count,dealer=dealer,vulnerability=vulnerability,
        cases=frozen,statistics=summarize_simulations(case.result for case in frozen),
    )
