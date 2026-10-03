"""A8.1 benchmark manifest contract tests."""
import pytest
from bridge.benchmark_manifest import AdviserIdentity,BenchmarkManifest,BenchmarkProfileIdentity,DatasetIdentity,DatasetKind,SolverIdentity

def _dataset(kind=DatasetKind.SYNTHETIC):
    return DatasetIdentity("a8-fixture","1",kind,"seeded-generator",100)
def _profile():
    return BenchmarkProfileIdentity("TWO_OVER_ONE_GF","1","nisim-nily","1","nisim-nily@1","1")
def _manifest(**kw):
    v=dict(benchmark_id="a8.1",benchmark_version="1",dataset=_dataset(),profile=_profile(),
      advisers=(AdviserIdentity("bridgelab","policy-engine","test"),AdviserIdentity("ben","external-adviser","0.8.8.7","ben-model")),
      solvers=(SolverIdentity("dds","test"),),seeds=(1,2,3),engine_version="test",source_revision="codex/phase18b",notes=("manifest-only",))
    v.update(kw); return BenchmarkManifest(**v)

def test_manifest_preserves_all_reproducibility_identities():
    m=_manifest(); assert m.dataset.dataset_id=="a8-fixture"; assert m.profile.system_id=="TWO_OVER_ONE_GF"; assert m.profile.partnership_id=="nisim-nily"; assert tuple(x.provider_id for x in m.advisers)==("bridgelab","ben"); assert m.solvers[0].solver_id=="dds"; assert m.seeds==(1,2,3)
def test_real_and_synthetic_are_distinct():
    assert _dataset(DatasetKind.REAL).kind is DatasetKind.REAL; assert _dataset().kind is DatasetKind.SYNTHETIC
def test_seeded_synthetic_is_deterministic(): assert _manifest().deterministic is True
def test_unseeded_synthetic_not_claimed_deterministic(): assert _manifest(seeds=()).deterministic is False
def test_real_dataset_needs_no_generation_seeds(): assert _manifest(dataset=_dataset(DatasetKind.REAL),seeds=()).deterministic is True
def test_profile_versions_are_paired():
    with pytest.raises(ValueError,match="partnership_id"): BenchmarkProfileIdentity("SAYC","1",partnership_id="pair")
    with pytest.raises(ValueError,match="resolved_profile_id"): BenchmarkProfileIdentity("SAYC","1",resolved_profile_version="1")
def test_duplicate_advisers_rejected_case_insensitively():
    with pytest.raises(ValueError,match="adviser provider_id"): _manifest(advisers=(AdviserIdentity("BEN","a","1"),AdviserIdentity("ben","b","2")))
def test_duplicate_solvers_rejected_case_insensitively():
    with pytest.raises(ValueError,match="solver_id"): _manifest(solvers=(SolverIdentity("DDS","1"),SolverIdentity("dds","2")))
def test_duplicate_seeds_rejected():
    with pytest.raises(ValueError,match="unique"): _manifest(seeds=(7,7))
def test_dataset_record_count_validation():
    with pytest.raises(ValueError,match="non-negative"): DatasetIdentity("d","1",DatasetKind.REAL,"corpus",-1)
    with pytest.raises(TypeError,match="integer"): DatasetIdentity("d","1",DatasetKind.REAL,"corpus",True)
def test_required_identity_fields_reject_blank():
    with pytest.raises(ValueError,match="dataset_id"): DatasetIdentity(" ","1",DatasetKind.REAL,"corpus")
    with pytest.raises(ValueError,match="system_id"): BenchmarkProfileIdentity("","1")
    with pytest.raises(ValueError,match="provider_id"): AdviserIdentity("","x","1")
    with pytest.raises(ValueError,match="solver_id"): SolverIdentity("","1")
def test_manifest_has_no_winner_or_result_surface():
    m=_manifest()
    for n in ("winner","ranking","rank","score","recommendation","selected","preferred","results","outcomes"): assert not hasattr(m,n)
def test_manifest_is_immutable():
    with pytest.raises(AttributeError): _manifest().benchmark_id="changed"
