"""Phase 10B runner for the frozen Phase 10A milestone scenarios.

This runner composes existing benchmark functions. Benchmark-only policy
fixtures are explicit and never become production defaults.
"""
from __future__ import annotations
from dataclasses import dataclass

from .bidding_rules import KnowledgeSource
from .milestone_benchmark import MilestoneResult, MilestoneSummary, summarize_milestone
from .policy_registry import (
    PolicyRegistry, STOPPER_POLICY_OPTION,
    SUIT_QUALITY_POLICY_OPTION, PLAYING_STRENGTH_POLICY_OPTION,
    OFFENSIVE_HAND_POLICY_OPTION, OPPONENT_SUIT_SHORTNESS_POLICY_OPTION,
    TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION,
    SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION,
)
from .sayc_coverage_benchmark import run_sayc_coverage_benchmark
from .sayc_competitive_benchmark import (
    run_sayc_direct_overcall_benchmark,
    run_sayc_takeout_advancer_benchmark,
    run_sayc_support_double_benchmark,
)
from .stopper_policy import StopperAssessment
from .suit_quality_policy import SuitQualityAssessment
from .playing_strength_policy import PlayingStrengthAssessment
from .offensive_hand_policy import OffensiveHandAssessment
from .opponent_suit_shortness_policy import (
    OpponentSuitShortnessAssessment, OpponentSuitShortnessStatus,
)
from .takeout_advancer_strength_policy import (
    TakeoutAdvancerStrengthAssessment, TakeoutAdvancerStrengthClass,
)
from .support_double_eligibility_policy import (
    SupportDoubleEligibilityAssessment, SupportDoubleEligibilityStatus,
)

_SRC=KnowledgeSource("benchmark/phase10","Explicit benchmark-only policy fixture")

class _Stopped:
    policy_id="benchmark.phase10.always-stopped"
    def assess(self,context,suit):
        return StopperAssessment.stopped(
            policy_id=self.policy_id,evidence=context.evaluation.honor_evidence(suit),
            explanation="Phase 10 benchmark-only all-stopped fixture.",sources=(_SRC,),
        )


class _SuitQualifies:
    policy_id="benchmark.phase10.suit-qualifies"
    def assess(self,context,suit):
        return SuitQualityAssessment.qualifies(
            self.policy_id,suit,context.evaluation.quality_evidence(suit),
            "Phase 10 benchmark-only suit-quality qualification.",(_SRC,),
        )

class _PlayingStrengthQualifies:
    policy_id="benchmark.phase10.playing-strength-qualifies"
    def assess(self,context):
        return PlayingStrengthAssessment.qualifies(
            self.policy_id,
            "Phase 10 benchmark-only playing-strength qualification.",(_SRC,),
        )

class _OffensiveQualifies:
    policy_id="benchmark.phase10.offensive-qualifies"
    def assess(self,context):
        return OffensiveHandAssessment.qualifies(
            self.policy_id,
            "Phase 10 benchmark-only offensive-hand qualification.",(_SRC,),
        )

class _ShortnessQualifies:
    policy_id="benchmark.phase10.shortness-qualifies"
    def assess(self,context,opponent_suit,suit_length):
        return OpponentSuitShortnessAssessment(
            self.policy_id,OpponentSuitShortnessStatus.QUALIFIES,
            opponent_suit,suit_length,
            "Phase 10 benchmark-only opponent-suit-shortness qualification.",(_SRC,),
        )

class _Minimum:
    policy_id="benchmark.phase10.minimum"
    def assess(self,context):
        return TakeoutAdvancerStrengthAssessment(
            self.policy_id,TakeoutAdvancerStrengthClass.MINIMUM,
            "Phase 10 benchmark-only all-minimum fixture.",(_SRC,),
        )

class _SupportQualifies:
    policy_id="benchmark.phase10.support-qualifies"
    def assess(self,context):
        return SupportDoubleEligibilityAssessment(
            self.policy_id,SupportDoubleEligibilityStatus.QUALIFIES,
            "Phase 10 benchmark-only Support Double eligibility fixture.",(_SRC,),
        )

def _registry():
    return PolicyRegistry.from_policies(
        stopper_policies=(_Stopped(),),
        suit_quality_policies=(_SuitQualifies(),),
        playing_strength_policies=(_PlayingStrengthQualifies(),),
        offensive_hand_policies=(_OffensiveQualifies(),),
        opponent_suit_shortness_policies=(_ShortnessQualifies(),),
        takeout_advancer_strength_policies=(_Minimum(),),
        support_double_eligibility_policies=(_SupportQualifies(),),
    )

