"""A8.3 benchmark batch definition tests."""

import pytest

from bridge.benchmark_batch import BenchmarkBatch
from bridge.benchmark_case_identity import BenchmarkCaseIdentity
from bridge.benchmark_manifest import (
    BenchmarkManifest,
    BenchmarkProfileIdentity,
    DatasetIdentity,
    DatasetKind,
)
from bridge.deals import generate_deal


def _profile():
    return BenchmarkProfileIdentity("TWO_OVER_ONE_GF", "1")


def _synthetic_dataset(version="1", count=10):
    return DatasetIdentity("synthetic-a8", version, DatasetKind.SYNTHETIC, "generate_deal", count)


def _real_dataset(version="1", count=10):
    return DatasetIdentity("real-a8", version, DatasetKind.REAL, "test.pbn", count)


def _manifest(dataset, seeds=()):
    return BenchmarkManifest("a8.3", "1", dataset, _profile(), seeds=seeds)


def _synthetic_case(case_id, dataset, seed):
    return BenchmarkCaseIdentity.for_synthetic(
        case_id, dataset, seed=seed, deal=generate_deal(seed)
    )


def _real_case(case_id, dataset, record_id):
    return BenchmarkCaseIdentity.for_corpus(case_id, dataset, record_id=record_id)


def test_synthetic_batch_accepts_matching_manifest_and_cases():
    dataset = _synthetic_dataset()
    batch = BenchmarkBatch(
        _manifest(dataset, seeds=(1, 2, 3)),
        tuple(_synthetic_case(f"c-{seed}", dataset, seed) for seed in (1, 2, 3)),
    )
    assert batch.case_count == 3
    assert batch.replay_keys == (
        "synthetic-a8@1:seed:1",
        "synthetic-a8@1:seed:2",
        "synthetic-a8@1:seed:3",
    )


def test_real_batch_accepts_record_id_cases_without_seeds():
    dataset = _real_dataset()
    batch = BenchmarkBatch(
        _manifest(dataset),
        (
            _real_case("c1", dataset, "r1"),
            _real_case("c2", dataset, "r2"),
        ),
    )
    assert batch.case_count == 2


def test_empty_batch_is_valid():
    dataset = _synthetic_dataset()
    assert BenchmarkBatch(_manifest(dataset, seeds=(1,)), ()).case_count == 0


def test_duplicate_case_ids_are_rejected():
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError, match="case_id"):
        BenchmarkBatch(
            _manifest(dataset, seeds=(1, 2)),
            (
                _synthetic_case("same", dataset, 1),
                _synthetic_case("same", dataset, 2),
            ),
        )


def test_duplicate_replay_identity_is_rejected():
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError, match="replay identities"):
        BenchmarkBatch(
            _manifest(dataset, seeds=(1,)),
            (
                _synthetic_case("a", dataset, 1),
                _synthetic_case("b", dataset, 1),
            ),
        )


def test_case_dataset_id_must_match_manifest():
    manifest_dataset = _synthetic_dataset()
    other = DatasetIdentity("other", "1", DatasetKind.SYNTHETIC, "generate_deal", 10)
    with pytest.raises(ValueError, match="does not match"):
        BenchmarkBatch(
            _manifest(manifest_dataset, seeds=(1,)),
            (_synthetic_case("c", other, 1),),
        )


def test_case_dataset_version_must_match_manifest():
    manifest_dataset = _synthetic_dataset("1")
    other = _synthetic_dataset("2")
    with pytest.raises(ValueError, match="does not match"):
        BenchmarkBatch(
            _manifest(manifest_dataset, seeds=(1,)),
            (_synthetic_case("c", other, 1),),
        )


def test_case_dataset_kind_must_match_manifest():
    synthetic = _synthetic_dataset()
    real = DatasetIdentity(
        synthetic.dataset_id, synthetic.version, DatasetKind.REAL, synthetic.source, 10
    )
    with pytest.raises(ValueError, match="does not match"):
        BenchmarkBatch(
            _manifest(synthetic, seeds=(1,)),
            (_real_case("c", real, "r1"),),
        )


def test_synthetic_case_seed_must_be_declared_when_manifest_has_seed_set():
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError, match="not declared"):
        BenchmarkBatch(
            _manifest(dataset, seeds=(1, 2)),
            (_synthetic_case("c", dataset, 3),),
        )


def test_manifest_may_describe_superset_of_batch_seeds():
    dataset = _synthetic_dataset()
    batch = BenchmarkBatch(
        _manifest(dataset, seeds=(1, 2, 3, 4)),
        (
            _synthetic_case("c1", dataset, 1),
            _synthetic_case("c3", dataset, 3),
        ),
    )
    assert batch.case_count == 2


def test_real_manifest_rejects_generation_seeds():
    dataset = _real_dataset()
    with pytest.raises(ValueError, match="must not declare seeds"):
        BenchmarkBatch(
            _manifest(dataset, seeds=(1,)),
            (_real_case("c", dataset, "r1"),),
        )


def test_batch_cannot_exceed_declared_dataset_record_count():
    dataset = _real_dataset(count=1)
    with pytest.raises(ValueError, match="record_count"):
        BenchmarkBatch(
            _manifest(dataset),
            (
                _real_case("c1", dataset, "r1"),
                _real_case("c2", dataset, "r2"),
            ),
        )


def test_cases_must_be_tuple():
    dataset = _real_dataset()
    with pytest.raises(TypeError, match="tuple"):
        BenchmarkBatch(_manifest(dataset), [])


def test_cases_must_contain_case_identities():
    dataset = _real_dataset()
    with pytest.raises(TypeError, match="BenchmarkCaseIdentity"):
        BenchmarkBatch(_manifest(dataset), ("not-a-case",))


def test_batch_is_passive_with_no_winner_ranking_or_score_surface():
    dataset = _real_dataset()
    batch = BenchmarkBatch(_manifest(dataset), ())
    for name in (
        "winner", "ranking", "rank", "score", "recommendation",
        "selected", "preferred", "results", "outcomes",
    ):
        assert not hasattr(batch, name)


def test_batch_is_immutable():
    dataset = _real_dataset()
    batch = BenchmarkBatch(_manifest(dataset), ())
    with pytest.raises(AttributeError):
        batch.cases = ()
