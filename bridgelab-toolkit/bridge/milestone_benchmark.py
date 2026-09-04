"""Phase 10 deterministic integration-milestone definitions.

This module freezes benchmark *definitions* and aggregation only. It contains
no bidding theory and installs no partnership policy defaults.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

MILESTONE_VERSION="phase10a.v1"
DEFAULT_START_SEED=1
DEFAULT_DEAL_COUNT=100_000

@dataclass(frozen=True,slots=True)
class MilestoneScenario:
    scenario_id:str
    family:str
    description:str
    production_rule_ids:tuple[str,...]=()
    requires_explicit_policy:bool=False

@dataclass(frozen=True,slots=True)
class MilestoneResult:
    scenario_id:str
    deals:int
    positions_reached:int
    production_actions:int
    abstentions:int
    rule_counts:tuple[tuple[str,int],...]

@dataclass(frozen=True,slots=True)
class MilestoneSummary:
    version:str
    start_seed:int
    deal_count:int
    results:tuple[MilestoneResult,...]

    @property
    def total_positions(self)->int:
        return sum(x.positions_reached for x in self.results)

    @property
    def total_actions(self)->int:
        return sum(x.production_actions for x in self.results)

    @property
    def total_abstentions(self)->int:
        return sum(x.abstentions for x in self.results)

SCENARIOS=(
    MilestoneScenario(
        "sayc.uncontested.production",
        "constructive",
        "Production SAYC router on deterministic uncontested deals.",
    ),
    MilestoneScenario(
        "sayc.direct.competition",
        "competitive",
        "Direct competition after scripted one-level suit openings.",
        (
            "sayc.overcall.one_level.natural",
            "sayc.overcall.weak_jump",
            "sayc.double.takeout.direct",
            "sayc.overcall.direct.1nt",
        ),
        True,
    ),
    MilestoneScenario(
        "sayc.takeout.advancer.minimum",
        "competitive",
        "Advancer after scripted 1x-X-P using production router.",
        ("sayc.advancer.takeout.minimum.natural",),
        True,
    ),
    MilestoneScenario(
        "sayc.support_double.example_slice",
        "competitive",
        "Frozen-source Phase 9R Support Double example routes.",
        ("sayc.double.support.example_slice",),
        True,
    ),
)

def validate_milestone_results(results:Iterable[MilestoneResult],*,deal_count:int)->tuple[MilestoneResult,...]:
    frozen=tuple(results)
    if not isinstance(deal_count,int) or isinstance(deal_count,bool) or deal_count<=0:
        raise ValueError("deal_count must be a positive integer")
    ids={s.scenario_id for s in SCENARIOS}
    seen=set()
    for r in frozen:
        if r.scenario_id not in ids:
            raise ValueError(f"unknown milestone scenario: {r.scenario_id}")
        if r.scenario_id in seen:
            raise ValueError(f"duplicate milestone scenario: {r.scenario_id}")
        seen.add(r.scenario_id)
        if r.deals != deal_count:
            raise ValueError("all milestone results must use the frozen deal_count")
        if r.positions_reached < 0 or r.production_actions < 0 or r.abstentions < 0:
            raise ValueError("milestone counts must be non-negative")
        if r.production_actions + r.abstentions > r.positions_reached:
            raise ValueError("actions + abstentions cannot exceed reached positions")
    return frozen

def summarize_milestone(results:Iterable[MilestoneResult],*,start_seed:int=DEFAULT_START_SEED,deal_count:int=DEFAULT_DEAL_COUNT)->MilestoneSummary:
    if not isinstance(start_seed,int) or isinstance(start_seed,bool) or start_seed<0:
        raise ValueError("start_seed must be a non-negative integer")
    frozen=validate_milestone_results(results,deal_count=deal_count)
    return MilestoneSummary(MILESTONE_VERSION,start_seed,deal_count,frozen)
