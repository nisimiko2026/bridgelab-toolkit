"""A8.9 end-to-end benchmark pipeline integration tests."""
import pytest
from bridge.benchmark_batch import BenchmarkBatch
from bridge.benchmark_case_identity import BenchmarkCaseIdentity
from bridge.benchmark_gap_discovery import GapCategory
from bridge.benchmark_manifest import BenchmarkManifest,BenchmarkProfileIdentity,DatasetIdentity,DatasetKind
from bridge.benchmark_pipeline import BenchmarkPipelineResult,run_benchmark_pipeline
from bridge.benchmark_runner import BenchmarkExecutionStatus
from bridge.decision_case import DecisionCase
from bridge.decision_evidence import Disagreement,DisagreementKind
from bridge.deals import generate_deal

def _batch(count=5):
    seeds=tuple(range(1,count+1))
    dataset=DatasetIdentity("a89","1",DatasetKind.SYNTHETIC,"generator",record_count=count)
    manifest=BenchmarkManifest("a89-integration","1",dataset,BenchmarkProfileIdentity("test-system","1"),seeds=seeds)
    cases=tuple(BenchmarkCaseIdentity.for_synthetic(f"case-{n}",dataset,seed=n,deal=generate_deal(n)) for n in seeds)
    return BenchmarkBatch(manifest,cases)

def _case(identity,kind=None):
    disagreements=() if kind is None else (Disagreement(kind,"bridgelab","external","fixture"),)
    return DecisionCase(case_id=identity.case_id,disagreements=disagreements)

def test_pipeline_runs_every_case_once_in_order():
    seen=[]
    p=run_benchmark_pipeline(_batch(5),lambda i:(seen.append(i.case_id),_case(i))[1])
    assert seen==[f"case-{n}" for n in range(1,6)]
    assert tuple(x.identity.case_id for x in p.records)==tuple(seen)

def test_pipeline_preserves_replay_identity_end_to_end():
    p=run_benchmark_pipeline(_batch(3),lambda i:_case(i,DisagreementKind.JUDGMENT_DIFFERENCE))
    assert tuple(x.replay_key for x in p.gaps.items)==("a89@1:seed:1","a89@1:seed:2","a89@1:seed:3")
    assert p.aggregation.groups[0].replay_keys==("a89@1:seed:1","a89@1:seed:2","a89@1:seed:3")

def test_pipeline_statistics_match_batch_size():
    p=run_benchmark_pipeline(_batch(20),lambda i:_case(i))
    assert p.statistics.total==20
    assert p.statistics.completed==20
    assert p.statistics.failed==0

def test_pipeline_failure_is_isolated_and_aggregated():
    def execute(i):
        if i.case_id=="case-2": raise RuntimeError("fixture failure")
        return _case(i)
    p=run_benchmark_pipeline(_batch(4),execute)
    assert (p.statistics.completed,p.statistics.failed)==(3,1)
    assert p.aggregation.count(GapCategory.EXECUTION_FAILURE)==1
    assert p.aggregation.groups[0].case_ids==("case-2",)

def test_pipeline_agreement_does_not_become_gap():
    p=run_benchmark_pipeline(_batch(2),lambda i:_case(i,DisagreementKind.AGREEMENT))
    assert p.gaps.items==() and p.aggregation.total_items==0

def test_pipeline_policy_gap_remains_review_candidate_not_failure():
    p=run_benchmark_pipeline(_batch(3),lambda i:_case(i,DisagreementKind.POSSIBLE_POLICY_GAP))
    assert p.statistics.failed==0
    assert p.aggregation.count(GapCategory.POLICY_GAP)==3
    assert p.aggregation.review_candidate_count==3

def test_pipeline_system_difference_is_not_policy_gap():
    p=run_benchmark_pipeline(_batch(3),lambda i:_case(i,DisagreementKind.SYSTEM_DIFFERENCE))
    assert p.aggregation.count(GapCategory.SYSTEM_DIFFERENCE)==3
    assert p.aggregation.review_candidate_count==0

def test_pipeline_mixed_classifications_survive():
    kinds={1:DisagreementKind.POSSIBLE_ENGINE_DEFECT,2:DisagreementKind.JUDGMENT_DIFFERENCE,3:DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM}
    p=run_benchmark_pipeline(_batch(3),lambda i:_case(i,kinds[int(i.case_id.split("-")[1])]))
    assert p.aggregation.count(GapCategory.ENGINE_DEFECT)==1
    assert p.aggregation.count(GapCategory.JUDGMENT_DIFFERENCE)==1
    assert p.aggregation.count(GapCategory.UNKNOWN_EXTERNAL_SYSTEM)==1

def test_pipeline_is_deterministic_for_same_batch_and_executor():
    batch=_batch(25)
    a=run_benchmark_pipeline(batch,lambda i:_case(i,DisagreementKind.JUDGMENT_DIFFERENCE))
    b=run_benchmark_pipeline(batch,lambda i:_case(i,DisagreementKind.JUDGMENT_DIFFERENCE))
    assert a.records==b.records
    assert a.statistics==b.statistics
    assert a.gaps==b.gaps
    assert a.aggregation==b.aggregation

def test_pipeline_handles_controlled_1000_case_batch():
    batch=_batch(1000)
    p=run_benchmark_pipeline(batch,lambda i:_case(i,DisagreementKind.JUDGMENT_DIFFERENCE))
    assert p.statistics.total==1000
    assert p.statistics.completed==1000
    assert p.aggregation.count(GapCategory.JUDGMENT_DIFFERENCE)==1000
    assert len(p.aggregation.groups[0].replay_keys)==1000

def test_empty_batch_runs_end_to_end():
    p=run_benchmark_pipeline(_batch(0),lambda i:_case(i))
    assert p.statistics.total==0 and p.records==() and p.gaps.items==() and p.aggregation.groups==()

def test_pipeline_rejects_invalid_batch_through_runner():
    with pytest.raises(TypeError): run_benchmark_pipeline("bad",lambda i:i)

def test_pipeline_rejects_non_callable_executor_through_runner():
    with pytest.raises(TypeError): run_benchmark_pipeline(_batch(1),None)

def test_pipeline_result_validates_record_count():
    p=run_benchmark_pipeline(_batch(1),lambda i:_case(i))
    with pytest.raises(ValueError,match="record count"):
        BenchmarkPipelineResult(p.run,(),p.statistics,p.gaps,p.aggregation)

def test_pipeline_result_validates_identity_order():
    p=run_benchmark_pipeline(_batch(2),lambda i:_case(i))
    with pytest.raises(ValueError,match="identities"):
        BenchmarkPipelineResult(p.run,tuple(reversed(p.records)),p.statistics,p.gaps,p.aggregation)

def test_pipeline_result_is_immutable():
    p=run_benchmark_pipeline(_batch(0),lambda i:_case(i))
    with pytest.raises(AttributeError): p.records=()

def test_pipeline_has_no_rank_winner_score_or_policy_override_surface():
    p=run_benchmark_pipeline(_batch(0),lambda i:_case(i))
    for name in ("rank","ranking","winner","score","selected","preferred","override","correct","accuracy"):
        assert not hasattr(p,name)
