"""Deterministic coverage benchmark for the current production SAYC router.

East/West use an explicit passive benchmark engine that recommends Pass.
Those calls are fixture behavior, not production SAYC coverage and are labeled
separately in the report. North/South use only the production standard router.

No suit-quality policy is installed by default, so policy-gated 2/1 responses
remain abstentions in the baseline benchmark.
"""

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass

from .auction import Call
from .batch_simulation import BatchSimulationReport, run_seeded_batch
from .bidding_engine import BiddingEngine
from .bidding_rules import KnowledgeSource, RuleDecision, SystemContext
from .models import Seat
from .sayc_route_configuration import create_standard_sayc_router


_FIXTURE_SOURCE=KnowledgeSource("bidding/systems/sayc","Opening Bid Requirements")


@dataclass(frozen=True,slots=True)
class _PassivePassRule:
    rule_id:str
    def evaluate(self,context):
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.pass_(),
            explanation="Explicit passive-opponent benchmark fixture; not production SAYC coverage.",
            sources=(_FIXTURE_SOURCE,),priority=1,
        )


@dataclass(frozen=True,slots=True)
class SaycCoverageMetrics:
    runs:int
    production_calls:int
    fixture_calls:int
    opened:int
    responder_reached:int
    responder_bid:int
    opener_rebid:int
    completed:int
    abstained:int
    depth_counts:tuple[tuple[int,int],...]
    production_rule_counts:tuple[tuple[str,int],...]

    @property
    def opening_rate(self)->float:
        return 0.0 if self.runs==0 else self.opened/self.runs
    @property
    def responder_bid_rate(self)->float:
        return 0.0 if self.runs==0 else self.responder_bid/self.runs
    @property
    def opener_rebid_rate(self)->float:
        return 0.0 if self.runs==0 else self.opener_rebid/self.runs


@dataclass(frozen=True,slots=True)
class SaycCoverageBenchmarkReport:
    batch:BatchSimulationReport
    metrics:SaycCoverageMetrics


def _engines(deal):
    router=create_standard_sayc_router()
    return {
        Seat.NORTH:router,
        Seat.EAST:BiddingEngine((_PassivePassRule("benchmark.fixture.pass.east"),)),
        Seat.SOUTH:router,
        Seat.WEST:BiddingEngine((_PassivePassRule("benchmark.fixture.pass.west"),)),
    }


def _systems(deal):
    return {seat:SystemContext("SAYC") for seat in Seat}


def run_sayc_coverage_benchmark(*,start_seed:int=1,count:int=1000)->SaycCoverageBenchmarkReport:
    batch=run_seeded_batch(
        start_seed=start_seed,count=count,engine_factory=_engines,system_factory=_systems
    )
    prod=Counter()
    depths=Counter()
    production_calls=fixture_calls=opened=responder_reached=responder_bid=opener_rebid=0
    for case in batch.cases:
        steps=case.result.steps
        depths[len(steps)]+=1
        for step in steps:
            if step.rule_id.startswith("benchmark.fixture."):
                fixture_calls+=1
            else:
                production_calls+=1
                prod[step.rule_id]+=1
        if steps and not steps[0].rule_id.startswith("benchmark.fixture."):
            opened+=1
        # With North dealer and passive East, South is reached after N opening + E pass.
        if len(steps)>=2 and steps[0].rule_id.startswith("sayc.opening.") and steps[1].rule_id=="benchmark.fixture.pass.east":
            responder_reached+=1
        if len(steps)>=3 and steps[2].rule_id.startswith("sayc."):
            responder_bid+=1
        if len(steps)>=5 and steps[4].rule_id.startswith("sayc.2over1.opener."):
            opener_rebid+=1

    metrics=SaycCoverageMetrics(
        runs=count,production_calls=production_calls,fixture_calls=fixture_calls,
        opened=opened,responder_reached=responder_reached,responder_bid=responder_bid,
        opener_rebid=opener_rebid,completed=batch.statistics.completed,
        abstained=batch.statistics.abstained,depth_counts=tuple(sorted(depths.items())),
        production_rule_counts=tuple(sorted(prod.items())),
    )
    return SaycCoverageBenchmarkReport(batch,metrics)
