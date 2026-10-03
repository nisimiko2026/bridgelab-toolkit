"""Generic execution layer for validated A8 benchmark batches.

A8.4 deliberately knows nothing about bidding semantics.  A caller supplies a
case executor; this runner preserves case identity/order and isolates ordinary
per-case execution failures so large batches can finish and be audited.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar

from .benchmark_batch import BenchmarkBatch
from .benchmark_case_identity import BenchmarkCaseIdentity

T = TypeVar("T")


class BenchmarkExecutionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class BenchmarkCaseExecution(Generic[T]):
    identity: BenchmarkCaseIdentity
    status: BenchmarkExecutionStatus
    result: T | None = None
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.identity, BenchmarkCaseIdentity):
            raise TypeError("identity must be BenchmarkCaseIdentity")
        if not isinstance(self.status, BenchmarkExecutionStatus):
            raise TypeError("status must be BenchmarkExecutionStatus")
        if self.status is BenchmarkExecutionStatus.COMPLETED:
            if self.error_type is not None or self.error_message is not None:
                raise ValueError("completed execution cannot contain error metadata")
        else:
            if self.result is not None:
                raise ValueError("failed execution cannot contain a result")
            if not isinstance(self.error_type, str) or not self.error_type.strip():
                raise ValueError("failed execution requires error_type")
            if not isinstance(self.error_message, str):
                raise TypeError("error_message must be a string")


@dataclass(frozen=True, slots=True)
class BenchmarkRun(Generic[T]):
    batch: BenchmarkBatch
    executions: tuple[BenchmarkCaseExecution[T], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.batch, BenchmarkBatch):
            raise TypeError("batch must be BenchmarkBatch")
        if not isinstance(self.executions, tuple):
            raise TypeError("executions must be a tuple")
        if not all(isinstance(x, BenchmarkCaseExecution) for x in self.executions):
            raise TypeError("executions must contain BenchmarkCaseExecution")
        if len(self.executions) != self.batch.case_count:
            raise ValueError("execution count must equal batch case count")
        if tuple(x.identity for x in self.executions) != self.batch.cases:
            raise ValueError("execution identities must match batch cases in order")

    @property
    def completed(self) -> int:
        return sum(x.status is BenchmarkExecutionStatus.COMPLETED for x in self.executions)

    @property
    def failed(self) -> int:
        return sum(x.status is BenchmarkExecutionStatus.FAILED for x in self.executions)


def run_benchmark_batch(
    batch: BenchmarkBatch,
    executor: Callable[[BenchmarkCaseIdentity], T],
) -> BenchmarkRun[T]:
    """Execute every validated case once, preserving order and failures."""
    if not isinstance(batch, BenchmarkBatch):
        raise TypeError("batch must be BenchmarkBatch")
    if not callable(executor):
        raise TypeError("executor must be callable")

    executions = []
    for identity in batch.cases:
        try:
            result = executor(identity)
        except Exception as exc:
            executions.append(
                BenchmarkCaseExecution(
                    identity=identity,
                    status=BenchmarkExecutionStatus.FAILED,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
        else:
            executions.append(
                BenchmarkCaseExecution(
                    identity=identity,
                    status=BenchmarkExecutionStatus.COMPLETED,
                    result=result,
                )
            )

    return BenchmarkRun(batch=batch, executions=tuple(executions))
