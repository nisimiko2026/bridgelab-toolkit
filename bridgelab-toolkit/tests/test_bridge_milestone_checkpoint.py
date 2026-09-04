import json
import pytest
from bridge.milestone_runner import run_phase10_milestone
from bridge.milestone_checkpoint import (
    summary_to_dict,summary_from_dict,save_checkpoint,load_checkpoint,
    run_checkpoint,merge_checkpoint_files,
)

def test_dict_round_trip():
    a=run_phase10_milestone(start_seed=1,count=10)
    assert summary_from_dict(summary_to_dict(a))==a

def test_file_round_trip(tmp_path):
    a=run_phase10_milestone(start_seed=5,count=10)
    p=save_checkpoint(a,tmp_path/"a.json")
    assert load_checkpoint(p)==a

def test_run_checkpoint(tmp_path):
    p=tmp_path/"chunk.json"
    a=run_checkpoint(start_seed=1,count=8,path=p)
    assert p.exists()
    assert load_checkpoint(p)==a

def test_checkpoint_merge_matches_single_run(tmp_path):
    paths=[]
    for seed in (1,11,21,31):
        p=tmp_path/f"{seed}.json"
        run_checkpoint(start_seed=seed,count=10,path=p)
        paths.append(p)
    merged=merge_checkpoint_files(tuple(paths),start_seed=1,total_count=40)
    direct=run_phase10_milestone(start_seed=1,count=40)
    assert merged==direct

def test_reject_schema():
    a=summary_to_dict(run_phase10_milestone(start_seed=1,count=2))
    a["schema"]="wrong"
    with pytest.raises(ValueError):
        summary_from_dict(a)

def test_reject_version():
    a=summary_to_dict(run_phase10_milestone(start_seed=1,count=2))
    a["version"]="wrong"
    with pytest.raises(ValueError):
        summary_from_dict(a)
