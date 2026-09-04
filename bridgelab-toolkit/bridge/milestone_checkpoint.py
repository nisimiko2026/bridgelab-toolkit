"""Phase 10E JSON checkpoints for resumable deterministic milestone execution."""
from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path

from .milestone_benchmark import MILESTONE_VERSION, MilestoneResult, MilestoneSummary
from .milestone_runner import merge_phase10_chunks, run_phase10_milestone


def summary_to_dict(summary: MilestoneSummary) -> dict:
    return {
        "schema": "bridgelab.phase10.checkpoint.v1",
        "version": summary.version,
        "start_seed": summary.start_seed,
        "deal_count": summary.deal_count,
        "results": [
            {
                "scenario_id": r.scenario_id,
                "deals": r.deals,
                "positions_reached": r.positions_reached,
                "production_actions": r.production_actions,
                "abstentions": r.abstentions,
                "rule_counts": [[rid, n] for rid, n in r.rule_counts],
            }
            for r in summary.results
        ],
    }


def summary_from_dict(data: dict) -> MilestoneSummary:
    if data.get("schema") != "bridgelab.phase10.checkpoint.v1":
        raise ValueError("unsupported checkpoint schema")
    if data.get("version") != MILESTONE_VERSION:
        raise ValueError("checkpoint milestone version mismatch")
    results=tuple(
        MilestoneResult(
            r["scenario_id"], int(r["deals"]), int(r["positions_reached"]),
            int(r["production_actions"]), int(r["abstentions"]),
            tuple((str(rid), int(n)) for rid, n in r["rule_counts"]),
        )
        for r in data["results"]
    )
    return MilestoneSummary(
        str(data["version"]), int(data["start_seed"]), int(data["deal_count"]), results
    )


def save_checkpoint(summary: MilestoneSummary, path: str | Path) -> Path:
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary_to_dict(summary),indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return path


def load_checkpoint(path: str | Path) -> MilestoneSummary:
    return summary_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def run_checkpoint(*, start_seed: int, count: int, path: str | Path) -> MilestoneSummary:
    summary=run_phase10_milestone(start_seed=start_seed,count=count)
    save_checkpoint(summary,path)
    return summary


def merge_checkpoint_files(
    paths: tuple[str | Path, ...], *, start_seed: int, total_count: int
) -> MilestoneSummary:
    chunks=tuple(load_checkpoint(p) for p in paths)
    return merge_phase10_chunks(chunks,start_seed=start_seed,total_count=total_count)
