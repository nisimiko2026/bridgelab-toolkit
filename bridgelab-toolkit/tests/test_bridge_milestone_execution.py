from bridge.milestone_execution import checkpoint_plan, completed_checkpoint_specs, next_pending_checkpoint, run_next_checkpoint, merge_completed_plan

def test_plan_exact_ranges(tmp_path):
    p=checkpoint_plan(directory=tmp_path,start_seed=1,total_count=23,chunk_size=10)
    assert [(x.start_seed,x.end_seed,x.count) for x in p]==[(1,10,10),(11,20,10),(21,23,3)]

def test_resume_and_merge(tmp_path):
    p=checkpoint_plan(directory=tmp_path,start_seed=1,total_count=20,chunk_size=10)
    assert next_pending_checkpoint(p).start_seed==1
    run_next_checkpoint(p)
    assert len(completed_checkpoint_specs(p))==1
    assert next_pending_checkpoint(p).start_seed==11
    run_next_checkpoint(p)
    assert len(completed_checkpoint_specs(p))==2
    merged=merge_completed_plan(p)
    assert merged.start_seed==1 and merged.deal_count==20
    assert next_pending_checkpoint(p) is None
