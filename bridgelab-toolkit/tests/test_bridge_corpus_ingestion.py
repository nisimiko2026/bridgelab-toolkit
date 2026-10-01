import pytest
from bridge.corpus_providers import BridgeDealsNormalizedAdapter, PbnNormalizedAdapter
from bridge.corpus_validation import ValidationStatus, compare_provider_records, validate_record
from bridge.notation import normalize_rank_string

def sample(**changes):
    x={"source":"fixture","record_id":"7","board_number":7,"dealer":"N","vulnerability":"All","auction":["1C","P","1H","P","2H","P","4H","P","P","P"],"contract":"4H S","tricks":10}
    x.update(changes); return x

def test_french_rank_notation():
    assert normalize_rank_string("ARDV109",language="fr")[0] == "AKQJT9"

def test_two_independent_boundaries_agree():
    a=BridgeDealsNormalizedAdapter().adapt(sample())
    b=PbnNormalizedAdapter().adapt(sample())
    assert compare_provider_records(a,b).status is ValidationStatus.ACCEPT
    assert a.ns_system is None and a.ew_system is None

def test_provider_disagreement_is_conflict():
    a=BridgeDealsNormalizedAdapter().adapt(sample())
    b=PbnNormalizedAdapter().adapt(sample(tricks=9))
    r=compare_provider_records(a,b)
    assert r.status is ValidationStatus.INGESTION_CONFLICT
    assert "tricks" in r.issues[0]

def test_partial_record_warns():
    r=BridgeDealsNormalizedAdapter().adapt(sample())
    assert validate_record(r).status is ValidationStatus.ACCEPT_WITH_WARNINGS

def test_illegal_auction_is_not_silently_fixed():
    with pytest.raises(ValueError): BridgeDealsNormalizedAdapter().adapt(sample(auction=["1S","1H"]))
