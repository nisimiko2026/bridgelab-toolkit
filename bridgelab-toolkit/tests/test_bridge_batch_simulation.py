from dataclasses import dataclass
from bridge import (
    BiddingEngine, Call, KnowledgeSource, RuleDecision, Seat,
    SimulationStopReason, SystemContext, run_seeded_batch,
)


SRC=KnowledgeSource("bidding/systems/sayc","Opening Bid Requirements")


@dataclass(frozen=True)
class PassRule:
    rule_id:str
    def evaluate(self,context):
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.pass_(),
            explanation="explicit batch fixture pass",sources=(SRC,),priority=1,
        )


def all_pass_engines(deal):
    return {seat:BiddingEngine((PassRule(f"fixture.pass.{seat.value}"),)) for seat in Seat}


def all_sayc_systems(deal):
    return {seat:SystemContext("SAYC") for seat in Seat}


def abstain_engines(deal):
    return {seat:BiddingEngine(()) for seat in Seat}


def test_seeded_batch_is_reproducible():
    a=run_seeded_batch(start_seed=100,count=5,engine_factory=all_pass_engines,system_factory=all_sayc_systems)
    b=run_seeded_batch(start_seed=100,count=5,engine_factory=all_pass_engines,system_factory=all_sayc_systems)
    assert a.replay_records==b.replay_records
    assert a.statistics==b.statistics


def test_explicit_pass_engines_complete_every_passed_out_deal():
    report=run_seeded_batch(start_seed=1,count=7,engine_factory=all_pass_engines,system_factory=all_sayc_systems)
    assert report.statistics.runs==7
    assert report.statistics.completed==7
    assert report.statistics.abstained==0
    assert all(case.result.final_auction=="P P P P" for case in report.cases)


def test_empty_engines_abstain_immediately_without_implicit_pass():
    report=run_seeded_batch(start_seed=1,count=4,engine_factory=abstain_engines,system_factory=all_sayc_systems)
    assert report.statistics.abstained==4
    assert report.statistics.completed==0
    assert report.statistics.total_calls_added==0
    assert all(case.result.stop_reason is SimulationStopReason.NO_RECOMMENDATION for case in report.cases)
    assert all(case.result.stopped_seat is Seat.NORTH for case in report.cases)


def test_replay_records_include_seed_and_canonical_deal():
    report=run_seeded_batch(start_seed=55,count=2,engine_factory=abstain_engines,system_factory=all_sayc_systems)
    assert [seed for seed,_ in report.replay_records]==[55,56]
    assert all(text.count("|")==3 for _,text in report.replay_records)


def test_zero_count_produces_empty_statistics():
    report=run_seeded_batch(start_seed=5,count=0,engine_factory=abstain_engines,system_factory=all_sayc_systems)
    assert report.cases==()
    assert report.statistics.runs==0


def test_invalid_max_steps_rejected():
    try:
        run_seeded_batch(start_seed=1,count=1,engine_factory=abstain_engines,system_factory=all_sayc_systems,max_steps=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
