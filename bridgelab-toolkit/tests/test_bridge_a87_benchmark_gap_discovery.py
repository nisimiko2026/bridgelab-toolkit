"""A8.7 conservative gap discovery tests."""
import pytest
from bridge.benchmark_case_identity import BenchmarkCaseIdentity
from bridge.benchmark_gap_discovery import GapCategory,GapDiscoveryItem,GapDiscoveryReport,discover_benchmark_gaps
from bridge.benchmark_manifest import DatasetIdentity,DatasetKind
from bridge.benchmark_result_record import BenchmarkResultRecord
from bridge.benchmark_runner import BenchmarkExecutionStatus
from bridge.decision_evidence import DisagreementKind
from bridge.deals import generate_deal

def _id(n):
    d=DatasetIdentity("a8","1",DatasetKind.SYNTHETIC,"generator")
    return BenchmarkCaseIdentity.for_synthetic(f"c{n}",d,seed=n,deal=generate_deal(n))

def _record(n,*kinds):
    return BenchmarkResultRecord(_id(n),BenchmarkExecutionStatus.COMPLETED,disagreements=tuple(kinds))

@pytest.mark.parametrize("kind,category",[
    (DisagreementKind.POSSIBLE_POLICY_GAP,GapCategory.POLICY_GAP),
    (DisagreementKind.POSSIBLE_ENGINE_DEFECT,GapCategory.ENGINE_DEFECT),
    (DisagreementKind.SYSTEM_DIFFERENCE,GapCategory.SYSTEM_DIFFERENCE),
    (DisagreementKind.CONVENTION_DIFFERENCE,GapCategory.CONVENTION_DIFFERENCE),
    (DisagreementKind.TREATMENT_DIFFERENCE,GapCategory.TREATMENT_DIFFERENCE),
    (DisagreementKind.PARTNERSHIP_AGREEMENT,GapCategory.PARTNERSHIP_AGREEMENT),
    (DisagreementKind.JUDGMENT_DIFFERENCE,GapCategory.JUDGMENT_DIFFERENCE),
    (DisagreementKind.BRIDGELAB_ABSTAIN,GapCategory.BRIDGELAB_ABSTENTION),
    (DisagreementKind.EXTERNAL_MODEL_ABSTAIN,GapCategory.EXTERNAL_ABSTENTION),
    (DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,GapCategory.UNKNOWN_EXTERNAL_SYSTEM),
])
def test_existing_classification_maps_without_reinterpretation(kind,category):
    report=discover_benchmark_gaps((_record(1,kind),))
    assert report.items[0].category is category
    assert report.items[0].source_kind is kind

def test_agreement_is_not_a_gap_item():
    r=discover_benchmark_gaps((_record(1,DisagreementKind.AGREEMENT),))
    assert r.items==()

def test_failure_is_separate_from_bridge_semantic_gaps():
    record=BenchmarkResultRecord(_id(1),BenchmarkExecutionStatus.FAILED,error_type="RuntimeError",error_message="boom")
    r=discover_benchmark_gaps((record,))
    assert r.items[0].category is GapCategory.EXECUTION_FAILURE
    assert r.items[0].source_kind is None
    assert r.items[0].error_type=="RuntimeError"

def test_multiple_existing_disagreements_preserve_order():
    r=discover_benchmark_gaps((_record(1,DisagreementKind.SYSTEM_DIFFERENCE,DisagreementKind.JUDGMENT_DIFFERENCE),))
    assert tuple(x.category for x in r.items)==(GapCategory.SYSTEM_DIFFERENCE,GapCategory.JUDGMENT_DIFFERENCE)

def test_case_identity_and_replay_key_are_preserved():
    r=discover_benchmark_gaps((_record(7,DisagreementKind.POSSIBLE_POLICY_GAP),))
    assert r.items[0].case_id=="c7"
    assert r.items[0].replay_key=="a8@1:seed:7"

def test_review_candidate_count_only_policy_and_engine():
    r=discover_benchmark_gaps((
        _record(1,DisagreementKind.POSSIBLE_POLICY_GAP),
        _record(2,DisagreementKind.POSSIBLE_ENGINE_DEFECT),
        _record(3,DisagreementKind.JUDGMENT_DIFFERENCE),
    ))
    assert r.review_candidate_count==2

def test_count_is_descriptive():
    r=discover_benchmark_gaps((_record(1,DisagreementKind.SYSTEM_DIFFERENCE),_record(2,DisagreementKind.SYSTEM_DIFFERENCE)))
    assert r.count(GapCategory.SYSTEM_DIFFERENCE)==2

def test_empty_input():
    r=discover_benchmark_gaps(())
    assert r.total_records==0 and r.items==() and r.review_candidate_count==0

def test_input_must_be_tuple():
    with pytest.raises(TypeError,match="tuple"): discover_benchmark_gaps([])

def test_input_must_contain_records():
    with pytest.raises(TypeError,match="BenchmarkResultRecord"): discover_benchmark_gaps(("x",))

def test_count_validates_category():
    with pytest.raises(TypeError,match="GapCategory"): GapDiscoveryReport(0,()).count("policy-gap")

def test_failure_item_requires_error_type():
    with pytest.raises(ValueError,match="error_type"):
        GapDiscoveryItem("c","key",GapCategory.EXECUTION_FAILURE)

def test_non_failure_item_rejects_error_type():
    with pytest.raises(ValueError,match="non-failure"):
        GapDiscoveryItem("c","key",GapCategory.JUDGMENT_DIFFERENCE,DisagreementKind.JUDGMENT_DIFFERENCE,"X")

def test_report_is_immutable():
    r=discover_benchmark_gaps(())
    with pytest.raises(AttributeError): r.total_records=1

def test_report_has_no_correctness_winner_ranking_or_policy_override_surface():
    r=discover_benchmark_gaps(())
    for name in ("correct","accuracy","winner","ranking","rank","score","selected","preferred","override"):
        assert not hasattr(r,name)
