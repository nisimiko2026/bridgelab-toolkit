"""A8.5 normalized benchmark result record tests."""
import pytest
from bridge.auction import Call
from bridge.benchmark_case_identity import BenchmarkCaseIdentity
from bridge.benchmark_manifest import DatasetIdentity,DatasetKind
from bridge.benchmark_result_record import BenchmarkProviderRecord,BenchmarkResultRecord,benchmark_result_record
from bridge.benchmark_runner import BenchmarkCaseExecution,BenchmarkExecutionStatus
from bridge.capability_providers import Capability,CapabilityResult,ProviderDescriptor,ProviderEvidence,ProviderStatus
from bridge.decision_case import DecisionCase
from bridge.decision_evidence import DecisionEvidence,Disagreement,DisagreementKind,EvidenceScope
from bridge.deals import generate_deal

def _identity():
    d=DatasetIdentity("a8","1",DatasetKind.SYNTHETIC,"generator")
    return BenchmarkCaseIdentity.for_synthetic("c1",d,seed=1,deal=generate_deal(1))

def _evidence(provider,call=None,status=ProviderStatus.SUCCESS,source_ids=(),model_id=None):
    return DecisionEvidence(
        result=CapabilityResult(
            provider=ProviderDescriptor(provider,Capability.BIDDING,f"{provider}-test","1"),
            status=status,
            recommendation=Call.parse(call) if status is ProviderStatus.SUCCESS else None,
            evidence=ProviderEvidence(source_ids=source_ids,model_id=model_id),
        ),
        scope=EvidenceScope.PROVIDER,
    )

def test_decision_case_is_normalized_without_losing_payload():
    bridge=_evidence("bridgelab","1S",source_ids=("policy:1",),model_id="policy")
    ben=_evidence("ben","2S",source_ids=("ben:1",),model_id="ben-model")
    disagreement=Disagreement(DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,"bridgelab","ben","test")
    case=DecisionCase("decision",bridgelab=bridge,external=(ben,),disagreements=(disagreement,))
    execution=BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.COMPLETED,result=case)
    record=benchmark_result_record(execution)
    assert record.payload is case
    assert record.bridgelab.provider_id=="bridgelab"
    assert record.bridgelab.source_ids==("policy:1",)
    assert record.external[0].model_id=="ben-model"
    assert record.disagreements==(DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,)

def test_abstention_is_preserved_not_failure():
    bridge=_evidence("bridgelab",status=ProviderStatus.ABSTAIN)
    case=DecisionCase("d",bridgelab=bridge)
    record=benchmark_result_record(BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.COMPLETED,result=case))
    assert record.execution_status is BenchmarkExecutionStatus.COMPLETED
    assert record.bridgelab.status is ProviderStatus.ABSTAIN
    assert record.bridgelab_abstained is True

def test_success_recommendation_flag_is_true():
    r=benchmark_result_record(BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.COMPLETED,result=DecisionCase("d",bridgelab=_evidence("bridgelab","1NT"))))
    assert r.bridgelab.has_recommendation is True

def test_external_operational_status_is_preserved():
    ext=_evidence("offline",status=ProviderStatus.UNAVAILABLE)
    r=benchmark_result_record(BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.COMPLETED,result=DecisionCase("d",external=(ext,))))
    assert r.external[0].status is ProviderStatus.UNAVAILABLE
    assert r.external[0].has_recommendation is False

def test_failed_execution_becomes_failure_record():
    execution=BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.FAILED,error_type="RuntimeError",error_message="boom")
    r=benchmark_result_record(execution)
    assert r.execution_status is BenchmarkExecutionStatus.FAILED
    assert r.error_type=="RuntimeError" and r.error_message=="boom"
    assert r.payload is None and r.bridgelab is None and r.external==()

def test_non_decision_payload_is_preserved_opaquely():
    payload={"simulation":"result"}
    r=benchmark_result_record(BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.COMPLETED,result=payload))
    assert r.payload is payload
    assert r.bridgelab is None and r.external==() and r.disagreements==()

def test_none_payload_is_valid_completed_record():
    r=benchmark_result_record(BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.COMPLETED,result=None))
    assert r.execution_status is BenchmarkExecutionStatus.COMPLETED and r.payload is None

def test_provider_record_validates_status():
    with pytest.raises(TypeError,match="ProviderStatus"):
        BenchmarkProviderRecord("x","success",True)

def test_provider_record_rejects_blank_source_id():
    with pytest.raises(TypeError,match="source_ids"):
        BenchmarkProviderRecord("x",ProviderStatus.SUCCESS,True,source_ids=(" ",))

def test_failed_record_rejects_evidence():
    p=BenchmarkProviderRecord("x",ProviderStatus.SUCCESS,True)
    with pytest.raises(ValueError,match="cannot contain benchmark evidence"):
        BenchmarkResultRecord(_identity(),BenchmarkExecutionStatus.FAILED,bridgelab=p,error_type="X",error_message="bad")

def test_completed_record_rejects_error_metadata():
    with pytest.raises(ValueError,match="cannot contain error"):
        BenchmarkResultRecord(_identity(),BenchmarkExecutionStatus.COMPLETED,error_type="X")

def test_function_rejects_non_execution():
    with pytest.raises(TypeError,match="BenchmarkCaseExecution"):
        benchmark_result_record("x")

def test_record_is_immutable():
    r=benchmark_result_record(BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.COMPLETED,result=None))
    with pytest.raises(AttributeError): r.payload="changed"

def test_record_has_no_winner_ranking_or_policy_surface():
    r=benchmark_result_record(BenchmarkCaseExecution(_identity(),BenchmarkExecutionStatus.COMPLETED,result=None))
    for name in ("winner","ranking","rank","score","recommendation","selected","preferred","policy"):
        assert not hasattr(r,name)
