"""A8.4 generic benchmark runner tests."""
import pytest

from bridge.benchmark_batch import BenchmarkBatch
from bridge.benchmark_case_identity import BenchmarkCaseIdentity
from bridge.benchmark_manifest import BenchmarkManifest, BenchmarkProfileIdentity, DatasetIdentity, DatasetKind
from bridge.benchmark_runner import BenchmarkCaseExecution, BenchmarkExecutionStatus, BenchmarkRun, run_benchmark_batch
from bridge.deals import generate_deal


def _dataset():
    return DatasetIdentity("synthetic-a8","1",DatasetKind.SYNTHETIC,"generate_deal",10)

def _batch(seeds=(1,2,3)):
    d=_dataset()
    m=BenchmarkManifest("a8.4","1",d,BenchmarkProfileIdentity("TWO_OVER_ONE_GF","1"),seeds=seeds)
    cases=tuple(BenchmarkCaseIdentity.for_synthetic(f"c-{s}",d,seed=s,deal=generate_deal(s)) for s in seeds)
    return BenchmarkBatch(m,cases)


def test_runner_executes_every_case_once_in_order():
    seen=[]
    run=run_benchmark_batch(_batch(),lambda c: seen.append(c.case_id) or c.replay_key)
    assert seen==["c-1","c-2","c-3"]
    assert tuple(x.identity.case_id for x in run.executions)==("c-1","c-2","c-3")
    assert run.completed==3 and run.failed==0

def test_runner_preserves_return_values():
    run=run_benchmark_batch(_batch((7,)),lambda c: {"key":c.replay_key})
    assert run.executions[0].result=={"key":"synthetic-a8@1:seed:7"}

def test_none_is_valid_completed_result():
    run=run_benchmark_batch(_batch((1,)),lambda c: None)
    assert run.executions[0].status is BenchmarkExecutionStatus.COMPLETED
    assert run.executions[0].result is None

def test_exception_is_isolated_and_later_case_runs():
    seen=[]
    def execute(c):
        seen.append(c.case_id)
        if c.case_id=="c-2": raise RuntimeError("boom")
        return c.case_id
    run=run_benchmark_batch(_batch(),execute)
    assert seen==["c-1","c-2","c-3"]
    assert tuple(x.status for x in run.executions)==(
        BenchmarkExecutionStatus.COMPLETED,
        BenchmarkExecutionStatus.FAILED,
        BenchmarkExecutionStatus.COMPLETED,
    )
    assert run.executions[1].error_type=="RuntimeError"
    assert run.executions[1].error_message=="boom"
    assert run.completed==2 and run.failed==1

def test_failed_execution_has_no_result():
    run=run_benchmark_batch(_batch((1,)),lambda c: (_ for _ in ()).throw(ValueError("bad")))
    item=run.executions[0]
    assert item.result is None
    assert item.error_type=="ValueError"

def test_empty_batch_runs_cleanly():
    d=_dataset()
    m=BenchmarkManifest("a8.4","1",d,BenchmarkProfileIdentity("SAYC","1"),seeds=())
    run=run_benchmark_batch(BenchmarkBatch(m,()),lambda c: c)
    assert run.executions==() and run.completed==0 and run.failed==0

def test_runner_rejects_non_batch():
    with pytest.raises(TypeError,match="batch"): run_benchmark_batch("x",lambda c:c)

def test_runner_rejects_non_callable_executor():
    with pytest.raises(TypeError,match="callable"): run_benchmark_batch(_batch((1,)),None)

def test_completed_execution_rejects_error_metadata():
    c=_batch((1,)).cases[0]
    with pytest.raises(ValueError,match="completed"):
        BenchmarkCaseExecution(c,BenchmarkExecutionStatus.COMPLETED,result="x",error_type="X")

def test_failed_execution_rejects_result():
    c=_batch((1,)).cases[0]
    with pytest.raises(ValueError,match="cannot contain a result"):
        BenchmarkCaseExecution(c,BenchmarkExecutionStatus.FAILED,result="x",error_type="X",error_message="bad")

def test_failed_execution_requires_error_type():
    c=_batch((1,)).cases[0]
    with pytest.raises(ValueError,match="error_type"):
        BenchmarkCaseExecution(c,BenchmarkExecutionStatus.FAILED,error_message="bad")

def test_run_requires_exact_case_order():
    b=_batch((1,2))
    executions=(
        BenchmarkCaseExecution(b.cases[1],BenchmarkExecutionStatus.COMPLETED),
        BenchmarkCaseExecution(b.cases[0],BenchmarkExecutionStatus.COMPLETED),
    )
    with pytest.raises(ValueError,match="in order"): BenchmarkRun(b,executions)

def test_run_requires_one_execution_per_case():
    b=_batch((1,2))
    executions=(BenchmarkCaseExecution(b.cases[0],BenchmarkExecutionStatus.COMPLETED),)
    with pytest.raises(ValueError,match="count"): BenchmarkRun(b,executions)

def test_runner_has_no_ranking_winner_or_policy_surface():
    run=run_benchmark_batch(_batch((1,)),lambda c:"evidence")
    for name in ("winner","ranking","rank","score","recommendation","selected","preferred","policy"):
        assert not hasattr(run,name)

def test_execution_records_are_immutable():
    item=run_benchmark_batch(_batch((1,)),lambda c:"ok").executions[0]
    with pytest.raises(AttributeError): item.status=BenchmarkExecutionStatus.FAILED
