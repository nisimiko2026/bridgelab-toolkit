"""Validated batch definition for reproducible BridgeLab benchmarks.

A8.3 binds one A8.1 manifest to A8.2 case identities.  It validates identity
consistency only; it does not execute, rank, score, or alter bidding policy.
"""
from __future__ import annotations

from dataclasses import dataclass

from .benchmark_case_identity import BenchmarkCaseIdentity
from .benchmark_manifest import BenchmarkManifest, DatasetKind


@dataclass(frozen=True, slots=True)
class BenchmarkBatch:
    manifest: BenchmarkManifest
    cases: tuple[BenchmarkCaseIdentity, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, BenchmarkManifest):
            raise TypeError("manifest must be BenchmarkManifest")
        if not isinstance(self.cases, tuple):
            raise TypeError("cases must be a tuple")
        if not all(isinstance(x, BenchmarkCaseIdentity) for x in self.cases):
            raise TypeError("cases must contain BenchmarkCaseIdentity")

        case_ids = tuple(x.case_id for x in self.cases)
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("case_id values must be unique")

        replay_keys = tuple(x.replay_key for x in self.cases)
        if len(set(replay_keys)) != len(replay_keys):
            raise ValueError("case replay identities must be unique")

        expected = self.manifest.dataset
        for case in self.cases:
            if case.dataset != expected:
                raise ValueError(
                    f"case {case.case_id} dataset does not match manifest dataset"
                )

        if expected.record_count is not None and len(self.cases) > expected.record_count:
            raise ValueError("batch contains more cases than dataset record_count")

        if expected.kind is DatasetKind.SYNTHETIC:
            case_seeds = tuple(x.synthetic.seed for x in self.cases)
            manifest_seeds = self.manifest.seeds

            if len(set(case_seeds)) != len(case_seeds):
                raise ValueError("synthetic case seeds must be unique")

            if manifest_seeds:
                allowed = set(manifest_seeds)
                missing = tuple(seed for seed in case_seeds if seed not in allowed)
                if missing:
                    raise ValueError(
                        "synthetic case seed is not declared in manifest seeds: "
                        + ", ".join(str(x) for x in missing)
                    )
        elif self.manifest.seeds:
            raise ValueError("real-dataset benchmark manifest must not declare seeds")

    @property
    def case_count(self) -> int:
        return len(self.cases)

    @property
    def replay_keys(self) -> tuple[str, ...]:
        return tuple(x.replay_key for x in self.cases)