def run_phase10_milestone(*,start_seed:int=1,count:int=1000)->MilestoneSummary:
    """Run all frozen scenario families with `count` deals per sub-route.

    Phase 10B validation can use small counts. The Phase 10 milestone run uses
    count=100_000. Each competitive family aggregates its frozen sub-routes.
    """
    if not isinstance(count,int) or isinstance(count,bool) or count<=0:
        raise ValueError("count must be a positive integer")
    reg=_registry()

    cov=run_sayc_coverage_benchmark(start_seed=start_seed,count=count)
    cm=cov.metrics
    constructive=MilestoneResult(
        "sayc.uncontested.production",count,cm.production_calls+cm.abstained,
        cm.production_calls,cm.abstained,cm.production_rule_counts,
    )

    direct_actions=direct_abst=direct_reached=0
    direct_rules={}
    # Explicit benchmark-only fixtures qualify every qualitative gate used by
    # the four frozen direct competitive capabilities. These are measurement
    # fixtures only; they are never production defaults.
    direct_opts={
        STOPPER_POLICY_OPTION:_Stopped.policy_id,
        SUIT_QUALITY_POLICY_OPTION:_SuitQualifies.policy_id,
        PLAYING_STRENGTH_POLICY_OPTION:_PlayingStrengthQualifies.policy_id,
        OFFENSIVE_HAND_POLICY_OPTION:_OffensiveQualifies.policy_id,
        OPPONENT_SUIT_SHORTNESS_POLICY_OPTION:_ShortnessQualifies.policy_id,
    }
    for opening in ("1C","1D","1H","1S"):
        r=run_sayc_direct_overcall_benchmark(
            start_seed=start_seed,count=count,opening=opening,
            registry=reg,system_options=direct_opts,
        ).metrics
        direct_reached+=r.direct_positions_reached
        direct_actions+=r.direct_actions
        direct_abst+=r.direct_abstentions
        for rid,n in r.production_rule_counts:
            direct_rules[rid]=direct_rules.get(rid,0)+n
    direct=MilestoneResult(
        "sayc.direct.competition",count,direct_reached,direct_actions,direct_abst,
        tuple(sorted(direct_rules.items())),
    )

    adv_actions=adv_abst=adv_reached=0; adv_rules={}
    adv_opts={TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION:_Minimum.policy_id}
    for opening in ("1C","1D","1H","1S"):
        r=run_sayc_takeout_advancer_benchmark(
            start_seed=start_seed,count=count,opening=opening,
            registry=reg,system_options=adv_opts,
        ).metrics
        adv_reached+=r.advancer_positions_reached
        adv_actions+=r.advancer_actions
        adv_abst+=r.advancer_abstentions
        for rid,n in r.production_rule_counts:
            adv_rules[rid]=adv_rules.get(rid,0)+n
    adv=MilestoneResult(
        "sayc.takeout.advancer.minimum",count,adv_reached,adv_actions,adv_abst,
        tuple(sorted(adv_rules.items())),
    )

    sup_actions=sup_abst=sup_reached=0; sup_rules={}
    sup_opts={SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION:_SupportQualifies.policy_id}
    for route in ("1D-P-1H-1S","1C-P-1H-1S","1D-P-1S-2C","1H-P-1S-2D"):
        r=run_sayc_support_double_benchmark(
            start_seed=start_seed,count=count,route=route,
            registry=reg,system_options=sup_opts,
        ).metrics
        sup_reached+=r.positions_reached
        sup_actions+=r.support_double_actions
        sup_abst+=r.abstentions
        for rid,n in r.production_rule_counts:
            sup_rules[rid]=sup_rules.get(rid,0)+n
    support=MilestoneResult(
        "sayc.support_double.example_slice",count,sup_reached,sup_actions,sup_abst,
        tuple(sorted(sup_rules.items())),
    )

    return summarize_milestone(
        (constructive,direct,adv,support),start_seed=start_seed,deal_count=count
    )


def merge_phase10_chunks(
    chunks: tuple[MilestoneSummary, ...],
    *,
    start_seed: int,
    total_count: int,
) -> MilestoneSummary:
    """Exactly aggregate contiguous Phase 10 chunk summaries."""
    if not chunks:
        raise ValueError("chunks must not be empty")
    if total_count <= 0:
        raise ValueError("total_count must be positive")
    expected_seed=start_seed
    accumulated=0
    scenario_ids=tuple(x.scenario_id for x in chunks[0].results)
    positions={x:0 for x in scenario_ids}
    actions={x:0 for x in scenario_ids}
    abstentions={x:0 for x in scenario_ids}
    rules={x:{} for x in scenario_ids}
    for chunk in chunks:
        if chunk.version != chunks[0].version:
            raise ValueError("chunk milestone versions differ")
        if chunk.start_seed != expected_seed:
            raise ValueError("chunks must cover contiguous seed ranges in order")
        ids=tuple(x.scenario_id for x in chunk.results)
        if ids != scenario_ids:
            raise ValueError("chunk scenario ordering differs")
        expected_seed += chunk.deal_count
        accumulated += chunk.deal_count
        for r in chunk.results:
            positions[r.scenario_id]+=r.positions_reached
            actions[r.scenario_id]+=r.production_actions
            abstentions[r.scenario_id]+=r.abstentions
            for rid,n in r.rule_counts:
                d=rules[r.scenario_id]
                d[rid]=d.get(rid,0)+n
    if accumulated != total_count:
        raise ValueError("chunk deal counts do not equal total_count")
    merged=tuple(
        MilestoneResult(
            sid,total_count,positions[sid],actions[sid],abstentions[sid],
            tuple(sorted(rules[sid].items())),
        )
        for sid in scenario_ids
    )
    return summarize_milestone(merged,start_seed=start_seed,deal_count=total_count)


def run_phase10_milestone_chunked(
    *,
    start_seed: int=1,
    count: int=100_000,
    chunk_size: int=1_000,
) -> MilestoneSummary:
    """Run the exact deterministic seed interval in bounded-memory chunks."""
    if not isinstance(chunk_size,int) or isinstance(chunk_size,bool) or chunk_size<=0:
        raise ValueError("chunk_size must be a positive integer")
    if not isinstance(count,int) or isinstance(count,bool) or count<=0:
        raise ValueError("count must be a positive integer")
    chunks=[]
    offset=0
    while offset<count:
        n=min(chunk_size,count-offset)
        chunks.append(run_phase10_milestone(start_seed=start_seed+offset,count=n))
        offset+=n
    return merge_phase10_chunks(tuple(chunks),start_seed=start_seed,total_count=count)
