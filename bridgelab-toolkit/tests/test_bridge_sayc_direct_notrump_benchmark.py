import pytest
from bridge import (
    KnowledgeSource, PolicyRegistry, StopperAssessment,
    run_sayc_direct_one_notrump_benchmark,
)
from bridge.policy_registry import STOPPER_POLICY_OPTION

SRC=(KnowledgeSource("bidding/systems/sayc","Notrump Overcalls — Direct 1NT"),)

class AlwaysStopped:
    policy_id="benchmark.stopper.always-stopped"
    def assess(self, context, suit):
        return StopperAssessment.stopped(
            policy_id=self.policy_id,
            evidence=context.evaluation.honor_evidence(suit),
            explanation="Benchmark-only all-stopped fixture.",
            sources=SRC,
        )

def setup():
    reg=PolicyRegistry.from_stopper_policies([AlwaysStopped()])
    opts={STOPPER_POLICY_OPTION:"benchmark.stopper.always-stopped"}
    return reg,opts

@pytest.mark.parametrize("opening",["1C","1D","1H","1S"])
def test_all_stopped_fixture_actions_equal_objective_gate(opening):
    reg,opts=setup()
    r=run_sayc_direct_one_notrump_benchmark(
        count=100, opening=opening, registry=reg, system_options=opts
    )
    assert r.metrics.direct_positions_reached==100
    assert r.metrics.one_notrump_actions==r.metrics.hcp_15_18_balanced

def test_no_stopper_policy_produces_no_direct_1nt():
    r=run_sayc_direct_one_notrump_benchmark(count=100,opening="1H")
    assert r.metrics.one_notrump_actions==0

def test_deterministic():
    reg,opts=setup()
    a=run_sayc_direct_one_notrump_benchmark(
        count=100,opening="1D",registry=reg,system_options=opts
    )
    b=run_sayc_direct_one_notrump_benchmark(
        count=100,opening="1D",registry=reg,system_options=opts
    )
    assert a.metrics==b.metrics
    assert a.batch.replay_records==b.batch.replay_records

def test_invalid_opening():
    with pytest.raises(ValueError):
        run_sayc_direct_one_notrump_benchmark(count=1,opening="1NT")
