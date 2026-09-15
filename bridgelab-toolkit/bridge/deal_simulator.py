"""Deterministic deal batches with one production opening analysis per deal."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable

from .auction import Auction
from .bidding_rules import BiddingContext, SystemContext
from .deal_analysis import AnalysisStatus
from .deals import generate_deal
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


Analyzer = Callable[..., FullDealApplicationResponse]


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
