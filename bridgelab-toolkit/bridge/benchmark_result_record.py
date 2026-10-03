"""Normalized passive result record for one A8 benchmark case.

A8.5 converts successful execution payloads into a small aggregation-friendly
record while preserving the original payload and case identity.  It does not
rank evidence, infer missing metadata, or change policy.
"""
from __future__ import annotations
from dataclasses import dataclass

from .benchmark_case_identity import BenchmarkCaseIdentity
from .benchmark_runner import BenchmarkCaseExecution, BenchmarkExecutionStatus
from .capability_providers import ProviderStatus
from .decision_case import DecisionCase
from .decision_evidence import DisagreementKind


@dataclass(frozen=True, slots=True)
class BenchmarkProviderRecord:
    provider_id: str
    status: ProviderStatus
    has_recommendation: bool
    source_ids: tuple[str, ...] = ()
    model_id: str | None = None

    def __post_init__(self):
        if not isinstance(self.provider_id,str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        object.__setattr__(self,"provider_id",self.provider_id.strip())
        if not isinstance(self.status,ProviderStatus):
            raise TypeError("status must be ProviderStatus")
        if not isinstance(self.has_recommendation,bool):
            raise TypeError("has_recommendation must be bool")
        if not isinstance(self.source_ids,tuple) or not all(isinstance(x,str) and x.strip() for x in self.source_ids):
            raise TypeError("source_ids must be a tuple of non-blank strings")
        if self.model_id is not None and (not isinstance(self.model_id,str) or not self.model_id.strip()):
            raise ValueError("model_id must be a non-blank string or None")


@dataclass(frozen=True, slots=True)
class BenchmarkResultRecord:
    identity: BenchmarkCaseIdentity
    execution_status: BenchmarkExecutionStatus
    bridgelab: BenchmarkProviderRecord | None = None
    external: tuple[BenchmarkProviderRecord,...] = ()
    disagreements: tuple[DisagreementKind,...] = ()
    payload: object | None = None
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self):
        if not isinstance(self.identity,BenchmarkCaseIdentity):
            raise TypeError("identity must be BenchmarkCaseIdentity")
        if not isinstance(self.execution_status,BenchmarkExecutionStatus):
            raise TypeError("execution_status must be BenchmarkExecutionStatus")
        if self.bridgelab is not None and not isinstance(self.bridgelab,BenchmarkProviderRecord):
            raise TypeError("bridgelab must be BenchmarkProviderRecord or None")
        if not isinstance(self.external,tuple) or not all(isinstance(x,BenchmarkProviderRecord) for x in self.external):
            raise TypeError("external must contain BenchmarkProviderRecord")
        if not isinstance(self.disagreements,tuple) or not all(isinstance(x,DisagreementKind) for x in self.disagreements):
            raise TypeError("disagreements must contain DisagreementKind")
        if self.execution_status is BenchmarkExecutionStatus.FAILED:
            if self.payload is not None or self.bridgelab is not None or self.external or self.disagreements:
                raise ValueError("failed result record cannot contain benchmark evidence")
            if not isinstance(self.error_type,str) or not self.error_type.strip():
                raise ValueError("failed result record requires error_type")
            if not isinstance(self.error_message,str):
                raise TypeError("failed result record requires error_message")
        elif self.error_type is not None or self.error_message is not None:
            raise ValueError("completed result record cannot contain error metadata")

    @property
    def bridgelab_abstained(self) -> bool:
        return self.bridgelab is not None and self.bridgelab.status is ProviderStatus.ABSTAIN


def _provider(evidence) -> BenchmarkProviderRecord:
    result=evidence.result
    return BenchmarkProviderRecord(
        provider_id=result.provider.provider_id,
        status=result.status,
        has_recommendation=evidence.recommendation is not None,
        source_ids=result.evidence.source_ids,
        model_id=result.evidence.model_id,
    )


def benchmark_result_record(execution: BenchmarkCaseExecution) -> BenchmarkResultRecord:
    """Normalize one runner execution without reinterpreting its evidence."""
    if not isinstance(execution,BenchmarkCaseExecution):
        raise TypeError("execution must be BenchmarkCaseExecution")

    if execution.status is BenchmarkExecutionStatus.FAILED:
        return BenchmarkResultRecord(
            identity=execution.identity,
            execution_status=execution.status,
            error_type=execution.error_type,
            error_message=execution.error_message,
        )

    payload=execution.result
    if isinstance(payload,DecisionCase):
        return BenchmarkResultRecord(
            identity=execution.identity,
            execution_status=execution.status,
            bridgelab=None if payload.bridgelab is None else _provider(payload.bridgelab),
            external=tuple(_provider(x) for x in payload.external),
            disagreements=tuple(x.kind for x in payload.disagreements),
            payload=payload,
        )

    return BenchmarkResultRecord(
        identity=execution.identity,
        execution_status=execution.status,
        payload=payload,
    )
