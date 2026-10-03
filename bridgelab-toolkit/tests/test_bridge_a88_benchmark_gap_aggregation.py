"""A8.8 gap aggregation tests."""
import pytest
from bridge.benchmark_gap_aggregation import GapAggregateGroup,GapAggregation,aggregate_gap_discovery
from bridge.benchmark_gap_discovery import GapCategory,GapDiscoveryItem,GapDiscoveryReport
from bridge.decision_evidence import DisagreementKind

def _item(n,category,kind=DisagreementKind.JUDGMENT_DIFFERENCE):
    return GapDiscoveryItem(f"c{n}",f"d@1:seed:{n}",category,kind)

def test_empty_report_aggregates_cleanly():
    a=aggregate_gap_discovery(GapDiscoveryReport(0,()))
    assert a.total_records==0 and a.total_items==0 and a.groups==()

def test_same_category_is_grouped_and_provenance_preserved():
    r=GapDiscoveryReport(2,(_item(1,GapCategory.JUDGMENT_DIFFERENCE),_item(2,GapCategory.JUDGMENT_DIFFERENCE)))
    a=aggregate_gap_discovery(r)
    g=a.groups[0]
    assert g.count==2
    assert g.case_ids==("c1","c2")
    assert g.replay_keys==("d@1:seed:1","d@1:seed:2")

def test_different_categories_remain_separate():
    r=GapDiscoveryReport(2,(
        _item(1,GapCategory.POLICY_GAP,DisagreementKind.POSSIBLE_POLICY_GAP),
        _item(2,GapCategory.SYSTEM_DIFFERENCE,DisagreementKind.SYSTEM_DIFFERENCE),
    ))
    a=aggregate_gap_discovery(r)
    assert a.count(GapCategory.POLICY_GAP)==1
    assert a.count(GapCategory.SYSTEM_DIFFERENCE)==1

def test_group_order_is_enum_order_not_frequency_priority():
    r=GapDiscoveryReport(4,(
        _item(1,GapCategory.JUDGMENT_DIFFERENCE),
        _item(2,GapCategory.JUDGMENT_DIFFERENCE),
        _item(3,GapCategory.JUDGMENT_DIFFERENCE),
        _item(4,GapCategory.POLICY_GAP,DisagreementKind.POSSIBLE_POLICY_GAP),
    ))
    a=aggregate_gap_discovery(r)
    assert tuple(x.category for x in a.groups)==(GapCategory.POLICY_GAP,GapCategory.JUDGMENT_DIFFERENCE)

def test_execution_failures_preserve_error_types():
    items=(
        GapDiscoveryItem("c1","k1",GapCategory.EXECUTION_FAILURE,error_type="RuntimeError"),
        GapDiscoveryItem("c2","k2",GapCategory.EXECUTION_FAILURE,error_type="TimeoutError"),
    )
    g=aggregate_gap_discovery(GapDiscoveryReport(2,items)).groups[0]
    assert g.error_types==("RuntimeError","TimeoutError")

def test_review_candidate_count_only_policy_and_engine():
    r=GapDiscoveryReport(3,(
        _item(1,GapCategory.POLICY_GAP,DisagreementKind.POSSIBLE_POLICY_GAP),
        _item(2,GapCategory.ENGINE_DEFECT,DisagreementKind.POSSIBLE_ENGINE_DEFECT),
        _item(3,GapCategory.JUDGMENT_DIFFERENCE),
    ))
    assert aggregate_gap_discovery(r).review_candidate_count==2

def test_total_records_can_exceed_gap_items():
    a=aggregate_gap_discovery(GapDiscoveryReport(100,(_item(1,GapCategory.JUDGMENT_DIFFERENCE),)))
    assert a.total_records==100 and a.total_items==1

def test_count_returns_zero_for_absent_category():
    assert aggregate_gap_discovery(GapDiscoveryReport(0,())).count(GapCategory.POLICY_GAP)==0

def test_aggregate_requires_report():
    with pytest.raises(TypeError,match="GapDiscoveryReport"): aggregate_gap_discovery(())

def test_count_requires_category():
    with pytest.raises(TypeError,match="GapCategory"): GapAggregation(0,0,()).count("policy-gap")

def test_group_requires_positive_count():
    with pytest.raises(ValueError,match="positive"): GapAggregateGroup(GapCategory.POLICY_GAP,0,(),())

def test_group_requires_matching_case_ids():
    with pytest.raises(ValueError,match="case_ids length"): GapAggregateGroup(GapCategory.POLICY_GAP,2,("c1",),("k1","k2"))

def test_group_requires_matching_replay_keys():
    with pytest.raises(ValueError,match="replay_keys length"): GapAggregateGroup(GapCategory.POLICY_GAP,2,("c1","c2"),("k1",))

def test_failure_group_requires_one_error_type_per_item():
    with pytest.raises(ValueError,match="error_types length"):
        GapAggregateGroup(GapCategory.EXECUTION_FAILURE,1,("c1",),("k1",),())

def test_non_failure_group_rejects_error_types():
    with pytest.raises(ValueError,match="non-failure"):
        GapAggregateGroup(GapCategory.POLICY_GAP,1,("c1",),("k1",),("X",))

def test_aggregation_validates_total_items():
    g=GapAggregateGroup(GapCategory.POLICY_GAP,1,("c1",),("k1",))
    with pytest.raises(ValueError,match="group counts"): GapAggregation(1,2,(g,))

def test_aggregation_rejects_duplicate_categories():
    g1=GapAggregateGroup(GapCategory.POLICY_GAP,1,("c1",),("k1",))
    g2=GapAggregateGroup(GapCategory.POLICY_GAP,1,("c2",),("k2",))
    with pytest.raises(ValueError,match="unique"): GapAggregation(2,2,(g1,g2))

def test_aggregation_is_immutable():
    a=aggregate_gap_discovery(GapDiscoveryReport(0,()))
    with pytest.raises(AttributeError): a.total_items=1

def test_no_priority_score_rank_winner_or_correctness_surface():
    a=aggregate_gap_discovery(GapDiscoveryReport(0,()))
    for name in ("priority","priority_score","score","rank","ranking","winner","correct","accuracy","selected","preferred"):
        assert not hasattr(a,name)
