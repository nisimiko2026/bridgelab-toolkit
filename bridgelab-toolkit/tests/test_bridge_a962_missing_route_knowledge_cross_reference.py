from bridge.evidence_review_contract import ReviewClassification as C
from bridge.missing_route_structural_classification import MissingRouteStructuralFamily as F
from bridge.missing_route_knowledge_cross_reference import (
    KnowledgeStatus as K,
    _mapping,
    cross_reference_missing_route_knowledge,
)

def test_weak_two_responses_are_partnership_agreement():
    c,k,ready,_ = _mapping(F.RESPONSE_TO_TWO_LEVEL_OPENING)
    assert c is C.PARTNERSHIP_AGREEMENT
    assert k is K.DEFERRED_PARTNERSHIP_POLICY
    assert not ready

def test_three_level_preempt_responses_remain_judgment_source_partial():
    c,k,ready,_ = _mapping(F.RESPONSE_TO_THREE_LEVEL_OPENING)
    assert c is C.JUDGMENT
    assert k is K.DEFERRED_SOURCE_PARTIAL
    assert not ready

def test_opener_rebid_is_known_partial_coverage():
    c,k,ready,_ = _mapping(F.OPENER_REBID_AFTER_ONE_LEVEL_RESPONSE)
    assert c is C.KNOWN_CONVENTION_MISSING_TREATMENT
    assert k is K.CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE
    assert not ready

def test_responder_rebid_remains_source_partial():
    c,k,ready,_ = _mapping(F.RESPONDER_REBID_AFTER_OPENER_REBID)
    assert c is C.KNOWN_CONVENTION_MISSING_TREATMENT
    assert k is K.DEFERRED_SOURCE_PARTIAL
    assert not ready

def test_later_continuation_remains_source_partial():
    c,k,ready,_ = _mapping(F.LATER_CONTINUATION)
    assert c is C.KNOWN_CONVENTION_MISSING_TREATMENT
    assert k is K.DEFERRED_SOURCE_PARTIAL
    assert not ready

def test_report_accounts_for_full_missing_route_population():
    r = cross_reference_missing_route_knowledge(start_seed=1,count=100)
    assert sum(x.population for x in r.entries) == r.missing_route_population

def test_a962_does_not_mark_any_family_production_ready():
    r = cross_reference_missing_route_knowledge(start_seed=1,count=100)
    assert not any(x.production_ready for x in r.entries)

def test_no_bid_or_recommendation_surface():
    r = cross_reference_missing_route_knowledge(start_seed=1,count=25)
    assert all(not hasattr(x,"call") for x in r.entries)
    assert all(not hasattr(x,"recommendation") for x in r.entries)
