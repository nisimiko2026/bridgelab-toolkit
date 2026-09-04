"""Phase 10F persistent milestone execution planning and checkpoint status.

This module contains execution orchestration only. It does not change bidding
rules or partnership defaults.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .milestone_checkpoint import load_checkpoint, merge_checkpoint_files, run_checkpoint

@dataclass(frozen=True, slots=True)
class CheckpointSpec:
    start_seed: int
    count: int
    path: Path

    @property
    def end_seed(self) -> int:
        return self.start_seed + self.count - 1


def checkpoint_plan(*, directory: str|Path, start_seed:int=1, total_count:int=100_000, chunk_size:int=1_000) -> tuple[CheckpointSpec,...]:
    if total_count <= 0 or chunk_size <= 0:
        raise ValueError('total_count and chunk_size must be positive')
    directory=Path(directory)
    out=[]
    offset=0
    while offset < total_count:
        n=min(chunk_size,total_count-offset)
        seed=start_seed+offset
        end=seed+n-1
        out.append(CheckpointSpec(seed,n,directory/f'chunk_{seed:06d}_{end:06d}.json'))
        offset += n
    return tuple(out)


def completed_checkpoint_specs(plan: tuple[CheckpointSpec,...]) -> tuple[CheckpointSpec,...]:
    completed=[]
    for spec in plan:
        if not spec.path.exists():
            continue
        summary=load_checkpoint(spec.path)
        if summary.start_seed != spec.start_seed or summary.deal_count != spec.count:
            raise ValueError(f'checkpoint does not match plan: {spec.path}')
        completed.append(spec)
    return tuple(completed)


def next_pending_checkpoint(plan: tuple[CheckpointSpec,...]) -> CheckpointSpec|None:
    done={x.path for x in completed_checkpoint_specs(plan)}
    return next((x for x in plan if x.path not in done),None)


def run_next_checkpoint(plan: tuple[CheckpointSpec,...]):
    spec=next_pending_checkpoint(plan)
    if spec is None:
        return None
    spec.path.parent.mkdir(parents=True,exist_ok=True)
    return run_checkpoint(start_seed=spec.start_seed,count=spec.count,path=spec.path)


def merge_completed_plan(plan: tuple[CheckpointSpec,...]):
    completed=completed_checkpoint_specs(plan)
    if len(completed) != len(plan):
        raise ValueError('milestone plan is incomplete')
    return merge_checkpoint_files(tuple(x.path for x in completed),start_seed=plan[0].start_seed,total_count=sum(x.count for x in plan))
