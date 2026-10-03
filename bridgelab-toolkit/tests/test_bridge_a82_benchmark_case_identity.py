"""A8.2 benchmark case identity and replay tests."""
import pytest
from bridge.benchmark_case_identity import BenchmarkCaseIdentity, CorpusReplay, SyntheticReplay
from bridge.benchmark_manifest import DatasetIdentity, DatasetKind
from bridge.deals import generate_deal

def _synthetic():
    return DatasetIdentity("synthetic-a8","1",DatasetKind.SYNTHETIC,"generate_deal",1000)
def _real():
    return DatasetIdentity("real-a8","2026-10",DatasetKind.REAL,"test.pbn",1000)

def test_synthetic_case_round_trips_exact_deal():
    deal = generate_deal(42)
    case = BenchmarkCaseIdentity.for_synthetic(
        "case-42",
        _synthetic(),
        seed=42,
        deal=deal,
    )

    replayed = case.synthetic.replay_deal()

    assert replayed.serialize() == deal.serialize()
    assert case.synthetic.deal == deal.serialize()
    assert case.synthetic.seed == 42

def test_same_seed_and_dataset_make_stable_replay_key():
    a=BenchmarkCaseIdentity.for_synthetic("a",_synthetic(),seed=42,deal=generate_deal(42))
    b=BenchmarkCaseIdentity.for_synthetic("b",_synthetic(),seed=42,deal=generate_deal(42))
    assert a.replay_key==b.replay_key=="synthetic-a8@1:seed:42"

def test_corpus_case_uses_record_identity_not_seed():
    case=BenchmarkCaseIdentity.for_corpus("board-7",_real(),record_id="rec-7",source="test.pbn")
    assert case.synthetic is None
    assert case.corpus.record_id=="rec-7"
    assert case.replay_key=="real-a8@2026-10:record:rec-7"

def test_synthetic_dataset_rejects_corpus_replay():
    with pytest.raises(ValueError,match="synthetic replay only"):
        BenchmarkCaseIdentity("x",_synthetic(),corpus=CorpusReplay("r"))

def test_real_dataset_rejects_synthetic_replay():
    replay=SyntheticReplay(1,generate_deal(1).serialize())
    with pytest.raises(ValueError,match="corpus replay only"):
        BenchmarkCaseIdentity("x",_real(),synthetic=replay)

def test_synthetic_case_cannot_contain_both_replay_types():
    with pytest.raises(ValueError,match="synthetic replay only"):
        BenchmarkCaseIdentity("x",_synthetic(),synthetic=SyntheticReplay(1,generate_deal(1).serialize()),corpus=CorpusReplay("r"))

def test_real_case_cannot_contain_both_replay_types():
    with pytest.raises(ValueError,match="corpus replay only"):
        BenchmarkCaseIdentity("x",_real(),synthetic=SyntheticReplay(1,generate_deal(1).serialize()),corpus=CorpusReplay("r"))

def test_synthetic_factory_requires_real_deal_object():
    with pytest.raises(TypeError,match="deal must be Deal"):
        BenchmarkCaseIdentity.for_synthetic("x",_synthetic(),seed=1,deal="not-a-deal")

def test_synthetic_replay_validates_canonical_deal_text():
    with pytest.raises(Exception):
        SyntheticReplay(1,"not-a-deal")

def test_seed_rejects_bool_even_though_bool_is_int_subclass():
    with pytest.raises(TypeError,match="seed"):
        SyntheticReplay(True,generate_deal(1).serialize())

def test_corpus_record_id_must_be_nonblank():
    with pytest.raises(ValueError,match="record_id"):
        CorpusReplay(" ")

def test_dataset_version_participates_in_replay_identity():
    d1=DatasetIdentity("real-a8","1",DatasetKind.REAL,"x")
    d2=DatasetIdentity("real-a8","2",DatasetKind.REAL,"x")
    a=BenchmarkCaseIdentity.for_corpus("a",d1,record_id="r")
    b=BenchmarkCaseIdentity.for_corpus("b",d2,record_id="r")
    assert a.replay_key != b.replay_key

def test_case_identity_is_immutable():
    case=BenchmarkCaseIdentity.for_corpus("a",_real(),record_id="r")
    with pytest.raises(AttributeError):
        case.case_id="changed"
