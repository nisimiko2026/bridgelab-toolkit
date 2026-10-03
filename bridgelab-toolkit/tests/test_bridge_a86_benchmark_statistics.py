"""A8.6 benchmark aggregation tests."""
import pytest
from bridge.benchmark_case_identity import BenchmarkCaseIdentity
from bridge.benchmark_manifest import DatasetIdentity,DatasetKind
from bridge.benchmark_result_record import BenchmarkProviderRecord,BenchmarkResultRecord
from bridge.benchmark_runner import BenchmarkExecutionStatus
from bridge.benchmark_statistics import BenchmarkStatistics,ProviderStatusCount,summarize_benchmark_records
from bridge.capability_providers import ProviderStatus
from bridge.decision_evidence import DisagreementKind
from bridge.deals import generate_deal

def _id(n):
    d=DatasetIdentity("a8","1",DatasetKind.SYNTHETIC,"generator")
    return BenchmarkCaseIdentity.for_synthetic(f"c{n}",d,seed=n,deal=generate_deal(n))

def _provider(name,status,recommendation=False):
    return BenchmarkProviderRecord(name,status,recommendation)

def _record(n,bridge=None,external=(),disagreements=()):
    return BenchmarkResultRecord(_id(n),BenchmarkExecutionStatus.COMPLETED,bridgelab=bridge,external=external,disagreements=disagreements)

def test_empty_statistics_are_zero():
    s=summarize_benchmark_records(())
    assert s.total==s.completed==s.failed==0
    assert s.execution_success_rate==s.bridgelab_coverage_rate==s.bridgelab_abstention_rate==0.0

def test_execution_counts_completed_and_failed():
    records=(
        _record(1),
        BenchmarkResultRecord(_id(2),BenchmarkExecutionStatus.FAILED,error_type="RuntimeError",error_message="boom"),
    )
    s=summarize_benchmark_records(records)
    assert (s.total,s.completed,s.failed)==(2,1,1)
    assert s.execution_success_rate==0.5

def test_bridge_recommendation_and_abstention_are_separate():
    s=summarize_benchmark_records((
        _record(1,_provider("bridgelab",ProviderStatus.SUCCESS,True)),
        _record(2,_provider("bridgelab",ProviderStatus.ABSTAIN,False)),
    ))
    assert (s.bridgelab_observed,s.bridgelab_recommended,s.bridgelab_abstained,s.bridgelab_other_status)==(2,1,1,0)
    assert s.bridgelab_coverage_rate==0.5 and s.bridgelab_abstention_rate==0.5

def test_bridge_unavailable_is_other_not_abstention():
    s=summarize_benchmark_records((_record(1,_provider("bridgelab",ProviderStatus.UNAVAILABLE,False)),))
    assert s.bridgelab_other_status==1 and s.bridgelab_abstained==0

def test_completed_opaque_payload_does_not_fake_bridge_observation():
    s=summarize_benchmark_records((_record(1),))
    assert s.bridgelab_observed==0

def test_external_provider_statuses_are_counted_independently():
    s=summarize_benchmark_records((
        _record(1,external=(_provider("ben",ProviderStatus.SUCCESS,True),_provider("ai2",ProviderStatus.ABSTAIN))),
        _record(2,external=(_provider("ben",ProviderStatus.SUCCESS,True),_provider("ai2",ProviderStatus.UNAVAILABLE))),
    ))
    assert s.provider_count("BEN",ProviderStatus.SUCCESS)==2
    assert s.provider_count("ai2",ProviderStatus.ABSTAIN)==1
    assert s.provider_count("ai2",ProviderStatus.UNAVAILABLE)==1

def test_disagreements_are_counted_as_already_classified():
    s=summarize_benchmark_records((
        _record(1,disagreements=(DisagreementKind.AGREEMENT,DisagreementKind.JUDGMENT_DIFFERENCE)),
        _record(2,disagreements=(DisagreementKind.JUDGMENT_DIFFERENCE,)),
    ))
    assert s.disagreement_count(DisagreementKind.AGREEMENT)==1
    assert s.disagreement_count(DisagreementKind.JUDGMENT_DIFFERENCE)==2

def test_failed_records_do_not_add_evidence_counts():
    failed=BenchmarkResultRecord(_id(1),BenchmarkExecutionStatus.FAILED,error_type="X",error_message="bad")
    s=summarize_benchmark_records((failed,))
    assert s.bridgelab_observed==0 and s.provider_status_counts==()
    assert sum(n for _,n in s.disagreement_counts)==0

def test_provider_rows_have_deterministic_order():
    s=summarize_benchmark_records((_record(1,external=(
        _provider("z",ProviderStatus.SUCCESS,True),
        _provider("A",ProviderStatus.UNAVAILABLE),
        _provider("A",ProviderStatus.ABSTAIN),
    )),))
    assert tuple((x.provider_id,x.status) for x in s.provider_status_counts)==(
        ("A",ProviderStatus.ABSTAIN),("A",ProviderStatus.UNAVAILABLE),("z",ProviderStatus.SUCCESS)
    )

def test_records_must_be_tuple():
    with pytest.raises(TypeError,match="tuple"): summarize_benchmark_records([])

def test_records_must_contain_result_records():
    with pytest.raises(TypeError,match="BenchmarkResultRecord"): summarize_benchmark_records(("x",))

def test_provider_count_validates_status():
    s=summarize_benchmark_records(())
    with pytest.raises(TypeError,match="ProviderStatus"): s.provider_count("ben","success")

def test_disagreement_count_validates_kind():
    s=summarize_benchmark_records(())
    with pytest.raises(TypeError,match="DisagreementKind"): s.disagreement_count("AGREEMENT")

def test_statistics_reject_inconsistent_execution_totals():
    with pytest.raises(ValueError,match="completed plus failed"):
        BenchmarkStatistics(2,2,1,0,0,0,0,(),())

def test_statistics_have_no_correctness_winner_or_ranking_surface():
    s=summarize_benchmark_records(())
    for name in ("correct","accuracy","winner","ranking","rank","score","selected","preferred"):
        assert not hasattr(s,name)

def test_statistics_are_immutable():
    s=summarize_benchmark_records(())
    with pytest.raises(AttributeError): s.total=1
